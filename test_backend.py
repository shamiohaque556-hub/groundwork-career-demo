"""Isolated integration checks; no demo database is used."""
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import build_opener, HTTPCookieProcessor, Request
from urllib.error import HTTPError
from http.cookiejar import CookieJar
import server

class BackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        server.DB=Path(cls.tmp.name)/'test.sqlite3'
        server.setup();server.setup_profiles()
        cls.http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        cls.url='http://127.0.0.1:'+str(cls.http.server_port)
        threading.Thread(target=cls.http.serve_forever,daemon=True).start()
    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown();cls.http.server_close();cls.tmp.cleanup()
    def test_profile_and_existing_journey(self):
        a=build_opener(HTTPCookieProcessor(CookieJar()))
        b=build_opener(HTTPCookieProcessor(CookieJar()))
        def get(client,path):
            with client.open(self.url+path) as r:return json.load(r)
        def post(client,path,data):
            req=Request(self.url+path,json.dumps(data).encode(),{'Content-Type':'application/json','Origin':self.url})
            with client.open(req) as r:return json.load(r)
        self.assertIsNone(get(a,'/api/profile'))
        profile={'name':'Demo explorer','age':19,'occupation':'College student','detail':'Interested in nature'}
        self.assertEqual(post(a,'/api/profile',profile),profile)
        self.assertEqual(get(a,'/api/profile'),profile)
        self.assertIsNone(get(b,'/api/profile'))
        for bad in [0,121,'nineteen',True]:
            with self.assertRaises(HTTPError) as cm:post(a,'/api/profile',{**profile,'age':bad})
            self.assertEqual(cm.exception.code,400)
        self.assertEqual(len(get(a,'/api/experiences')),3)
        post(a,'/api/interest',{'experience':'soil','answers':{'interest':'Plants and soil','purpose':'Learn something new','hope':'What is daily work like?'}})
        post(a,'/api/reflection',{'experience':'soil','reflection':{'enjoyed':'Planting','surprised':'Daily routines','next':'Try more in this field'}})
        self.assertEqual(len(get(a,'/api/me')),1)
        self.assertIsNotNone(get(a,'/api/me')[0]['reflection'])
        self.assertEqual(get(b,'/api/me'),[])
        post(a,'/api/reset',{})
        self.assertEqual(get(a,'/api/me'),[])
        self.assertEqual(get(a,'/api/profile'),profile)
        for path in ['/','/style.css','/script.js']:
            with a.open(self.url+path) as r:self.assertEqual(r.status,200);self.assertTrue(r.read())
        with self.assertRaises(HTTPError) as cm:a.open(self.url+'/server.py')
        self.assertEqual(cm.exception.code,404)

if __name__=='__main__':unittest.main()
