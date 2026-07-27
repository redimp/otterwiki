# Examples for plugins into An Otter Wiki

An Otter Wiki uses [pluggy](https://pluggy.readthedocs.io/en/stable/) to provide
function hooks that can be used to add or modify features via plugins.

The API for plugins is currently experimental and very limited. If you
want to write an plugin and cannot find a matching hook, please open
up an [issue](https://github.com/redimp/otterwiki/issues).

## Installation of plugins

Plugins need to be installed in the (virtual) environment that runs the
flask app. If in a virtual environment just `pip install .` the directory
that contains the plugin.

### Plugins into the Docker image

The `entrypoint.sh` checks before running the app the paths

- /app-data/plugins
- /plugins

for plugins to install. So you can either add the plugins as a directory to
the volume that keeps the `app-data`, where also the `db.sqlite` and the
`repository` lives. Or you organize the plugins in a separate directory
which you mount in the container into `/plugins`.

*Note:* For plugins with complex dependencies the docker image might be missing
packages. In this case adding these packages to the image is inevitable, a
custom image (which packs the plugin, too) might be the best solution.

#### Plugins with SELinux

In environments with `SELINUX=enforcing` the bind mounts have to be adjusted,
please check the [FAQ](https://otterwiki.com/FAQ#environments-with-selinux).

## Uninstalling plugins

When running An Otter Wiki from a virtual environment run `pip uninstall
<plugin-name>`. When running from a docker image it is recommended to recreate
the container for a clean environment, after removing the plugin from the
directory.

### Demo of the example plugins

You can find a `docker-compose.yaml` in [docs/plugin_examples](https://github.com/redimp/otterwiki/tree/main/docs/plugin_examples).

## Testing the example plugins

The example plugins are tested in [docs/plugin_examples/tests](https://github.com/redimp/otterwiki/tree/main/docs/plugin_examples/tests).
The `example_plugin_loader` fixture defined in the `conftest.py` there
loads a plugin straight from its directory, no installation is needed.
Plugins loaded via the fixture are unregistered on teardown, which keeps
the tests independent of each other.

The tests run as part of the test suite via `make test`, or standalone with

```bash
OTTERWIKI_SETTINGS="" venv/bin/pytest docs/plugin_examples/tests
```

To add tests for a new example plugin, create a `test_<name>.py` next to
the existing ones and load the plugin with
`example_plugin_loader("plugin_<name>")`. If the plugin implements the
`setup()` hook, call it on the loaded instance, see
`test_referencingpages.py` for an example.
