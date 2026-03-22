#!/usr/bin/env python
# vim: set et ts=8 sts=4 sw=4 ai:

from bs4 import BeautifulSoup


def test_help_page(test_client):
    rv = test_client.get('/-/help')
    assert rv.status_code == 200
    soup = BeautifulSoup(rv.data.decode(), 'html.parser')
    # check that the page has a title
    title = soup.find('title')
    assert title is not None
    # check that help content is rendered
    assert soup.find('div') is not None
    # check for navigation links to other help topics in the sidebar
    sidebar_links = soup.find_all('a', class_='sidebar-link', href=True)
    hrefs = [a['href'] for a in sidebar_links]
    assert any('/-/help/syntax' in h for h in hrefs)
    assert any('/-/help/admin' in h for h in hrefs)
    # check that the edit button span is rendered
    btn_span = soup.find('span', class_='btn btn-primary btn-sm btn-hlp')
    assert btn_span is not None, 'Edit button span not found in help page'
    assert (
        btn_span.find('i', class_='fas fa-pencil-alt') is not None
    ), 'Pencil icon not found inside edit button span'
    # check that help topics are present as h3 headings
    h3_texts = [h3.get_text(strip=True) for h3 in soup.find_all('h3')]
    help_topics = [
        'Editing and creating pages',
        'Attachments',
        'Search',
        'Page index',
        'Changelog',
        'Subdirectories',
    ]
    for topic in help_topics:
        assert topic in h3_texts, f'Help topic {topic!r} not found in h3 tags'
    # check that the sidebar has links with class sidebar-link for each topic
    for topic in help_topics:
        anchor = '#' + topic.lower().replace(' ', '-')
        assert any(
            anchor in h for h in hrefs
        ), f'Sidebar link for {topic!r} not found with class sidebar-link'


def test_help_syntax_page(test_client):
    rv = test_client.get('/-/help/syntax')
    assert rv.status_code == 200
    soup = BeautifulSoup(rv.data.decode(), 'html.parser')
    title = soup.find('title')
    assert title is not None
    # check that syntax topics are present as h3 headings
    h3_texts = [h3.get_text(strip=True) for h3 in soup.find_all('h3')]
    for topic in [
        'Emphasis',
        'Headings',
        'Lists',
        'Links',
        'Quotes',
        'Images',
        'Tables',
        'Code',
    ]:
        assert (
            topic in h3_texts
        ), f'Syntax topic {topic!r} not found in h3 tags'
    # check that the sidebar has links with class sidebar-link for each topic
    sidebar_links = soup.find_all('a', class_='sidebar-link', href=True)
    sidebar_hrefs = [a['href'] for a in sidebar_links]
    for topic in [
        'emphasis',
        'headings',
        'lists',
        'links',
        'quotes',
        'images',
        'tables',
        'code',
    ]:
        assert any(
            f'#{topic}' in h for h in sidebar_hrefs
        ), f'Sidebar link for {topic!r} not found with class sidebar-link'


def test_help_admin_page(test_client):
    rv = test_client.get('/-/help/admin')
    assert rv.status_code == 200
    soup = BeautifulSoup(rv.data.decode(), 'html.parser')
    title = soup.find('title')
    assert title is not None
    # check that admin topics are present as h3 headings
    h3_texts = [h3.get_text(strip=True) for h3 in soup.find_all('h3')]
    admin_topics = [
        'Branding',
        'Meta data',
        'User management',
        'Sidebar Preferences',
        'Content and Editing Preferences',
        'Access Permissions and Registration Preferences',
        'Mail Preferences',
    ]
    for topic in admin_topics:
        assert topic in h3_texts, f'Admin topic {topic!r} not found in h3 tags'
    # check that the sidebar has links with class sidebar-link for each topic
    sidebar_links = soup.find_all('a', class_='sidebar-link', href=True)
    sidebar_hrefs = [a['href'] for a in sidebar_links]
    for topic in admin_topics:
        anchor = '#' + topic.lower().replace(' ', '-')
        assert any(
            anchor in h for h in sidebar_hrefs
        ), f'Sidebar link for {topic!r} not found with class sidebar-link'
    # check that the settings button span is present in the rendered html
    settings_spans = soup.find_all('span', class_='help-button')
    found = any(
        s.find('span', class_='btn btn-square btn-sm')
        and s.find('i', class_='fas fa-cog')
        and 'Settings' in s.get_text()
        for s in settings_spans
    )
    assert found, 'Settings button span with cog icon not found in admin help'
