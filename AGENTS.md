# AGENTS.md — An Otter Wiki Codebase Reference

Dense reference for AI coding agents. Not a tutorial. All facts verified against source files.

---

## Project Overview

**An Otter Wiki** is a Python/Flask wiki with git-backed Markdown storage.

- **Version**: 2.19.0 (see `otterwiki/version.py`)
- **Python**: >=3.11 (enforced in `pyproject.toml`)
- **License**: MIT
- **Homepage**: https://otterwiki.com
- **Default port**: 8080

Core value proposition: every page edit is a git commit; full history and diff available for every page and attachment.

---

## Architecture Overview

```
HTTP request
    -> Flask app (server.py — module-level singleton)
    -> views.py (route handlers, imported for side effects)
    -> wiki.py (Page / Changelog / Attachment / Search / AutoRoute)
    -> gitstorage.py (GitStorage — gitpython wrapper)
    -> renderer.py (OtterwikiRenderer — mistune 3.x pipeline)
    -> auth.py (SimpleAuth or ProxyHeaderAuth — Flask-Login)
    -> models.py (SQLAlchemy: Preferences / Drafts / User / Cache)
    -> plugins.py (pluggy plugin_manager, "otterwiki" namespace)
```

**Config layering** (lowest to highest precedence):

1. `app.config` defaults hardcoded in `server.py`
2. `settings.cfg` file, path from `OTTERWIKI_SETTINGS` env var
3. Individual env vars matching any `app.config` key
4. `Preferences` table (admin UI writes here; loaded via `update_app_config()`)

**Singletons** in `server.py` (module-level, imported everywhere):

- `app` — Flask application
- `db` — Flask-SQLAlchemy instance
- `storage` — `GitStorage` instance
- `mail` — Flask-Mail instance (set after `update_app_config()`)
- `app_renderer` — `OtterwikiRenderer` instance
- `githttpserver` — `GitHttpServer` instance

`views.py` is imported at the bottom of `server.py` purely for its route-registration side effects (no public API).

---

## Module Map

| Module | Purpose |
|---|---|
| `server.py` | Flask app factory, config layering, global singletons, Jinja filters |
| `views.py` | All HTTP route handlers; delegates to wiki/auth/preferences/tools |
| `wiki.py` | `Page`, `Changelog`, `Attachment`, `Search`, `AutoRoute` classes |
| `auth.py` | `SimpleAuth`, `ProxyHeaderAuth`; module-level proxy functions to `auth_manager` |
| `renderer.py` | Markdown-to-HTML pipeline: `OtterwikiRenderer`, `OtterwikiMdRenderer`, block/inline parsers |
| `renderer_plugins.py` | Custom mistune plugins: footnotes, task lists, math, fancy blocks, alerts, spoilers, fold, wikilinks, frontmatter, embeddings |
| `renderer_embeddings.py` | Built-in embedding plugins registered via pluggy |
| `gitstorage.py` | `GitStorage` class; wraps gitpython; raises `StorageError`, `StorageNotFound` |
| `models.py` | SQLAlchemy models: `Preferences`, `Drafts`, `User`, `Cache` |
| `plugins.py` | `OtterWikiPluginSpec` hookspecs; `chain_hooks`, `call_hook`, `collect_hook`; `plugin_manager` |
| `helper.py` | `toast`, `send_mail`, breadcrumbs, page name resolution, `clean_html`, caching |
| `util.py` | `slugify`, `sanitize_pagename`, path utils, `ttl_lru_cache`, `sizeof_fmt`, validators |
| `preferences.py` | Admin preference form handlers and renderers |
| `sidebar.py` | `SidebarMenu`, `SidebarPageIndex`, `SidebarPageIndexEntry` |
| `pageindex.py` | `PageIndex` class |
| `pluginmgmt.py` | Plugin info collection, help generation |
| `repomgmt.py` | `RepositoryManager` for remote git push/pull |
| `remote.py` | `GitHttpServer` — git HTTP smart protocol |
| `cli.py` | Flask CLI: `flask user create/edit/password/delete/list` |
| `tools.py` | Housekeeping: drafts cleanup, empty pages, broken wikilinks |
| `sitemap.py` | XML sitemap generation |
| `profiler.py` | Dev profiler (excluded from coverage) |
| `version.py` | `__version__` string; managed by tbump |

---

## Directory Structure

```
otterwiki/           Python package
  static/            CSS, JS (CodeMirror, halfmoon, Font Awesome)
  templates/         Jinja2 HTML templates
  *.md               Bundled content: help.md, help_admin.md, initial_home.md, about.md
tests/               pytest test suite
  conftest.py        Shared fixtures
  test_*.py          One file per feature area
docs/                Documentation and plugin examples
helm/                Helm chart
docker/              Dockerfile variants
.pre-commit-config.yaml
pyproject.toml       Package config, tool config (black, tox, pyright, pytest, coverage)
Makefile             Dev workflow commands
settings.cfg.skeleton  Example settings file
```

---

## Build, Test & Run Commands

### Development setup

```sh
make venv          # create venv, install deps (pip install -e '.[dev]'), install pre-commit hooks
```

### Running

```sh
make run           # Flask dev server on port 8080 (requires settings.cfg)
make debug         # Flask debug mode, port 8080
make shell         # Flask interactive shell
make cli ARGS="..."  # Run flask CLI commands with settings.cfg
```

### Testing

```sh
make test          # OTTERWIKI_SETTINGS="" venv/bin/pytest tests
make coverage      # pytest with coverage report + HTML output in coverage_html/
make tox           # tox across py3.11, py3.12, py3.13
```

**Critical**: Tests require `OTTERWIKI_SETTINGS=""`. Without it, any settings.cfg on disk pollutes the test run. The `conftest.py` `create_app` fixture sets `OTTERWIKI_SETTINGS` to a temp file.

Direct invocation:

```sh
OTTERWIKI_SETTINGS="" venv/bin/pytest tests
OTTERWIKI_SETTINGS="" venv/bin/pytest tests/test_renderer.py -k test_name
```

### Code formatting

```sh
make black         # venv/bin/black setup.py otterwiki/ tests/
```

### Cleaning

```sh
make clean         # remove venv, __pycache__, .pytest_cache, .tox, coverage_html
```

---

## Code Style & Conventions

### Black

Configured in `pyproject.toml` `[tool.black]`:

- `line-length = 79`
- `skip-string-normalization = true` (single quotes preferred)

### Pre-commit hooks

`.pre-commit-config.yaml` runs on every commit:

1. `check-yaml` (excludes `helm/templates/`)
2. `end-of-file-fixer`
3. `trailing-whitespace`
4. `black` (rev 24.10.0)

### Pyright

`typeCheckingMode = "strict"` with several overrides in `pyproject.toml`. Notable relaxations: `reportUnknownMemberType`, `reportUnknownVariableType`, `reportAttributeAccessIssue`, `reportCallIssue` are all disabled.

### Vim modelines

Every Python file starts with:

```python
# vim: set et ts=8 sts=4 sw=4 ai:
```

This is a convention, not enforced by tooling. Match it in new files.

### Naming

- Page paths use forward slashes: `Namespace/PageName`
- By default, page names are lowercased unless `RETAIN_PAGE_NAME_CASE=True`
- Attachment directory = page path without `.md` extension
- URL-safe slugs via `util.slugify()`: NFKD normalise, ASCII, lowercase, hyphens

### Import style

Module-level singletons from `server.py` are imported directly:

```python
from otterwiki.server import app, db, storage, app_renderer
```

Route handlers in `views.py` call business logic classes from `wiki.py` — no business logic in route handlers.

---

## Configuration System

Config keys live in `app.config`. Three layers:

1. **Defaults** — hardcoded `app.config.update(...)` block in `server.py`
2. **File** — `app.config.from_envvar("OTTERWIKI_SETTINGS", silent=True)` loads a Python config file
3. **Env vars** — `server.py` iterates `app.config` keys and checks `os.environ`; booleans match `"true"`, `"yes"`, `"on"`, `"1"`
4. **DB** — `update_app_config()` reads `Preferences` table rows and writes into `app.config`; also reinitialises Flask-Mail

### Key config keys

| Key | Default | Notes |
|---|---|---|
| `REPOSITORY` | `None` | Path to git repo. Required. |
| `SECRET_KEY` | `"CHANGE ME"` | Must be >=16 chars, not default |
| `SITE_NAME` | `"An Otter Wiki"` | |
| `AUTH_METHOD` | `""` | `""` = SimpleAuth, `"proxy"` = ProxyHeaderAuth |
| `READ_ACCESS` | `"ANONYMOUS"` | `ANONYMOUS`, `REGISTERED`, `APPROVED`, `ADMIN` |
| `WRITE_ACCESS` | `"ANONYMOUS"` | Same options |
| `ATTACHMENT_ACCESS` | `"ANONYMOUS"` | Same options |
| `RETAIN_PAGE_NAME_CASE` | `False` | If False, page names are lowercased |
| `SQLALCHEMY_DATABASE_URI` | `"sqlite:///:memory:"` | Change for persistent DB |
| `OTTERWIKI_SETTINGS` | — | Env var pointing to `settings.cfg` |
| `HOME_PAGE` | `""` | Custom home page path; `/-/`-prefixed redirects |
| `COMMIT_MESSAGE` | `"REQUIRED"` | `REQUIRED`, `OPTIONAL`, `DISABLED` |
| `GIT_WEB_SERVER` | `False` | Enable git HTTP smart protocol |
| `ROBOTS_TXT` | `"allow"` | `"allow"` or `"disallow"` |
| `SIDEBAR_MENUTREE_MODE` | `"SORTED"` | |
| `MINIFY_HTML` | `True` | |

See `server.py` `app.config.update(...)` for the full list of defaults.

### settings.cfg format

Standard Python config file (`app.config.from_envvar` uses `from_pyfile` internally):

```python
REPOSITORY = '/app-data/repo'
SECRET_KEY = 'your-random-key'
SITE_NAME = 'My Wiki'
SQLALCHEMY_DATABASE_URI = 'sqlite:////app-data/otterwiki.db'
```

---

## Testing Patterns

### Fixtures (defined in `tests/conftest.py`)

| Fixture | Scope | Description |
|---|---|---|
| `create_app` | function | Temp dir with git repo + `settings.cfg`. Sets `OTTERWIKI_SETTINGS`. Yields Flask app. |
| `test_client` | function | Unauthenticated Flask test client |
| `req_ctx` | function | Flask request context (`app.test_request_context()`) |
| `app_with_user` | function | `create_app` + admin user (`mail@example.org` / `password1234`) + non-admin user (`another@user.org` / `password4567`) |
| `admin_client` | function | Logged-in admin test client |
| `other_client` | function | Logged-in non-admin test client |

### Fixture dependency chain

```
create_app
    -> test_client
    -> req_ctx
       -> app_with_user
          -> admin_client
          -> other_client
```

### Test file coverage

| File | Area |
|---|---|
| `test_essentials.py` | Core page operations |
| `test_otterwiki.py` | General integration |
| `test_auth.py` | Auth flows |
| `test_renderer.py` | Markdown rendering |
| `test_gitstorage.py` | Git storage layer |
| `test_attachments.py` | File attachments |
| `test_editor.py` | Editor / draft handling |
| `test_draft.py` | Draft save/restore |
| `test_history.py` | Page history and diffs |
| `test_home_page.py` | Home page config |
| `test_pageindex.py` | Page index |
| `test_sidebar.py` | Sidebar rendering |
| `test_preferences.py` | Admin preferences |
| `test_settings.py` | Settings UI |
| `test_cli.py` | Flask CLI commands |
| `test_embeddings.py` | Embedding plugins |
| `test_renderer.py` | Renderer pipeline |
| `test_util.py` | Utility functions |
| `test_helper.py` | Helper functions |
| `test_sitemap.py` | XML sitemap |
| `test_feed.py` | RSS/Atom feed |
| `test_seo.py` | SEO / meta tags |
| `test_remote.py` | Git HTTP server |
| `test_repository_management.py` | Remote push/pull |
| `test_housekeeping.py` | Housekeeping tools |
| `test_page_lifecycle_hooks.py` | Plugin lifecycle hooks |
| `test_preview.py` | Preview rendering |
| `test_custom_html.py` | Custom HTML injection |
| `test_image.png` | Test fixture file |

### Writing tests

- Use `test_client` for unauthenticated requests, `admin_client` for admin-only routes
- `app_with_user` is needed when testing auth-sensitive flows where no client login is required but users must exist
- Page creation via `test_client.post("/<pagepath>/-/save", data={...})`
- Check flash messages in `result.data.decode()` — `toast()` maps to halfmoon alert classes

---

## Key Patterns & Conventions

### Route structure (`views.py`)

- `/-/<name>` — system pages (login, settings, admin, help, about, changelog, etc.)
- `/<path:path>` — wiki pages (view, edit, save, history, rename, delete, attachments)
- `/<path:path>/-/<action>` — page-specific actions
- Plugin routes: `/-/plugin/<name>/<extra>` and `/-/admin/plugin/<name>/<extra>`

### Page name handling

The flow for a page path:

1. URL path segment decoded from URL
2. `sanitize_pagename()` in `util.py` — strips `?$.|!#\\`, leading `-/`, normalises slashes
3. Lowercased unless `RETAIN_PAGE_NAME_CASE=True`
4. Stored as `<pagename>.md` in the git repo

### Auth system (`auth.py`)

Two backends, selected by `AUTH_METHOD`:

- `""` (default) — `SimpleAuth`: DB-backed login, register, email confirmation, admin approval workflow
- `"proxy"` — `ProxyHeaderAuth`: trusts `x-otterwiki-name`, `x-otterwiki-email`, `x-otterwiki-permissions` headers

Both implement the same interface; `auth_manager` is assigned at module level to the correct backend. Module-level functions (`has_permission`, `get_user`, `login_user`, etc.) delegate to `auth_manager`.

Permission levels: `ANONYMOUS` > `REGISTERED` > `APPROVED` > `ADMIN`. `has_permission(permission)` checks `current_user`.

### Renderer pipeline (`renderer.py`)

`OtterwikiRenderer.render(md, pagepath)` pipeline:

1. `chain_hooks("renderer_markdown_preprocess", md)` — plugin preprocessing
2. mistune parse with custom block/inline parsers + registered plugins
3. Pygments for code blocks
4. `chain_hooks("renderer_html_postprocess", html)` — plugin postprocessing

Renderer plugins in `renderer_plugins.py` (mistune plugin protocol):

- `plugin_footnotes`, `plugin_task_lists`, `plugin_math`
- `plugin_fancy_blocks`, `plugin_alerts`, `plugin_spoiler`, `plugin_fold`
- `plugin_wikilink`, `plugin_frontmatter`, `plugin_frontmatter_title`
- `plugin_embeddings` — delegates to pluggy `embedding_render` hook

### Plugin system (`plugins.py`)

pluggy namespace: `"otterwiki"`. Entry point group: `"otterwiki"`.

```python
hookspec = pluggy.HookspecMarker("otterwiki")
hookimpl = pluggy.HookimplMarker("otterwiki")
plugin_manager = pluggy.PluginManager("otterwiki")
plugin_manager.load_setuptools_entrypoints("otterwiki")
```

Three utility functions for non-standard hook dispatch:

- `chain_hooks(hook_name, value, **kwargs)` — pipes output of each impl into the next
- `call_hook(hook_name, **kwargs)` — returns first non-None result
- `collect_hook(hook_name, **kwargs)` — returns list of all non-None results

Key hookspecs: `setup`, `renderer_markdown_preprocess`, `renderer_html_postprocess`, `embedding_render`, `page_saved`, `page_deleted`, `page_renamed`, `repository_changed`, `template_html_head_inject`, `template_html_body_inject`, `sidebar_page_index_filter_entries`, `sidebar_page_index_sort_entries`.

External plugins: install as Python packages with `otterwiki` entry point. See `docs/plugin_examples/`.

### Storage layer (`gitstorage.py`)

`GitStorage` wraps gitpython. Key methods: `store`, `load`, `delete`, `rename`, `list`, `log`, `diff`, `blame`. Raises `StorageError` or `StorageNotFound` on failure.

Reload trigger: presence of `.git/RELOAD_GIT` file causes `_read_repo()` on next request. Used by the git HTTP server after a push.

### Attachments

Stored in the git repo under `<pagepath-without-.md>/` directory. `get_attachment_directoryname()` in `helper.py` derives the dir name from page path.

### Caching

`ttl_lru_cache(ttl, maxsize)` in `util.py` wraps `functools.lru_cache` with time-based expiry. Used on expensive lookups (file TOC, page breadcrumbs).

`Cache` SQLAlchemy model stores rendered content keyed by SHA256 hash.

### Toast messages

`toast(message, category)` in `helper.py` wraps Flask `flash()`. Categories map to halfmoon CSS alert classes: `""` -> `alert-primary`, `"success"` -> `alert-success`, `"error"/"danger"` -> `alert-danger`, `"warning"` -> `alert-secondary`.

### HTML sanitization

`clean_html()` in `helper.py` sanitises user-supplied HTML. Allowlist configurable via `RENDERER_HTML_ALLOWLIST` config key.

### Wikilinks

Syntax: `[[Page Name]]` or `[[Page Name|Display Text]]`. Handled by `plugin_wikilink` in `renderer_plugins.py`. Pluggy hook `renderer_process_wikilink` allows plugin override.

### CLI (`cli.py`)

Flask CLI extension via `AppGroup("user")`. Commands: `flask user create`, `flask user edit`, `flask user password`, `flask user delete`, `flask user list`. Registered in `server.py` at import time.

---

## Key Dependencies

| Package | Version (pinned) | Role |
|---|---|---|
| `Flask` | 3.1.3 | Web framework |
| `Werkzeug` | 3.1.6 | WSGI utilities, password hashing |
| `Flask-Login` | 0.6.3 | Session-based auth |
| `Flask-Mail` | 0.10.0 | Email (registration, password reset) |
| `Flask-SQLAlchemy` | 3.1.1 | ORM integration |
| `SQLAlchemy` | 2.0.36 | Database ORM |
| `Jinja2` | 3.1.6 | HTML templating |
| `gitpython` | 3.1.44 | Git repository access |
| `mistune` | 3.2.0 | Markdown parser/renderer |
| `pygments` | 2.19.2 | Syntax highlighting |
| `Pillow` | 12.1.1 | Image handling (attachments, thumbnails) |
| `PyYAML` | 6.0.2 | Frontmatter parsing |
| `pluggy` | 1.5.0 | Plugin system |
| `beautifulsoup4` | 4.12.3 | HTML parsing (TOC, postprocessing) |
| `unidiff` | 0.7.5 | Diff/patchset handling |
| `feedgen` | 1.0.0 | RSS/Atom feed generation |
| `regex` | 2026.2.28 | Extended regex (with timeout support) |
| `cython` | 3.0.11 | Build dependency |

### Dev-only dependencies

`coverage`, `pytest`, `black`, `tox`, `tbump`, `rjsmin`, `git-changelog`, `pre-commit`, `types-Flask`.

Install with: `pip install -e '.[dev]'`

### Frontend (bundled static assets)

- **halfmoon** — CSS framework (dark mode support)
- **CodeMirror 5** — editor with Markdown syntax highlighting
- **Font Awesome Free** — icons
- `otterwiki/static/js/cm-modes.min.js` — bundled CodeMirror language modes; rebuilt with `make otterwiki/static/js/cm-modes.min.js`
