#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

import pytest
import os
import tempfile


def test_load_custom_html_nonexistent_file(create_app):
    """Test loading a non-existent custom HTML file returns empty string"""
    app = create_app

    from otterwiki.helper import load_custom_html

    with app.app_context():
        result = load_custom_html('nonexistent.html')
        assert result == ""


def test_custom_html(test_client, create_app):
    """Test that custom HTML works with HTML_EXTRA_HEAD, HTML_EXTRA_BODY and custom files"""
    app = create_app

    app.config['HTML_EXTRA_HEAD'] = (
        '<meta name="env-head" content="env-head-value">'
    )
    app.config['HTML_EXTRA_BODY'] = (
        '<script>console.log("env-body-script");</script>'
    )

    custom_dir = os.path.join(app.root_path, 'static', 'custom')
    os.makedirs(custom_dir, exist_ok=True)

    head_content = '<meta name="file-head" content="file-head-value">'
    body_content = '<script>console.log("file-body-script");</script>'

    head_file = os.path.join(custom_dir, 'customHead.html')
    body_file = os.path.join(custom_dir, 'customBody.html')

    with open(head_file, 'w', encoding='utf-8') as f:
        f.write(head_content)

    with open(body_file, 'w', encoding='utf-8') as f:
        f.write(body_content)

    try:
        response = test_client.get('/')
        html = response.data.decode('utf-8')

        assert 'env-head-value' in html
        assert 'file-head-value' in html
        assert 'env-body-script' in html
        assert 'file-body-script' in html

    finally:
        for file_path in [head_file, body_file]:
            if os.path.exists(file_path):
                os.remove(file_path)
