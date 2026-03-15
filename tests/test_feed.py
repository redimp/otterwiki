#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

from xml.etree.ElementTree import fromstring


def save_page(client, pagename, content, commit_message):
    rv = client.post(
        '/{}/save'.format(pagename),
        data={'content': content, 'commit': commit_message},
        follow_redirects=True,
    )
    assert rv.status_code == 200


def test_feed_rss_status_and_content_type(test_client):
    response = test_client.get('/-/changelog/feed.rss')
    assert response.status_code == 200
    assert response.content_type == 'application/rss+xml; charset=utf-8'


def test_feed_atom_status_and_content_type(test_client):
    response = test_client.get('/-/changelog/feed.atom')
    assert response.status_code == 200
    assert response.content_type == 'application/atom+xml; charset=utf-8'


def test_feed_rss_valid_xml(test_client):
    response = test_client.get('/-/changelog/feed.rss')
    root = fromstring(response.data)
    assert root.tag == 'rss'


def test_feed_atom_valid_xml(test_client):
    response = test_client.get('/-/changelog/feed.atom')
    root = fromstring(response.data)
    assert root.tag == '{http://www.w3.org/2005/Atom}feed'


def test_feed_rss_contains_entries(test_client):
    save_page(
        test_client,
        'FeedTestPage',
        '# Feed Test\n\nContent.',
        'Feed test commit',
    )
    response = test_client.get('/-/changelog/feed.rss')
    assert response.status_code == 200
    xml = response.data.decode()
    assert 'Feed test commit' in xml


def test_feed_atom_contains_entries(test_client):
    save_page(
        test_client,
        'AtomTestPage',
        '# Atom Test\n\nContent.',
        'Atom test commit',
    )
    response = test_client.get('/-/changelog/feed.atom')
    assert response.status_code == 200
    xml = response.data.decode()
    assert 'Atom test commit' in xml


def test_feed_rss_self_link(test_client):
    response = test_client.get('/-/changelog/feed.rss')
    xml = response.data.decode()
    assert 'feed.rss' in xml


def test_feed_atom_self_link(test_client):
    response = test_client.get('/-/changelog/feed.atom')
    xml = response.data.decode()
    assert 'feed.atom' in xml
