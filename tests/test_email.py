#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import os
import pytest
import filelock
import contextlib


@pytest.fixture(scope="session")
def lock(tmp_path_factory):
    base_temp = tmp_path_factory.getbasetemp()
    lock_file = base_temp.parent / "serial.lock"
    yield filelock.FileLock(lock_file=str(lock_file))
    with contextlib.suppress(OSError):
        os.remove(path=lock_file)


@pytest.fixture()
def serial(lock):
    with lock.acquire(poll_interval=0.1):
        yield


from smtplib import SMTP


def test_sendmail(serial, smtpd):
    from_addr = "from.addr@example.org"
    to_addrs = "to.addr@example.org"
    msg = (
        f"From: {from_addr}\r\n"
        f"To: {to_addrs}\r\n"
        f"Subject: Foo\r\n\r\n"
        f"Foo bar"
    )

    with SMTP(smtpd.hostname, smtpd.port) as client:
        client.sendmail(from_addr, to_addrs, msg)

    assert len(smtpd.messages) == 1


##
## Dear Future-Ralph: No idea why MAIL_SERVER doesn't end up in app.config
##
#
# @pytest.fixture
# def create_app_smtp(tmpdir, smtpd, serial):
#    tmpdir.mkdir("repo")
#    storage = otterwiki.gitstorage.GitStorage(path=str(tmpdir.join("repo")),
#              initialize=True)
#    settings_cfg = str(tmpdir.join("settings.cfg"))
#    # write config file
#    with open(settings_cfg,'w') as f:
#        f.writelines([
#            "REPOSITORY = '{}'\n".format(str(tmpdir.join("repo"))),
#            "SITE_NAME = 'TEST WIKI'\n",
#            "MAIL_SERVER = '{}'\n".format(smtpd.hostname),
#            "MAIL_PORT = '{}'\n".format(smtpd.port),
#            ])
#    # configure environment
#    os.environ['OTTERWIKI_SETTINGS'] = settings_cfg
#    # get app
#    from otterwiki.server import app, mail
#    # enable test and debug settings
#    app.config['TESTING'] = True
#    app.config['DEBUG'] = True
#    mail.init_app(app)
#    # for debugging
#    app.storage = storage.path
#    yield app
#
# def test_sendmail(create_app_smtp, smtpd):
#    # configure app
#    from otterwiki.helper import send_mail
#
#    #def send_mail(subject, recipients, text_body, sender=None, html_body=None, _async=True):
#    send_mail("subject",["mail1@example.com"],"body","mail2@example.com", _async=False)
#    import time
#    time.sleep(1)
#    assert len(smtpd.messages) == 1
