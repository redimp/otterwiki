# User Info Plugin

This example plugin shows the logged-in user in the navbar of An Otter Wiki,
see [#574](https://github.com/redimp/otterwiki/issues/574). It also shows how
a plugin can ship its own Jinja templates.

## Features

- Shows the logged-in user left of the navbar menu button. The admin
  selects what to show:
  - the name of the user (default),
  - the email address,
  - the initial, e.g. `T` for "Test User", as a round badge,
  - the initials, e.g. `TU` for "Test User" or `JD` for "john.doe", as a
    round badge,
  - nothing, e.g. to show only the Gravatar icon.
- Optionally shows the [Gravatar](https://gravatar.com) icon of the user.
  The admin selects the icon for email addresses without a Gravatar.
- Marks admin users with a shield icon. The admin can turn this off.
- Adds a "Logged in as" line with the name and the email address to the top
  of the navbar dropdown menu.
- The navbar entry links to the user settings. Anonymous users see nothing.

### Configuration

Admins configure the plugin in the Settings via **User Info**
(`/-/admin/plugin/userinfo/settings`). The plugin stores the settings in the
`Preferences` table, with names that start with `PLUGIN_USERINFO_`. The
plugin reads the settings once per request, so all worker processes use the
same settings. When you uninstall the plugin, these rows stay in the
database.

### Privacy

The Gravatar icon is off by default. When it is on, the browser of the user
loads the icon from gravatar.com. The request contains a SHA256 hash of the
email address of the user.

## Installation

```bash
pip install docs/plugin_examples/plugin_userinfo
```

For development, install the plugin in editable mode, so the wiki uses your
changes to the source:

```bash
venv/bin/pip install -e docs/plugin_examples/plugin_userinfo
make debug
```

For the Docker image, see the
[README](../README.md#plugins-into-the-docker-image) of the plugin examples.

## How it works

### A plugin as a package with templates

Most example plugins are a single module, e.g. `otterwiki_redlinks.py`. This
plugin is a package, because it ships a template file:

```
plugin_userinfo/
├── pyproject.toml
├── README.md
└── otterwiki_userinfo/
    ├── __init__.py
    └── templates/
        └── userinfo/
            └── settings.html
```

- `pyproject.toml` defines the entry point
  `userinfo = "otterwiki_userinfo"`. An Otter Wiki loads all packages with an
  `otterwiki` entry point on startup. The name of the package directory must
  match the project name `otterwiki_userinfo`, so hatchling finds it.
- `otterwiki_userinfo/__init__.py` contains the plugin code and registers the
  plugin via `plugin_manager.register(UserInfo())`.
- `templates/userinfo/settings.html` is the admin page. Hatchling adds all
  files in the package directory to the wheel, so you do not have to
  configure the template in `pyproject.toml`.

A single module plugin cannot ship a template this way. When hatchling builds
a single module, it adds only the `.py` file to the wheel.

### Making the templates available

The plugin returns its template folder via the `template_folders` hook:

```python
@hookimpl
def template_folders(self):
    return [os.path.join(os.path.dirname(__file__), "templates")]
```

An Otter Wiki searches these folders after its own templates. Thus:

- A plugin cannot override a core template by mistake. A plugin file named
  `layout.html` has no effect.
- A plugin template can extend a core template. `settings.html` of the plugin
  starts with `{% extends "settings.html" %}`, so the admin page has the same
  layout and sidebar as the other admin pages.

To prevent name conflicts with other plugins, put the templates in a
subfolder named after the plugin, here `userinfo/`. The plugin then renders
the page via:

```python
render_template("userinfo/settings.html", settings=..., ...)
```
