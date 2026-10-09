#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

"""
Tests for setting configuration from environment
and getting correct type in app.config[XX]
1. Booleans
2. Strings
3. Ints
"""

import pytest
import os
import otterwiki.gitstorage


@pytest.fixture
def create_app_with_env_setting(tmpdir):
    """Create app with changes to environment variables before initialization."""
    import sys

    # the yielded func updates this
    origenvval = {}

    # snapshot the currently imported otterwiki modules so we can restore the
    # exact same module objects on teardown. Re-importing otterwiki.server
    # below rebuilds the whole module graph (a fresh plugin_manager, renderer,
    # storage, ...); without restoring, other test modules that hold a
    # module-level reference (e.g. `from otterwiki.renderer import render`)
    # would be left pointing at a stale, orphaned graph.
    saved_otterwiki_modules = {
        k: v for k, v in sys.modules.items() if k.startswith('otterwiki')
    }

    def _create_app(envdict):
        for k in envdict:
            origenvval[k] = os.environ.get(k)
        origenvval["OTTERWIKI_SETTINGS"] = os.environ.get("OTTERWIKI_SETTINGS")

        tmpdir.mkdir("repo")
        _storage = otterwiki.gitstorage.GitStorage(
            path=str(tmpdir.join("repo")), initialize=True
        )
        settings_cfg = str(tmpdir.join("settings.cfg"))

        with open(settings_cfg, "w") as f:
            f.writelines(
                [
                    "REPOSITORY = '{}'\n".format(str(_storage.path)),
                    "SITE_NAME = 'TEST WIKI'\n",
                    "DEBUG = True\n",
                    "TESTING = True\n",
                    "MAIL_SUPPRESS_SEND = True\n",
                    "SECRET_KEY = 'Testing Testing Testing'\n",
                ]
            )

        for k in envdict:
            os.environ[k] = envdict[k]

        os.environ["OTTERWIKI_SETTINGS"] = settings_cfg

        # remove cached modules to force fresh import
        modules_to_remove = [
            k for k in sys.modules.keys() if k.startswith('otterwiki')
        ]
        for mod in modules_to_remove:
            del sys.modules[mod]

        from otterwiki.server import app, storage

        app._otterwiki_tempdir = storage.path
        app.storage = storage
        app.config["TESTING"] = True
        app.config["DEBUG"] = True

        return app

    yield _create_app

    # cleanup: restore original environment variables and reimport modules
    for k in origenvval:
        if origenvval[k] is not None:
            os.environ[k] = origenvval[k]
        elif k in os.environ:
            del os.environ[k]

    # restore the original otterwiki module objects so that other tests'
    # module-level references stay bound to the same graph a fresh import
    # would return (otherwise e.g. the DataTable renderer and collect_hook end
    # up split across two plugin_manager instances).
    for mod in [k for k in sys.modules if k.startswith('otterwiki')]:
        del sys.modules[mod]
    sys.modules.update(saved_otterwiki_modules)


def test_initialization_type_by_env(create_app_with_env_setting):
    """
    Test setting a variety of configuration settings
    by environment variable.  The type should be that
    the default value set during app initialisation
    """
    values = [
        # These are just arbitrarily chosen for
        # having the appropriate types
        # booleans
        ["SESSION_COOKIE_HTTPONLY", "truE", True],
        ["SESSION_COOKIE_SECURE", "yeS", True],
        ["SESSION_COOKIE_PARTITIONED", "oN", True],
        ["SESSION_REFRESH_EACH_REQUEST", "1", True],
        ["GIT_WEB_SERVER", "falsE", False],
        ["GIT_REMOTE_PUSH_ENABLED", "nO", False],
        ["GIT_REMOTE_PULL_ENABLED", "ofF", False],
        ["GIT_REMOTE_PULL_URL_SECURE", "0", False],
        ["HIDE_LOGO", "Anything Else", False],
        # string
        ["DEFAULT_COMMIT_MESSAGE", "hello", "hello"],
        # int
        ["PASSWORD_MIN_LENGTH", "66", 66],
    ]

    envdict = {}
    for name, text, _ in values:
        assert type(text) is str
        envdict[name] = text

    app = create_app_with_env_setting(envdict)

    for name, _, rightvalue in values:
        value = app.config[name]
        assert type(value) is type(rightvalue)
        assert value == rightvalue


def test_invalid_int_by_env(create_app_with_env_setting, caplog):
    """
    An invalid int in the environment logs a warning
    and keeps the default value.
    """
    app = create_app_with_env_setting({"PASSWORD_MIN_LENGTH": "abc"})

    assert app.config["PASSWORD_MIN_LENGTH"] == 8
    assert "PASSWORD_MIN_LENGTH='abc'" in caplog.text
