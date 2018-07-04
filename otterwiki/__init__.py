from __future__ import print_function
import sys
import os
from flask import Flask
from flask_login import LoginManager, current_user
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('otterwiki.default_settings')
app.config.from_envvar('OTTERWIKI_SETTINGS', silent=True)

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = '.login'

# setup flask_mail
mail = Mail(app)

def fatal_error(msg):
    print("Error:", msg, file=sys.stderr)
    sys.exit(1)

if app.config['REPOSITORY'] is not None and not os.path.exists(app.config['REPOSITORY']):
    fatal_error("Repository path '{}' not found. Please configure otterwiki.".format(app.config['REPOSITORY']))

if not app.debug:
    import logging
    from logging.handlers import TimedRotatingFileHandler
    # https://docs.python.org/3.6/library/logging.handlers.html#timedrotatingfilehandler
    file_handler = TimedRotatingFileHandler(os.path.join(app.config['LOG_DIR'], 'otterwiki.log'), 'midnight')
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(logging.Formatter('<%(asctime)s> <%(levelname)s> %(message)s'))
    app.logger.addHandler(file_handler)

def has_read_access():
    if app.config['READ_ACCESS'] == 'ANONYMOUS':
        return True
    if app.config['READ_ACCESS'] == 'REGISTERED' and current_user.is_authenticated:
        return True
    if app.config['READ_ACCESS'] == 'APPROVED' and current_user.is_authenticated \
            and current_user.is_approved:
        return True
    return False

def has_write_access():
    if not has_read_access():
        return False
    if app.config['WRITE_ACCESS'] == 'ANONYMOUS':
        return True
    if app.config['WRITE_ACCESS'] == 'REGISTERED' and current_user.is_authenticated:
        return True
    if app.config['WRITE_ACCESS'] == 'APPROVED' and current_user.is_authenticated \
            and current_user.is_approved:
        return True
    return False

def has_attachment_access():
    if not has_read_access():
        return False
    if app.config['ATTACHMENT_ACCESS'] == 'ANONYMOUS':
        return True
    if app.config['ATTACHMENT_ACCESS'] == 'REGISTERED' and current_user.is_authenticated:
        return True
    if app.config['ATTACHMENT_ACCESS'] == 'APPROVED' and current_user.is_authenticated \
            and current_user.is_approved:
        return True
    return False

def has_admin_access():
    if not has_read_access():
        return False
    return current_user.is_admin

app.jinja_env.globals.update(has_write_access=has_write_access)
app.jinja_env.globals.update(has_attachment_access=has_attachment_access)
app.jinja_env.globals.update(has_admin_access=has_admin_access)

@app.template_filter('debug_append_unixtime')
def debug_append_unixtime(s):
    if app.debug:
        from datetime import datetime
        return "{}?q={}".format(s, datetime.now().strftime('%s'))
    else:
        return s

@app.template_filter('format_datetime')
def format_datetime(value, format='medium'):
    if format == 'medium':
        format="%Y-%m-%d %H:%M"
    else: # format == 'full':
        format="%Y-%m-%d %H:%M:%S"
    return value.strftime(format)

@app.template_global(name='ziphelper')
def _ziphelper(*args, **kwargs): #to not overwrite builtin zip in globals
    from pprint import pprint
    l0 = list(args[0])
    l1 = list(args[1])
    return zip(l0, l1)

import otterwiki.storage
if app.config['REPOSITORY'] is not None:
    try:
        otterwiki.storage.storage = otterwiki.storage.GitStorage(app.config['REPOSITORY'])
    except otterwiki.storage.StorageError as e:
        fatal_error(e)

import otterwiki.formatter as formatter
import otterwiki.views

try:
    db.create_all()
except Exception as e:
    fatal_error(e)
