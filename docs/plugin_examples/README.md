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
`repostitory` lives. Or you organize the plugins in a separate directory
which you mount in the container into `/plugins`.

*Note:* For plugins with complex dependencies the docker image might be missing
packages. In this case adding these packages to the image is inevitable, a
custom image (which packs the plugin, too) might be the best solution.

### Demo of the example plugins

You can find a `docker-compose.yaml` in [docs/plugin_examples](https://github.com/redimp/otterwiki/tree/main/docs/plugin_examples).

