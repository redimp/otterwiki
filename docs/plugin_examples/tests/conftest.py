#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

"""
Fixtures for testing the plugin examples in docs/plugin_examples without
installing them.
"""

import glob
import importlib.util
import os
import sys

import pytest

# make the repository root importable so the app fixtures from
# tests/conftest.py can be reused
_REPOSITORY_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
sys.path.insert(0, _REPOSITORY_ROOT)

from tests.conftest import *  # noqa: E402,F401,F403

PLUGIN_EXAMPLES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)


@pytest.fixture
def example_plugin_loader():
    """Load plugin examples from docs/plugin_examples without installing them.

    Executing a plugin module registers its plugin instance(s) with the
    plugin_manager. Every plugin registered through this fixture is
    unregistered on teardown, keeping the tests independent of each other.
    """
    import otterwiki.plugins

    plugin_manager = otterwiki.plugins.plugin_manager
    registered = []

    def load(plugin_directory):
        (module_path,) = glob.glob(
            os.path.join(
                PLUGIN_EXAMPLES_DIR, plugin_directory, "otterwiki_*.py"
            )
        )
        module_name = os.path.splitext(os.path.basename(module_path))[0]
        before = set(plugin_manager.get_plugins())
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        plugins = [p for p in plugin_manager.get_plugins() if p not in before]
        registered.extend(plugins)
        return module, plugins

    yield load

    for plugin in registered:
        plugin_manager.unregister(plugin)
