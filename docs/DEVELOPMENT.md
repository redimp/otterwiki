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

Files, under `otterwiki/translations/`:

- `messages.pot`: every string to translate, extracted from the sources;
- `<lang>/LC_MESSAGES/messages.po`: a catalog, what translators edit;
- `<lang>/LC_MESSAGES/messages.mo`: the compiled catalog the app reads. It is
  committed, so a plain `pip install` or a `docker build` needs no extra step.

Commands:

```sh
make translations-extract   # refresh messages.pot from the sources
make translations-update    # extract, merge into every .po, compile
make translations-compile   # compile the .po files after editing them
# start a new language, e.g. German
venv/bin/pybabel init -i otterwiki/translations/messages.pot -d otterwiki/translations -l de
```

Plugins can keep using English strings; translating them is up to each
plugin, with its own catalog.
