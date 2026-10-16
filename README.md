# Groundwork Core — Career Discovery Demo

Python 3.10 or newer. No packages to install.

## Windows
Extract the ZIP into its own folder. Double-click START-WINDOWS.bat.
Or open the extracted groundwork-core folder in VS Code and run:

    py -3 server.py --open

Open http://localhost:8010 and keep the terminal running. This demo uses 8010, so it does not share the competition platform's default port 8000.
If occupied: py -3 server.py --port 8011 --open

## Flow
Welcome → name, age and current activity → nine proposed groups → Nature's 14 fields → Agriculture → three sample experiences → interest questions → notebook → practice reflection.
Only Nature is available. Other groups are visibly marked Coming next. Nine groups follow the most recent proposed structure; labels can be revised.
The form can be edited from About you. Profiles, interests and reflections are stored in a local SQLite database and linked to a browser cookie. No login or cross-device account is included. The new package starts fresh and does not import progress from earlier demos. Deleting notebook progress deletes interests/reflections, not the introduction.
Experience dates, venues, hosts and bookings are not real. Branch content is a draft introduction, not an exhaustive career inventory.

## Files
server.py: Python backend and SQLite persistence.
web/index.html, style.css, script.js: frontend.
test_backend.py: isolated backend verification, using a temporary database.

## Hosting
This is a local pitch demo. Netlify static hosting will not run server.py or SQLite. Online hosting needs a suitable backend service and proper account/privacy controls before collecting real participant data. Do not upload groundwork.sqlite3 or personal demo records to GitHub.

## Verification
Run py -3 test_backend.py. Browser visual testing was not available during creation.
