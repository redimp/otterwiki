#!/usr/bin/env python3

"""
This is an example plugin for An Otter Wiki

The hook is inside a class named NoEmojiPlugin, to make the
plugin_manager find it, the class has to be registered.
"""

import re
from otterwiki.plugins import hookimpl, plugin_manager


class NoEmojiPlugin:
    # re from https://stackoverflow.com/a/58356570/212768
    emojis = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002500-\U00002BEF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642"
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # dingbats
        u"\u3030"
        "]+",
        re.UNICODE,
    )

    @hookimpl
    def renderer_markdown_preprocess(self, md):
        return self.emojis.sub('', md)

# this is ne
plugin_manager.register(NoEmojiPlugin())

def test_noemoji():
    noemoji = NoEmojiPlugin()
    assert noemoji.preprocess_markdown("👴") == ""
    assert noemoji.preprocess_markdown("🕶H🦴ello, W🎲orld😇!") == "Hello, World!"
