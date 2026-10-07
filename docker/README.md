# Docker images

An Otter Wiki is published as two images on Docker Hub
(`redimp/otterwiki`):

| Image   | Dockerfile               | Tags                                    |
|---------|--------------------------|-----------------------------------------|
| regular | `Dockerfile`             | `latest`, `2`, `2.25`, `2.25.0`         |
| slim    | `docker/Dockerfile.slim` | `2-slim`, `2.25-slim`, `2.25.0-slim`    |

Both are built via the `Makefile` targets `docker-push` and
`docker-push-slim`.

## Labels

Both images set the same labels in their final stage:

| Label                              | Value                                       |
|------------------------------------|---------------------------------------------|
| `maintainer`                       | `Ralph Thesen <mail@redimp.de>`             |
| `org.opencontainers.image.source`  | `https://github.com/redimp/otterwiki`       |
| `org.opencontainers.image.version` | the version, see below                      |

`org.opencontainers.image.version` is set from the `VERSION` build
argument. The `Makefile` reads the version from `otterwiki/version.py`
and passes it with a suffix depending on the kind of build:

| Build   | Make target                              | Branch | Example value             |
|---------|------------------------------------------|--------|---------------------------|
| release | `docker-push`, `docker-push-slim`        | `main` | `2.25.0`                  |
| dev     | `docker-push`, `docker-push-slim`        | other  | `2.25.0-dev-feature-xyz`  |
| local   | `docker-run`, `docker-run-slim`          | any    | `2.25.0-local`            |

The dev suffix is the sanitized branch name, the same as in the image
tag `dev-<branch>`. When an image is built with `docker build` directly,
without passing `--build-arg VERSION=...`, the label is empty.

## Environment

Besides the labels, both images set the environment variable `GIT_TAG`
from the `GIT_TAG` build argument. The `Makefile` passes the output of
`git describe --long`, e.g. `v2.25.0-4-g6e72b38`, and appends
`_<branch>` for dev images. It is shown on the About page.

## Finding the version

Read the label of an image:
```sh
docker inspect -f '{{ index .Config.Labels "org.opencontainers.image.version" }}' redimp/otterwiki:latest
```

Read the label of a running container:
```sh
docker inspect -f '{{ index .Config.Labels "org.opencontainers.image.version" }}' <container>
```

Show all labels:
```sh
docker inspect -f '{{ json .Config.Labels }}' redimp/otterwiki:latest
```

Ask the installed package inside a running container:
```sh
docker exec <container> python -c 'from otterwiki import __version__; print(__version__)'
```
