"""Groundwork Core local pitch demo. Python 3.10+, standard library only."""
import argparse
import hashlib
import json
import secrets
import sqlite3
import threading
import webbrowser
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'groundwork.sqlite3'
EXPERIENCES = [
 {'id':'soil', 'title':'A day close to the soil', 'category':'Crops & growing', 'number':'01', 'duration':'Half-day concept', 'summary':'Follow the journey from seed to harvest. Meet the choices behind the food on your plate.', 'intro':'A proposed small-group visit to a working crop farm. Observe the work, ask questions, and try an activity chosen by the host.', 'activities':['Walk the growing area and discuss seasonal decisions.','Try a supervised planting or soil observation activity.','Hear about labour, weather, costs and uncertainty.'], 'questions':['What changes when the weather does not cooperate?','Which tasks take the most time?','What would a beginner need to learn first?'], 'directions':['Crop production','Soil and crop testing','Farmer advisory work'], 'next':'Compare crop production with soil testing. Write down which daily tasks you would like to understand better.'},
 {'id':'dairy', 'title':'Meet the work behind the milk', 'category':'Animals & dairy', 'number':'02', 'duration':'Half-day concept', 'summary':'Look beyond the product. Explore animal care, routines and the responsibility of daily work.', 'intro':'A proposed visit to a dairy operation, led by a suitable host. Animal contact and demonstrations depend on host permission and hygiene requirements.', 'activities':['Observe feeding, housing and daily care routines.','Discuss milk handling and record keeping.','Ask about early starts, ongoing costs and animal wellbeing.'], 'questions':['What does a typical working day involve?','What happens when an animal needs care?','Which roles require specialist training?'], 'directions':['Dairy operations','Animal husbandry','Quality and supply operations'], 'next':'Compare animal care with dairy operations. Find out the training required for a specific role before choosing a pathway.'},
 {'id':'tools', 'title':'Where farming meets invention', 'category':'Tools & technology', 'number':'03', 'duration':'Workshop concept', 'summary':'Explore the tools people build for farmers—and the practical problems they need to solve.', 'intro':'A proposed workshop with a farming technology practitioner. Explore a simple problem through demonstrations and discussion; no machinery operation is assumed.', 'activities':['Explore an irrigation or sensing demonstration.','Sketch a solution to a real farming problem.','Discuss repairs, affordability and adoption with a practitioner.'], 'questions':['Who uses this tool, and what problem does it solve?','How is it maintained when it breaks?','What makes a useful idea practical on a farm?'], 'directions':['Agricultural engineering','Digital farming','Technical support'], 'next':'Choose one farm problem and sketch a simple solution. Explore the engineering and farming knowledge it would require.'}
]

def connect():
    con = sqlite3.connect(DB, timeout=10)
    con.execute('PRAGMA foreign_keys=ON')
    return con

def setup():
    with connect() as c:
        c.executescript('CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY); CREATE TABLE IF NOT EXISTS interests (session TEXT, experience TEXT, answers TEXT NOT NULL, reflection TEXT, PRIMARY KEY(session,experience), FOREIGN KEY(session) REFERENCES sessions(id));')

def setup_profiles():
    with connect() as c:
        c.execute('CREATE TABLE IF NOT EXISTS profiles (session TEXT PRIMARY KEY REFERENCES sessions(id), data TEXT NOT NULL)')

ACTIVITIES=['Being a farmer or grower','Being a technician','Working in sales & marketing','Working with technology','Building a business','Researching & experimenting','Managing operations & supply','Teaching & supporting farmers','Something else','I do not know yet']
PURPOSES=['Explore a job or career','Explore a business idea','Decide what to study','Improve my current work','Understand the field','I am not sure yet']
EXPOSURE=['Completely new','Read or watched things','Studied a related subject','Visited a farm or workplace','Helped family or worked in it','Currently working in it']
EXPECTATIONS=['See a normal working day','Talk to someone doing the work','Visit a farm or workplace','Try a guided activity','Understand skills and learning paths','Compare different kinds of work','Suggest a starting point']

def setup_questions():
    with connect() as c:
        c.execute('CREATE TABLE IF NOT EXISTS agriculture_answers (session TEXT PRIMARY KEY REFERENCES sessions(id), answers TEXT NOT NULL, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)')

class Handler(BaseHTTPRequestHandler):
    server_version = 'GroundworkDemo/1'
    def log_message(self, fmt, *args):
        pass
    def reply(self, status, value, content_type='application/json; charset=utf-8'):
        raw = json.dumps(value).encode() if content_type.startswith('application/json') else value
        self.send_response(status)
        self.send_header('Content-Type',content_type)
        self.send_header('Content-Length',str(len(raw)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','same-origin')
        self.send_header('Content-Security-Policy', "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        if getattr(self,'new_cookie',None):
            self.send_header('Set-Cookie',f'gc_session={self.new_cookie}; HttpOnly; SameSite=Strict; Path=/; Max-Age=2592000')
        self.end_headers()
        try:
            self.wfile.write(raw)
        except (BrokenPipeError,ConnectionResetError):
            pass
    def session(self):
        cookie = SimpleCookie()
        try: cookie.load(self.headers.get('Cookie',''))
        except Exception: pass
        token = cookie['gc_session'].value if 'gc_session' in cookie else ''
        digest = hashlib.sha256(token.encode()).hexdigest()
        with connect() as c:
            if token and c.execute('SELECT 1 FROM sessions WHERE id=?',(digest,)).fetchone(): return digest
            token = secrets.token_urlsafe(32)
            digest = hashlib.sha256(token.encode()).hexdigest()
            c.execute('INSERT INTO sessions VALUES (?)',(digest,))
        self.new_cookie = token
        return digest
    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/api/agriculture':
            sid=self.session()
            with connect() as c: row=c.execute('SELECT answers FROM agriculture_answers WHERE session=?',(sid,)).fetchone()
            return self.reply(200,json.loads(row[0]) if row else None)
        if path == '/api/profile':
            sid=self.session()
            with connect() as c: row=c.execute('SELECT data FROM profiles WHERE session=?',(sid,)).fetchone()
            return self.reply(200,json.loads(row[0]) if row else None)
        if path == '/api/experiences': return self.reply(200,EXPERIENCES)
        if path == '/api/me':
            sid=self.session()
            with connect() as c: rows=c.execute('SELECT experience,answers,reflection FROM interests WHERE session=?',(sid,)).fetchall()
            return self.reply(200,[{'experience':r[0],'answers':json.loads(r[1]),'reflection':json.loads(r[2]) if r[2] else None} for r in rows])
        files={'/':'index.html','/index.html':'index.html','/style.css':'style.css','/script.js':'script.js'}
        if path not in files: return self.reply(404,{'error':'Page not found.'})
        name=files[path]
        types={'html':'text/html; charset=utf-8','css':'text/css; charset=utf-8','js':'application/javascript; charset=utf-8'}
        return self.reply(200,(ROOT/'web'/name).read_bytes(),types[name.split('.')[-1]])
    def do_POST(self):
        # Local-only demo: reject cross-origin writes and unexpected hosts.
        allowed={f'localhost:{self.server.server_port}',f'127.0.0.1:{self.server.server_port}'}
        host=self.headers.get('Host','')
        origin=self.headers.get('Origin')
        if host not in allowed or (origin and origin not in {f'http://{h}' for h in allowed}):
            return self.reply(403,{'error':'This request is not allowed.'})
        if not self.headers.get('Content-Type','').startswith('application/json'): return self.reply(415,{'error':'JSON required.'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0 < length <= 16000: return self.reply(413,{'error':'Request is too large or empty.'})
            data=json.loads(self.rfile.read(length))
            if not isinstance(data,dict): raise ValueError()
        except (ValueError,UnicodeDecodeError): return self.reply(400,{'error':'Invalid request.'})
        sid=self.session()
        path=urlsplit(self.path).path
        if path=='/api/agriculture':
            with connect() as c: has_profile=c.execute('SELECT 1 FROM profiles WHERE session=?',(sid,)).fetchone()
            if not has_profile: return self.reply(409,{'error':'Please save your introduction first.'})
            clean={}
            for key,allowed in [('activities',ACTIVITIES),('purpose',PURPOSES),('experience',EXPOSURE),('expectations',EXPECTATIONS)]:
                value=data.get(key)
                if not isinstance(value,list) or not value or len(value)>len(allowed) or any(not isinstance(v,str) or v not in allowed for v in value):
                    return self.reply(400,{'error':'Please choose a valid answer for every question.'})
                if len(value)!=len(set(value)): return self.reply(400,{'error':'Duplicate selections are not allowed.'})
                exclusive={'I do not know yet','I am not sure yet','Completely new','Suggest a starting point'}
                if len(value)>1 and any(v in exclusive for v in value): return self.reply(400,{'error':'Choose uncertainty on its own, or select specific options.'})
                clean[key]=value
                note=data.get(key+'_note','')
                if not isinstance(note,str) or len(note)>1200: return self.reply(400,{'error':'Keep each note under 1,200 characters.'})
                clean[key+'_note']=note.strip()
            if 'Something else' in clean['activities'] and not clean['activities_note']:
                return self.reply(400,{'error':'Please describe the other activity you have in mind.'})
            with connect() as c:
                c.execute('INSERT INTO agriculture_answers(session,answers) VALUES (?,?) ON CONFLICT(session) DO UPDATE SET answers=excluded.answers,updated_at=CURRENT_TIMESTAMP',(sid,json.dumps(clean)))
            return self.reply(200,clean)
        if path=='/api/profile':
            name=data.get('name','')
            age=data.get('age')
            occupation=data.get('occupation','')
            detail=data.get('detail','')
            if not isinstance(name,str) or not 1 <= len(name.strip()) <= 80:
                return self.reply(400,{'error':'Enter a name of up to 80 characters.'})
            if type(age) is not int or not 1 <= age <= 120:
                return self.reply(400,{'error':'Enter a valid age from 1 to 120.'})
            if occupation not in ['School student','College student','Working','Running a business','Looking for work','Taking a break','Something else']:
                return self.reply(400,{'error':'Choose what you are doing now.'})
            if not isinstance(detail,str) or len(detail)>300:
                return self.reply(400,{'error':'Keep your optional note under 300 characters.'})
            clean={'name':name.strip(),'age':age,'occupation':occupation,'detail':detail.strip()}
            with connect() as c:
                c.execute('INSERT INTO profiles VALUES (?,?) ON CONFLICT(session) DO UPDATE SET data=excluded.data',(sid,json.dumps(clean)))
            return self.reply(200,clean)
        if path=='/api/reset':
            with connect() as c:
                c.execute('DELETE FROM interests WHERE session=?',(sid,))
                c.execute('DELETE FROM agriculture_answers WHERE session=?',(sid,))
            return self.reply(200,{'ok':True})
        exp=data.get('experience')
        if exp not in {e['id'] for e in EXPERIENCES}: return self.reply(400,{'error':'Choose an experience.'})
        if path=='/api/interest':
            answers=data.get('answers',{})
            if not isinstance(answers,dict): return self.reply(400,{'error':'Invalid answers.'})
            clean={k:answers.get(k,'') for k in ['interest','purpose','hope']}
            if any(not isinstance(v,str) or not v.strip() or len(v)>1200 for v in clean.values()): return self.reply(400,{'error':'Please complete all three answers (maximum 1,200 characters each).'})
            with connect() as c: c.execute('INSERT INTO interests(session,experience,answers) VALUES (?,?,?) ON CONFLICT(session,experience) DO UPDATE SET answers=excluded.answers',(sid,exp,json.dumps(clean)))
        elif path=='/api/reflection':
            reflection=data.get('reflection',{})
            if not isinstance(reflection,dict): return self.reply(400,{'error':'Invalid reflection.'})
            clean={k:reflection.get(k,'') for k in ['enjoyed','surprised','next']}
            if any(not isinstance(v,str) or not v.strip() or len(v)>1200 for v in clean.values()): return self.reply(400,{'error':'Please complete all three reflections.'})
            with connect() as c:
                result=c.execute('UPDATE interests SET reflection=? WHERE session=? AND experience=?',(json.dumps(clean),sid,exp))
                if result.rowcount!=1: return self.reply(409,{'error':'Save your interest first.'})
        else: return self.reply(404,{'error':'Unknown action.'})
        return self.reply(200,{'ok':True})

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=8010)
    parser.add_argument('--open',action='store_true')
    args=parser.parse_args()
    setup()
    setup_profiles()
    setup_questions()
    try: server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    except OSError as e:
        raise SystemExit(f'Could not start on port {args.port}: {e}. Try: py -3 server.py --port 8011 --open')
    address=f'http://localhost:{args.port}'
    print(f'Groundwork Core — Career Discovery Demo: {address}\nKeep this terminal open. Ctrl+C stops the demo.',flush=True)
    if args.open: threading.Timer(0.6,lambda:webbrowser.open(address)).start()
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
