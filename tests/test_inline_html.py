#!/usr/bin/env python3
# vim: set et ts=8 sts=4 sw=4 ai:

"""
Inline html used in real wikis that must keep working with the default
allowlist, see https://github.com/redimp/otterwiki/discussions/581
"""

import pytest
from bs4 import BeautifulSoup, Tag
from otterwiki.renderer import render

# (markdown, tags expected in the rendered html)
EXAMPLES = [
    # video
    (
        '<div style="float: right; max-width: 400px; width: 100%; margin-left: 20px; margin-bottom: 10px;"><video style="width: 100%; height: auto;" controls><source src="/webpage/video.mp4" type="video/mp4"></video></div>',
        ['div', 'video', 'source'],
    ),
    (
        '<div style="max-width: 400px; width: 100%; margin-bottom: 10px;"><video style="width: 100%; height: auto; display: block;" controls><source src="/webpage/video.mp4" type="video/mp4"></video></div>',
        ['div', 'video', 'source'],
    ),
    (
        '<div style="float: right; max-width: 400px; width: 50%; margin-left: 20px; margin-bottom: 10px;"><video style="width: 50%; height: auto;" controls><source src="webpage/video" type="video/mp4"></video></div>',
        ['div', 'video', 'source'],
    ),
    # audio
    (
        '<audio controls style="width:100%;"><source src="/file.mp3" type="audio/mpeg"></audio>',
        ['audio', 'source'],
    ),
    # font color
    (
        '<div style="font-size:1em; text-align:left; color: inherit; margin-top:6px; line-height:1.3;">',
        ['div'],
    ),
    # images with links, padding and text wrap
    (
        '<a href="website.com"><img src="/image.jpg" width="500" height="200" alt="Description"></a>',
        ['a', 'img'],
    ),
    (
        '<a href="website.com" style="float: right; padding-left: 20px;"><img src="/image.png" width="400" height="200" style="max-width: 100%; height: auto;"></a>',
        ['a', 'img'],
    ),
    (
        '<div style="float: right; padding-left: 20px;"><img src="/image.png" width="400" height="200" alt="Description" style="max-width: 100%; height: auto;"></div>',
        ['div', 'img'],
    ),
    # font size
    (
        '<span style="font-size:2em; font-weight:lighter;">\ntext\n</span>',
        ['span'],
    ),
    # drop down menus
    (
        '<details>\n<summary>title here</summary>\n\nContent here\n</details>',
        ['details', 'summary'],
    ),
    (
        '<details>\n<summary>\n<span style="font-size:1.3em; font-weight:lighter;">\nMain Title\n</span>\n</summary>\n\nYour paragraph text goes here.\n\n</details>',
        ['details', 'summary', 'span'],
    ),
    # tooltip
    (
        '<a href="#" title="This text will display in the tooltip pop-up">Tooltip Text</a>',
        ['a'],
    ),
    # page divider
    (
        '<div style="border-top: 2px solid #A9A9A9; flex: 1; max-height: 0;"></div>',
        ['div'],
    ),
    (
        '<div style="border-top:2px solid #A9A9A9; width:580px; height:0;"></div>',
        ['div'],
    ),
    (
        '<div style="display: flex; align-items: center;">\n<div style="border-top: 2px solid #C82909; flex: 1; max-height: 0;"></div>\n<div style="border-top: 2px solid #C82909; flex: 1; max-height: 0;"></div></div>',
        ['div'],
    ),
    # embeddings
    (
        '{{Video\n|width=360px\n|height=500px\n|controls=true\n|autoplay=false\n|loop=false\n|src=/webpage/video.mp4\n}}',
        ['video', 'source'],
    ),
    (
        '{{ImageFrame\n|width=400px\n|style=float: right; margin: 0 0 0 20px;\n[![](/image.jpg)](https://github.com/)\n}}',
        ['div', 'a', 'img'],
    ),
    (
        '{{ImageFrame\n|width=400px\n|style=float: right; margin: 0 0 0 20px;\n![](/image.jpg)\n}}',
        ['div', 'img'],
    ),
]


@pytest.mark.parametrize("md,tags", EXAMPLES)
def test_inline_html_allowed(md, tags):
    html, _, _ = render.markdown(md)
    assert '&lt;' not in html
    soup = BeautifulSoup(html, 'html.parser')
    for tag in tags:
        assert soup.find(tag) is not None, tag


def test_inline_html_style_preserved():
    md = '<div style="float: right; padding-left: 20px;"><img src="/image.png" width="400" height="200" alt="Description" style="max-width: 100%; height: auto;"></div>'
    html, _, _ = render.markdown(md)
    soup = BeautifulSoup(html, 'html.parser')
    div = soup.find('div')
    img = soup.find('img')
    assert isinstance(div, Tag) and isinstance(img, Tag)
    assert div['style'] == 'float: right; padding-left: 20px;'
    assert img['style'] == 'max-width: 100%; height: auto;'
    assert img['src'] == '/image.png'
    assert img['width'] == '400'
