#!/env/bin/python
# vim: set et ts=8 sts=4 sw=4 ai:
"""
This script can be used to profile flask using the werkzeug middleware
for cProfile.

FLASK_DEBUG=True FLASK_APP=otterwiki.server OTTERWIKI_SETTINGS=../settings.cfg \
        venv/bin/python otterwiki/profiler.py

Handle with curl to not get overwhelmed.
"""

from werkzeug.middleware.profiler import ProfilerMiddleware
import cProfile
from otterwiki.server import app

app.config['PROFILE'] = True
app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])

with cProfile.Profile() as pr:
    app.run(debug=True, port=8080)
