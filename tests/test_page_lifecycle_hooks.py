#!/usr/bin/env python

"""Tests for page lifecycle hooks (page_saved, page_deleted, page_renamed)."""

import sys

from otterwiki.plugins import hookimpl


def _get_plugin_manager():
    """Get the current plugin_manager, even after module reloads by other tests."""
    return sys.modules["otterwiki.plugins"].plugin_manager


class HookRecorder:
    """Test plugin that records hook calls."""

    def __init__(self):
        self.calls = []

    @hookimpl
    def page_saved(self, pagepath, content, author, message):
        self.calls.append(
            (
                "saved",
                {
                    "pagepath": pagepath,
                    "content": content,
                    "author": author,
                    "message": message,
                },
            )
        )

    @hookimpl
    def page_deleted(self, pagepath, author, message):
        self.calls.append(
            (
                "deleted",
                {"pagepath": pagepath, "author": author, "message": message},
            )
        )

    @hookimpl
    def page_renamed(self, old_pagepath, new_pagepath, author, message):
        self.calls.append(
            (
                "renamed",
                {
                    "old_pagepath": old_pagepath,
                    "new_pagepath": new_pagepath,
                    "author": author,
                    "message": message,
                },
            )
        )


def save_page(client, pagename, content, commit_message):
    rv = client.post(
        "/{}/save".format(pagename),
        data={"content": content, "commit": commit_message},
        follow_redirects=True,
    )
    assert rv.status_code == 200


def make_recorder():
    recorder = HookRecorder()
    _get_plugin_manager().register(recorder)
    return recorder


def test_page_saved_hook(test_client):
    recorder = make_recorder()
    try:
        save_page(test_client, "HookSaveTest", "# Hello", "create page")
        assert len(recorder.calls) == 1
        event, data = recorder.calls[0]
        assert event == "saved"
        assert data["pagepath"] == "HookSaveTest"
        assert "# Hello" in data["content"]
        assert data["message"] == "create page"
    finally:
        _get_plugin_manager().unregister(recorder)


def test_page_saved_hook_not_fired_when_unchanged(test_client):
    save_page(test_client, "HookNoChangeTest", "# Same", "create")
    recorder = make_recorder()
    try:
        # save identical content — hook should NOT fire
        save_page(test_client, "HookNoChangeTest", "# Same", "no-op save")
        assert len(recorder.calls) == 0
    finally:
        _get_plugin_manager().unregister(recorder)


def test_page_deleted_hook(test_client):
    save_page(test_client, "HookDeleteTest", "# Delete me", "create")
    recorder = make_recorder()
    try:
        rv = test_client.post(
            "/HookDeleteTest/delete",
            data={"message": "bye"},
            follow_redirects=True,
        )
        assert rv.status_code == 200
        assert len(recorder.calls) == 1
        event, data = recorder.calls[0]
        assert event == "deleted"
        assert data["pagepath"] == "HookDeleteTest"
        assert data["message"] == "bye"
    finally:
        _get_plugin_manager().unregister(recorder)


def test_page_renamed_hook(test_client):
    save_page(test_client, "HookRenameOld", "# Rename me", "create")
    recorder = make_recorder()
    try:
        rv = test_client.post(
            "/HookRenameOld/rename",
            data={"new_pagename": "HookRenameNew", "message": "renaming"},
            follow_redirects=True,
        )
        assert rv.status_code == 200
        assert len(recorder.calls) == 1
        event, data = recorder.calls[0]
        assert event == "renamed"
        assert data["old_pagepath"] == "HookRenameOld"
        assert data["new_pagepath"] == "HookRenameNew"
        assert data["message"] == "renaming"
    finally:
        _get_plugin_manager().unregister(recorder)
