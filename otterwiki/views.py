#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set et ts=8 sts=4 sw=4 ai fenc=utf-8:

import os
import random
import string
import re
from datetime import datetime, timedelta
from pprint import pprint

from flask import render_template, flash, redirect, url_for, request, \
                  send_file, abort, make_response, escape as html_escape, \
                  send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, \
                        logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from werkzeug.http import http_date

from PIL import Image, ImageOps
from io import BytesIO
import mimetypes
from unidiff import PatchSet

from otterwiki import app, db, login_manager, has_write_access, \
                      has_attachment_access, has_read_access, \
                      has_admin_access

from otterwiki.storage import storage, StorageNotFound, StorageError
from otterwiki.formatter import render_markdown as render_markdown
from otterwiki.util import send_email, sizeof_fmt, serialize, \
                           deserialize, SerializeError, get_filename, get_pagename

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    first_seen = db.Column(db.DateTime())
    last_seen = db.Column(db.DateTime())
    is_approved = db.Column(db.Boolean())
    is_admin = db.Column(db.Boolean())

    def __repr__(self):
        return "<User '{} <{}>'>".format(self.name, self.email)

def get_attachment_filename(pagename, filename=''):
    return os.path.join(get_filename(pagename)[:-3], filename)

def get_attachment_full_filename(pagename, filename=''):
    return os.path.join(storage.path, get_attachment_filename(pagename, filename))

def get_author():
    if current_user.is_authenticated:
        a = (current_user.name, current_user.email)
    else:
        a = ('{}'.format(request.remote_addr),'')
    return a

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/wiki/about')
def about():
    with open(os.path.join(app.root_path, 'about.md')) as f:
        content = f.read()
    htmlcontent, _ = render_markdown(content)
    return render_template(
            'wiki.html',
            title="About an Otter Wiki",
            htmlcontent=htmlcontent,
            )

@app.route('/wiki/log')
def log(filename=None):
    if not has_read_access():
        flash('You lack the permissions to access this wiki. Please login.')
        return redirect(url_for('.login'))
    # TODO: add paging
    log = storage.log()

    log_filtered = []
    for orig_entry in log:
        entry = dict(orig_entry)
        entry['files'] = {}

        for key in orig_entry['files']:
            entry['files'][key] = {}
            # handle attachments and pages
            arr = key.split('/')
            if key.endswith(".md"):
                entry['files'][key]['name'] = get_pagename(key)
                entry['files'][key]['url'] = url_for('.view', 
                        pagename=get_pagename(key), revision=entry['revision'])
            if len(arr) == 2:
                pagename, filename = get_pagename(arr[0]), arr[1]
                entry['files'][key]['url'] = url_for('.get_attachment', 
                        pagename=pagename, filename=filename, revision=entry['revision'])
                entry['files'][key]['name'] = key

        log_filtered.append(entry)

    return render_template(
            'log.html',
            title="Last Changes",
            log=log_filtered,
            )

@app.route('/wiki/index')
def pageindex():
    if not has_read_access():
        flash('You lack the permissions to access this wiki. Please login.')
        return redirect(url_for('.login'))
    ls = [get_pagename(x) for x in storage.list_files() if x.endswith(".md")]
    idx = {}
    for f in ls:
        if f[0] in idx:
            idx[f[0]].append(f)
        else:
            idx[f[0]] = [f]

    return render_template(
            'pageindex.html',
            title="Index of Pages",
            pageidx=idx,
            )

@app.route('/wiki/login', methods=['POST','GET'])
def login():
    if current_user.is_authenticated:
        flash('You are already authenticated.')
    email = request.cookies.get('email')
    if request.method == 'POST':
        email = request.form.get('email').strip()
        password = request.form.get('password')
        name = request.form.get('name').strip()
        loginorregister = request.form.get('loginorregister')
        if loginorregister == 'login':
            user = User.query.filter_by(email=email).first()
            if user is not None and check_password_hash(user.password_hash, password):
                # process login
                login_user(user, remember=True)
                flash('You logged in successfully.', 'success')
                if not user.is_approved:
                    flash('You are not approved yet.', 'warning')
                next_page = request.args.get('next')
                if not next_page or url_parse(next_page).netloc != '':
                    next_page = url_for('.index')
                user.last_seen = datetime.now()
                db.session.add(user)
                db.session.commit()
                return redirect(next_page)
            else:
                flash("Invalid username or password.","error")
        else:
            # register account
            # first check if the user exists
            user = User.query.filter_by(email=email).first()
            if user is not None:
                flash("This eMail address is already registered.", "error")
            elif email is None or len(email)<1:
                flash("Please enter your email address.", "error")
            elif name is None or len(name)<1:
                flash("Please enter your name.", "error")
            else:
                # generate random password
                password = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
                # hash password
                hashed_password=generate_password_hash(password, method='sha256')
                # take care of flags
                is_admin = False
                if len(User.query.all()) < 1:
                    is_admin = True
                is_approved = app.config['AUTO_APPROVAL'] is True

                # create user
                user = User(
                        name=name,
                        email=email,
                        password_hash=hashed_password,
                        first_seen=datetime.now(),
                        last_seen=datetime.now(),
                        is_admin=is_admin,
                        is_approved=is_approved,
                        )
                db.session.add(user)
                db.session.commit()

                # generate email
                text_body = """Hello {name},

thank you for registering your account at an otter wiki.

The password generated for you is: {password}

Please login here: {url}

Cheers!
"""
                send_email(
                        subject = "Account - {} - An Otter Wiki".format(app.config['SITE_NAME']),
                        recipients = [email],
                        text_body  = text_body.format(name=name,
                            password=password,
                            url=url_for('.login', _external=True)),
                        )
                flash("Your password was sent to {}. Please check your mailbox.".format(email))
                app.logger.warning('login(): new user registered: {}'.format(email))

    # login_user(user, remember=form.remember_me.data)
    # next_page = request.args.get('next')
    # if not next_page or url_parse(next_page).netloc != '':
    #     next_page = url_for('.index')
    # return redirect(next_page)

    return render_template(
            'login.html',
            title="Login",
            email=email,
            )

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You logged out successfully.')
    return redirect(url_for('.index'))

@app.route('/wiki/settings/user_management', methods=['POST'])
def user_management():
    if not has_admin_access():
        abort(403)
    is_admin = [int(x) for x in request.form.getlist('is_admin')]
    is_approved = [int(x) for x in request.form.getlist('is_approved')]
    if len(is_admin)<1:
        flash("You can not remove all admins.","warning")
    else:
        # get all users
        users = User.query.all()
        updated_users = []
        for u in users:
            should_be_admin = u.id in is_admin
            should_be_approved = u.id in is_approved
            if u.is_admin != should_be_admin:
                u.is_admin = should_be_admin
                app.logger.info('{} changed admin status to {}'.format(u.name, should_be_admin))
                updated_users.append(u.name)
                db.session.add(u)
            if u.is_approved != should_be_approved:
                u.is_approved = should_be_approved
                app.logger.info('{} changed approved status to {}'.format(u.name, should_be_approved))
                updated_users.append(u.name)
                db.session.add(u)
        db.session.commit()
        if len(updated_users):
            updated_users = list(set(updated_users))
            flash("Updated permissions of: {}.".format(", ".join(updated_users)))

    return redirect(url_for('.settings'))

@app.route('/wiki/settings/change_password', methods=['POST','GET'])
def change_password():
    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        if password is not None and len(password)>1:
            if password == confirm:
                # update password hash
                current_user.password_hash = generate_password_hash(password, method='sha256')
                db.session.add(current_user)
                db.session.commit()
                flash("Your password was updated successfully.", "success")
            else:
                flash("The passwords do not match.", "error")
    return redirect(url_for('.settings'))

@app.route('/wiki/settings', methods=['POST','GET'])
@login_required
def settings():
    if current_user.is_admin:
        # fetch all Users
        user_list = User.query.all()
    else:
        user_list = None
    return render_template(
            'settings.html',
            title="Settings",
            user_list=user_list,
            )

@app.route('/wiki/lost_password', methods=['POST','GET'])
def lost_password(token=None):
    email = request.form.get("email")
    token = request.args.get("token")
    if token is not None:
        try:
            email = deserialize(token, salt="lost-password-email", max_age=86400)
        except SerializeError:
            app.logger.warning('lost_password() Invalid token.')
            flash("Invalid token.", "error")
            return render_template('lost_password.html', title="Lost password")
        user = User.query.filter_by(email=email).first()
        login_user(user, remember=True)
        app.logger.warning('lost_password() recovery successful: {}'.format(email))
        flash("Welcome {}, please update your password.".format(user.name))
        return redirect( url_for(".settings") )

    if request.method == 'POST' and email is not None:
        email = email.strip()
        token = serialize(email, salt="lost-password-email")
        user = User.query.filter_by(email=email).first()
        if user is None:
            app.logger.warning('lost_password() unknown email: {}'.format(email))
            flash("Unknown email address '{}'.".format(email), "error")
            return render_template('lost_password.html', title="Lost password")
        # User found. Build and send the email.
        text_body = """Hello {name},

To recover your password, please use the following link:

{url}

Cheers!
"""
        app.logger.warning('lost_password() recovery started: {} ({})'.format(email, token))
        send_email(
                subject = "Lost Password  - {} - An Otter Wiki".format(app.config['SITE_NAME']),
                recipients = [email],
                text_body  = text_body.format(name=user.name,
                    url=url_for('.lost_password', token=token, _external=True)),
                )

    return render_template('lost_password.html', title="Lost password")

@app.route('/wiki/create', methods=['POST','GET'])
@app.route('/wiki/create/<string:pagename>', methods=['GET'])
def create(pagename=None):
    if not has_write_access():
        abort(403)
    if request.method == 'POST':
        pagename = request.form.get("pagename")
        pagename = pagename.strip()
        # check if page exists
        if storage.exists(get_filename(pagename)):
            flash("Page {} exists already.".format(pagename), "warning")
        else:
            return redirect(url_for('.edit', pagename=pagename))

    return render_template(
            'create.html',
            title="Create Page",
            pagename=pagename,
            )

@app.route('/wiki/syntax')
def syntax():
    return render_template(
            'syntax.html',
            title="Markdown Guide",
            )

@app.route('/<string:pagename>')
@app.route('/<string:pagename>/view/<string:revision>')
def view(pagename='Home', revision=None):
    if not has_read_access():
        if current_user.is_authenticated and not current_user.is_approved:
            flash('You lack the permissions to access this wiki. Please wait for approval.')
        else:
            flash('You lack the permissions to access this wiki. Please login.')
        return redirect(url_for('.login'))
    #app.logger.info('view {}'.format(name))
    filename = get_filename(pagename)
    try:
        content = storage.load(filename, revision=revision)
        metadata = storage.metadata(filename, revision=revision)
    except StorageNotFound:
        app.logger.warning('Not found {}'.format(pagename))
        return render_template('pagenotfound.html',
                title='404',
                subtitle='Page {} not found.'.format(pagename),
                pagename=pagename)
    # render page using the formatter
    page, toc = render_markdown(content)
    subtitle = None
    if revision is not None:
        subtitle = "Revision {}".format(revision)
    
    return render_template('view.html',
            title=pagename,
            subtitle=subtitle,
            pagename=pagename,
            metadata=metadata,
            revision=revision,
            page=page,
            toc=toc)

@app.route('/')
def index():
    return view()

@app.route('/<string:pagename>/edit/')
@app.route('/<string:pagename>/edit/<string:revision>')
def edit(pagename = 'Home', revision=None):
    if not has_write_access():
        abort(403)
    subtitle = None
    if revision is not None:
        subtitle = "Revision {}".format(revision)
    filename = get_filename(pagename)
    try:
        content = storage.load(filename, revision=revision)
    except StorageNotFound:
        content = ""
    return render_template('editor.html',
            title=pagename,
            subtitle=subtitle,
            pagename=pagename,
            revision=revision,
            content=content.strip())

@app.route('/<string:pagename>/save', methods=['POST'])
def save(pagename):
    if not has_write_access():
        abort(403)
    content = request.form.get('content').strip()
    content = content.replace("\r\n", "\n") + "\n"
    message = request.form.get('message')
    filename = get_filename(pagename)
    if message is None or message.strip() == "":
        message = "Updated {}".format(pagename)

    changed = storage.store(
            filename=filename,
            content=content,
            message = message,
            author = get_author()
        )
    if not changed:
        flash('Nothing to update.')

    return redirect(url_for('.view', pagename=pagename))


@app.route('/<string:pagename>/history', methods=['GET','POST'])
def history(pagename):
    if not has_read_access():
        flash('You lack the permissions to access this wiki. Please login.')
        return redirect(url_for('.login'))
    try:
        log = storage.log(get_filename(pagename))
    except StorageNotFound:
        return render_template('pagenotfound.html',
                title='404',
                subtitle='Page {} not found.'.format(pagename),
                name=pagename)
    # read radioboxes
    rev_a = request.form.get("rev_a")
    rev_b = request.form.get("rev_b")

    patchset = None
    if request.method == 'POST':
        return redirect(url_for('.diff', pagename=pagename, rev_a=rev_a, rev_b=rev_b))
    if rev_a is None:
        rev_a = log[0]['revision']
    if rev_b is None:
        try:
            rev_b = log[1]['revision']
        except:
            rev_b = rev_a

    return render_template('history.html',
            title=pagename,
            subtitle="History",
            pagename=pagename,
            log=log,
            rev_a=rev_a,
            rev_b=rev_b,
            patchset=patchset)

@app.route('/<string:pagename>/diff/<string:rev_a>/<string:rev_b>', methods=['GET'])
def diff(pagename, rev_a, rev_b):
    if not has_read_access():
        flash('You lack the permissions to access this wiki. Please login.')
        return redirect(url_for('.login'))
    try:
        log = storage.log(get_filename(pagename))
    except StorageNotFound:
        return render_template('pagenotfound.html',
                title='404',
                subtitle='Page {} not found.'.format(pagename),
                name=pagename)
    filename = get_filename(pagename)
    diff = storage.diff(filename, rev_b, rev_a)
    patchset = PatchSet(diff)
    hunk_helper = {}
    _line_type_style = {
                ' ':'',
                '+':'add',
                '-':'del',
            }
    for file in patchset:
        for hunk in file:
            lines = {}
            for l in hunk.source_lines():
                if not l.source_line_no in lines:
                    lines[l.source_line_no] = []
                lines[l.source_line_no].append({
                    'source':l.source_line_no,
                    'target':l.target_line_no or '',
                    'type':l.line_type,
                    'style':_line_type_style[l.line_type],
                    'value':l.value,
                    })
            for l in hunk.target_lines():
                if l.source_line_no is not None:
                    continue
                if not l.target_line_no in lines:
                    lines[l.target_line_no] = []
                lines[l.target_line_no].append({
                    'source':l.source_line_no or '',
                    'target':l.target_line_no,
                    'type':l.line_type,
                    'style':_line_type_style[l.line_type],
                    'value':l.value,
                    })
            hunk_helper[(file.source_file, file.target_file, hunk.source_start, hunk.source_length)] = lines

    return render_template('diff.html',
            title=pagename,
            subtitle="Diff {} {}".format(rev_a, rev_b),
            pagename=pagename,
            patchset=patchset,
            hunk_helper=hunk_helper)

@app.route('/<string:pagename>/a/<string:filename>')
@app.route('/<string:pagename>/a/<string:filename>/<string:revision>')
def get_attachment(pagename, filename, revision=None):
    # TODO: Solve the problem of using attachments as logo ...
    # if not has_read_access():
    #     flash('You lack the permissions to access this wiki. Please login.')
    #     return redirect(url_for('.login'))
    fn = get_attachment_filename(pagename, filename)
    ffn = get_attachment_full_filename(pagename, filename)
    if revision is None:
        if not storage.exists(fn):
            abort(404)
        # headers are alreday set correctly by send_file
        response = make_response(send_file(ffn))
        metadata = storage.metadata(fn)
    else:
        try:
            c = storage.load(fn, revision=revision, mode='rb')
            metadata = storage.metadata(fn, revision=revision)
        except StorageNotFound:
            abort(404)
        buffer = BytesIO()
        try:
            buffer.write(c)
        except:
            abort(500)
        buffer.seek(0)
        mimetype, encoding = mimetypes.guess_type(filename)
        response = make_response( send_file(buffer, mimetype=mimetype) )

    # set header, caching, etc
    modified = metadata['datetime']
    response.headers['Date'] = http_date(modified.utctimetuple())
    response.headers['Expires'] = http_date(modified.utctimetuple())
    response.headers['Last-Modified'] = http_date(modified.utctimetuple())

    return response

@app.route('/<string:pagename>/t/<string:filename>')
@app.route('/<string:pagename>/t/<string:filename>/<int:size>')
def get_attachment_thumbnail(pagename, filename, size=80):
    fn = get_attachment_filename(pagename, filename)
    ffn = get_attachment_full_filename(pagename, filename)
    if not storage.exists(fn):
        abort(404)
    # TODO fetch from cache
    data = None
    from timeit import default_timer as timer
    if data is None:
        t_start = timer()
        mimetype, encoding = mimetypes.guess_type(fn)
        if mimetype.startswith('image'):
            # read image
            image = Image.open(BytesIO(storage.load(fn, mode='rb')))
            # create thumbnail
            image.thumbnail((size,size), resample=Image.ANTIALIAS)
            options = {
                'format': image.format,
                'quality': 80,
            }
            data = BytesIO()
            image.save(data, **options)
            data.seek(0)
            app.logger.info("Thumbnail generation took {:.3f} seconds.".format(timer() - t_start))
    response = make_response(send_file(data, mimetype=mimetype))
    metadata = storage.metadata(fn)

    # set header, caching, etc
    modified = metadata['datetime']
    expires = modified + timedelta(hours=1)
    response.headers['Date'] = http_date(modified.utctimetuple())
    response.headers['Expires'] = http_date(modified.utctimetuple())
    response.headers['Last-Modified'] = http_date(modified.utctimetuple())

    return response

@app.route('/<string:pagename>/attachments/<string:filename>', methods=['GET','POST'] )
def edit_attachment(pagename, filename):
    # check if page exists
    if not storage.exists(get_filename(pagename)):
        return render_template('pagenotfound.html',
                title='404',
                subtitle='Page {} not found.'.format(pagename),
                name=pagename)
    if request.method == 'POST':
        # check access permissions
        if not has_attachment_access():
            abort(403)
        # the button defines the operation
        operation = request.form.get('operation')
        if operation == "rename":
            newfilename = request.form.get('newfilename')
            if filename != newfilename:
                try:
                    storage.rename(get_attachment_filename(pagename, filename),
                                   get_attachment_filename(pagename, newfilename), author=get_author())
                except StorageError:
                    flash("Renaming failed.", "error")
                else:
                    flash("{} renamed to {}.".format(filename, newfilename), "success")
                    return redirect( url_for( ".attachments", pagename=pagename ) )
        elif operation == "delete":
            fn = get_attachment_filename(pagename, filename)
            storage.delete(fn, message="{} removed.".format(fn), author=get_author() )
            flash("{} deleted.".format(filename), "success")
            return redirect( url_for( ".attachments", pagename=pagename ) )

    # find attachment, list all attachments
    files = storage.list_files(get_filename(pagename)[:-3])
    # check if attachment exists
    if filename not in files:
        return render_template('page.html',
                title='404',
                subtitle='Attachment not found.'.format(filename),
                pagename=pagename,
                content="Error: Attachment <tt>{}</tt> not found.".format(filename))
    try:
        log = storage.log(get_attachment_filename(pagename, filename))
    except StorageNotFound:
        log = None

    return render_template('edit_attachment.html',
            title=pagename,
            subtitle="Attachment: {}".format(filename),
            pagename=pagename,
            filename=filename,
            log=log,
            )

@app.route('/<string:pagename>/attachments', methods=['POST','GET'] )
def attachments(pagename):
    if not storage.exists(get_filename(pagename)):
        return render_template('pagenotfound.html',
                title='404',
                subtitle='Page {} not found.'.format(pagename),
                name=pagename)
    if request.method == 'POST':
        if not has_attachment_access():
            abort(403)
        # debug help via curl -F "file=@./354.jpg" http://localhost:5000/Home/attachments
        to_commit = []
        filename = request.form.get('filename')
        for file in request.files.getlist("file"):
            if file.filename == '':
                # no file selected
                continue
            # if filename is not None (update a attachment), replace only that
            if filename:
                fn = secure_filename(filename)
            else:
                fn = secure_filename(file.filename)
            ffn = get_attachment_full_filename(pagename, fn)
            to_commit.append( get_attachment_filename(pagename, fn) )
            # full directory name
            fdn = os.path.dirname(ffn)
            # make sure the directory exists
            os.makedirs(fdn, mode=0o777, exist_ok=True)
            # store attachment
            file.save(ffn)
            #print(ffn)
            if filename is not None:
                break
        if len(to_commit)>0:
            # take care of the commit message
            message = request.form.get('message')
            # default message
            if filename is None:
                default_message = "Added attachment(s): {}.".format(", ".join(to_commit))
            else:
                default_message = "Updated attachment: {}.".format(", ".join(to_commit))

            if message is None or message == "":
                message = default_message
            # commit
            storage.commit(to_commit, message=message, author=get_author())
            # notify the user
            flash(default_message)

    # find files
    files = storage.list_files(get_filename(pagename)[:-3])
    attachments = []
    for f in files:
        # prepare meta data dictionary
        d = {'filename':f, 'full':get_attachment_full_filename(pagename, f) }
        fn = get_attachment_filename(pagename, f)
        # store url
        d['url'] = url_for(".get_attachment", pagename=pagename, filename=f)
        try:
            d['meta'] = storage.metadata(get_attachment_filename(pagename, f))
        except StorageNotFound:
            # TODO log error?
            continue
        d['size'] = sizeof_fmt(os.stat(d['full']).st_size)
        d['mtime'] = datetime.fromtimestamp(os.path.getmtime(d['full']))
        mimetype, encoding = mimetypes.guess_type(fn)
        if mimetype is not None and mimetype.startswith('image'):
            d['thumbnail'] = url_for(".get_attachment_thumbnail", pagename=pagename, filename=f)
        attachments.append(d)

    return render_template('attachments.html',
            title=pagename,
            subtitle="Attachments",
            pagename=pagename,
            attachments=attachments,
            )

@app.route('/<string:pagename>/rename', methods=['POST','GET'] )
def rename(pagename):
    if not has_write_access():
        abort(403)
    fn = get_filename(pagename)
    # check if the page exists first
    if not storage.exists(fn):
        flash("Page '{}' not found.".format(pagename), "error")
        return redirect( url_for( ".index" ) )
    newname = request.form.get("newname")
    if request.method == 'POST':
        if newname is not None:
            newname = newname.strip()
            if len(newname)<1:
                flash("The name is too short.", "error")
            elif newname == pagename:
                flash("Nothing to update.", "error")
            else:
                try:
                    dirname = get_filename(pagename)[:-3]
                    files = storage.list_files(dirname)
                    # take care of the attachments
                    if len(files)>0:
                        newdirname = get_filename(newname)[:-3]
                        storage.rename(dirname, newdirname, author=get_author(),
                            no_commit=True)
                    # rename the file
                    storage.rename(get_filename(pagename),
                                   get_filename(newname), author=get_author())
                except StorageError as e:
                    flash("Renaming failed.", "error")
                else:
                    flash("{} renamed to {}.".format(pagename, newname), "success")
                    return redirect( url_for( ".view", pagename=newname ) )

    return render_template('rename.html',
            title="Rename {}".format(pagename),
            pagename=pagename,
            newname=newname,
            )

@app.route('/<string:pagename>/delete', methods=['POST','GET'])
def delete(pagename):
    if not has_write_access():
        abort(403)
    fn = get_filename(pagename)
    # check if the page exists first
    if not storage.exists(fn):
        flash("Page '{}' not found.".format(pagename), "error")
        return redirect( url_for( ".index" ) )
    if request.method == 'POST':
        message = request.form.get('message')
        storage.delete(fn, message=message, author=get_author() )
        flash("{} deleted.".format(pagename), "success")
        return redirect( url_for( ".index" ) )

    return render_template('delete.html',
            title="Delete {}".format(pagename),
            pagename=pagename,
            )

@app.route('/wiki/revert/<string:revision>', methods=['POST','GET'])
def revert(revision=None):
    if not has_write_access():
        abort(403)
    pagename = request.args.get('pagename')
    if request.method == 'POST':
        message = request.form.get('message')
        if message is None:
            message = "Reverted commit {}.".format(revision)
        try:
            storage.revert(revision, message=message, author=get_author() )
        except StorageError as e:
            flash("Error: Unable to revert {}.".format(revision),"error")
        return redirect( url_for( ".log" ) )

    return render_template('revert.html',
            title="Revert {}".format(revision),
            revision=revision,
            pagename=pagename,
            )

@app.route('/search', methods=['POST','GET'])
def search():
    if not has_read_access():
        flash('You lack the permissions to access this wiki. Please login.')
        return redirect(url_for('.login'))
    needle = request.form.get('needle')
    re_on = request.form.get('re')
    # match case is on
    mc_on = request.form.get('mc')
    result = {}
    if needle is not None and len(needle)>0:
        try:
            if re_on:
                sre = re.compile(needle)
                sre_i = re.compile(needle, re.IGNORECASE)
            else:
                sre = re.compile(re.escape(needle))
                sre_i = re.compile(re.escape(needle), re.IGNORECASE)
        except Exception as e:
            sre = None
            flash("Error in search term: {}".format(e.msg),"error")
        else:
            # find all markdown files
            md_files = [filename for filename in storage.list_files() if filename.endswith(".md")]
            for fn in md_files:
                r = []
                # open file, read file
                haystack = storage.load(fn)
                m = sre.search(get_pagename(fn))
                if mc_on is None and m is None:
                    m  = sre_i.search(get_pagename(fn))
                if m is not None:
                    # page name matches
                    r.append([None,get_pagename(fn),m.group(0)])
                for linernumber, line in enumerate(haystack.splitlines()):
                    line = line.strip()
                    m = sre.search(line)
                    if not m and mc_on is None:
                        # retry with ignore case
                        m = sre_i.search(line)
                    if m:
                        r.append(["{:04d}".format(linernumber+1),line,m.group(0)])
                if len(r)>0:
                    result[get_pagename(fn)] = []
                    for match in r:
                        hl = re.sub("({})".format(re.escape(html_escape(match[2]))),
                                   r"::o::w::1::\1::o::w::2::", html_escape(match[1]))
                        # shorten result line
                        if len(match[1])>70:
                            #splitter = "(::o::w::1::"+re.escape(match[2])+"::o::w::2::)"
                            splitter = "(::o::w::1::"+match[2]+"::o::w::2::)"
                            blocks = re.split(splitter, hl, flags=re.IGNORECASE)
                            for num,block in enumerate(blocks):
                                if len(block)<10 or re.match(splitter, block, flags=re.IGNORECASE):
                                    continue
                                words = re.split(r"(\S+)",block)
                                placeholder = False
                                while len(words)>12:
                                    placeholder = True
                                    del(words[int(len(words)/2)])
                                if placeholder:
                                    words.insert(int(len(words)/2)," [...] ")
                                blocks[num] = "".join(words)
                            hl = "".join(blocks)
                        # replace marker with html spans
                        hl = hl.replace("::o::w::1::", "<span class=\"match\">")
                        hl = hl.replace("::o::w::2::", "</span>")
                        result[get_pagename(fn)].append( match + [hl] )
            # "reorder" results
            newresult = [{},{}]
            # first all pagename matches
            for pagename in sorted(result.keys()):
                if result[pagename][0][0] is None:
                    newresult[0][pagename] = result[pagename]
                else:
                    newresult[1][pagename] = result[pagename]
            result = newresult

    return render_template('search.html',
            title="Search",
            needle = needle,
            re_on = re_on,
            mc_on = mc_on,
            result = result,
            )

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/img'),
                               'otter-favicon2.ico', mimetype='image/vnd.microsoft.icon')
