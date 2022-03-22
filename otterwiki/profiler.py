#!/env/bin/python
"""
This script can be used to profile flask using the werkzeug middleware
for cProfile.

FLASK_DEBUG=True FLASK_APP=otterwiki.server OTTERWIKI_SETTINGS=../settings.cfg \
        env/bin/python otterwiki/profiler.py
"""

from werkzeug.middleware.profiler import ProfilerMiddleware
from otterwiki.server import app

app.config['PROFILE'] = True
app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])
app.run(debug = True)
