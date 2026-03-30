#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:


def test_security_headers_enabled_by_default(app_with_user, test_client):
    response = test_client.get("/")
    assert response.headers.get('X-Content-Type-Options') == 'nosniff'
    assert response.headers.get('X-Frame-Options') == 'SAMEORIGIN'
    assert response.headers.get('Referrer-Policy') == 'same-origin'


def test_security_headers_disabled(app_with_user, test_client):
    app_with_user.config['SECURITY_HEADERS'] = False
    response = test_client.get("/")
    assert 'X-Content-Type-Options' not in response.headers
    assert 'X-Frame-Options' not in response.headers
    assert 'Referrer-Policy' not in response.headers
    # restore
    app_with_user.config['SECURITY_HEADERS'] = True
