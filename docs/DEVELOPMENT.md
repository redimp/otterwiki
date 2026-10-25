# Development Design Decisions

This document collects design decisions made while developing An Otter Wiki.
It is meant to be referenced from `CLAUDE.md` and grow over time.

## Routing: `url_for` and the editor endpoint

The editor is served through the `view` route using an `?edit` query flag
(`Pagename?edit`) instead of a dedicated `/edit` path, so the editor keeps the
same base url as the rendered page.

To make this transparent, `otterwiki/helper.py` provides a `url_for()` wrapper
that is a drop-in replacement for `flask.url_for`:

- Every endpoint is passed through to `flask.url_for` unchanged, except `edit`.
- `url_for("edit", path=...)` is rewritten to the matching `view` url with
  `?edit` appended. Remaining values (e.g. `revision`) become query arguments.

Use this wrapper everywhere instead of `flask.url_for`. It is registered as the
jinja global `url_for`, so templates (`{{ url_for("edit", ...) }}`) emit the
rewritten links automatically.

The `view` route (`otterwiki/views.py`) accepts `GET`/`POST` and serves the
editor when `edit` is present in the request values. The dedicated
`/<path>/edit` route is kept for existing links.

The wrapper lives in `helper.py` (not `util.py`) because it depends on
`flask.url_for`; `util.py` is the lightweight, Flask-free layer.

## Translations

The interface is translated with [Flask-Babel](https://python-babel.github.io/flask-babel/)
and the standard gettext tooling. English, the language of the templates, is
the source: a string without a translation is shown in English, so a partial
catalog is safe to ship.

The language is chosen in `get_locale()` (`otterwiki/server.py`), the first one
a catalog exists for (`fr-FR` uses `fr`) of:

1. the language picked in the menu, kept in the `otterwiki_language` cookie,
   when `LANGUAGE_MENU` is enabled;
2. the browser's preferred language (`Accept-Language`), when
   `LANGUAGE_FROM_BROWSER` is enabled;
3. `SITE_LANG`, which is also the `lang` of the pages;
4. English.

Both settings are off by default: the interface is in `SITE_LANG`. Each
combination is a usual strategy: a fixed language, the browser's, the
visitor's choice with `SITE_LANG` as default, or the visitor's choice with
the browser's as default.

Mark a string for translation:

- in a template: `{{ _("Search") }}`, with variables
  `{{ _("%(count)s pages", count=n) }}`;
- in Python: `from flask_babel import gettext as _`, or `lazy_gettext` for
  strings defined at import time.

Plurals: `ngettext("%(num)s page", "%(num)s pages", n)`, and in
templates `{{ ngettext(...) }}`. A sentence with markup stays one message:
`{% trans url=... %}See the <a href="{{ url }}">help</a>.{% endtrans %}`.
What is written to the git repository (commit messages, initial pages) is
content and stays in English.

`otterwiki/translations/messages.pot` holds every string to translate. Run
`make translations-extract` after adding or changing one, and commit it.

The catalogs themselves are not part of the wiki: each language is a plugin,
a *language pack*, released on its own schedule
([otterwiki-translations](https://github.com/quazardous/otterwiki-translations)
has one package per language and the tools to sync and check them). A
language pack implements the `translation_directories` hook
(`otterwiki/plugins.py`) and returns the folder of its catalogs:

```python
import os
from otterwiki.plugins import hookimpl, plugin_manager

class LanguagePack:
    @hookimpl
    def translation_directories(self):
        # holds <lang>/LC_MESSAGES/messages.mo, made from messages.pot
        return os.path.join(os.path.dirname(__file__), "translations")

plugin_manager.register(LanguagePack())
```

The folders of every installed plugin are merged, so a pack may also
complete or correct another one. The language menu and the browser
detection offer every installed language.

The tests use a tiny French catalog, `tests/translations`, registered the
same way in `tests/conftest.py`.
