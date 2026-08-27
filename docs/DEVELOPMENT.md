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
