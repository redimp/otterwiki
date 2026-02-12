#
# compile stage
#
FROM debian:12.11-slim AS compile-stage
LABEL maintainer="Ralph Thesen <mail@redimp.de>"
LABEL org.opencontainers.image.source="https://github.com/redimp/otterwiki"
# install python environment
RUN --mount=target=/var/cache/apt,type=cache,sharing=locked \
    rm /etc/apt/apt.conf.d/docker-clean && \
    apt-get update -y && \
    apt-get upgrade -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends python3.11 python3.11-venv \
    python3-pip libjpeg-dev zlib1g-dev build-essential python3-dev libxml2-dev libxslt-dev
# prepare environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
# upgrade pip and install requirements not in otterwiki
RUN --mount=type=cache,target=/root/.cache \
    pip install -U pip wheel toml
# copy src files
COPY pyproject.toml MANIFEST.in README.md LICENSE /src/
WORKDIR /src

# install requirements
RUN --mount=type=cache,target=/root/.cache \
    python -c 'import toml; print("\n".join(toml.load("./pyproject.toml")["project"]["dependencies"]));' > requirements.txt && \
    pip install -r requirements.txt

# copy otterwiki source and tests
COPY otterwiki /src/otterwiki
COPY tests /src/tests

# install the otterwiki
RUN pip install .
#
# test stage
#
FROM compile-stage AS test-stage
# install git (not needed for compiling)
RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    apt-get update -y && apt-get install -y --no-install-recommends git
# install the dev environment
RUN --mount=type=cache,target=/root/.cache \
    pip install '.[dev]'
RUN --mount=type=cache,target=/root/.cache \
    tox
# configure tox as default command when the test-stage is executed
CMD ["tox"]
#
# production stage
#
FROM debian:12.11-slim
# arg for marking dev images
ARG GIT_TAG
ENV GIT_TAG=$GIT_TAG
ENV PUID=33
ENV PGID=33
# environment variables (I'm not sure if anyone ever would modify this)
ENV OTTERWIKI_SETTINGS=/app-data/settings.cfg
ENV OTTERWIKI_REPOSITORY=/app-data/repository
# install supervisord and python
RUN --mount=target=/var/cache/apt,type=cache,sharing=locked \
    apt-get -y update && \
    apt-get upgrade -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    nginx supervisor git openssh-client \
    python3.11 python3-wheel python3-venv libpython3.11 \
    uwsgi uwsgi-plugin-python3 curl \
    && ln -sf /dev/stdout /var/log/nginx/access.log \
    && ln -sf /dev/stderr /var/log/nginx/error.log \
    && rm -rf /var/lib/apt/lists/*
# copy virtual environment
COPY --from=compile-stage /opt/venv /opt/venv
# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"
# create directories
RUN mkdir -p /app-data /app/otterwiki
VOLUME /app-data
RUN chown -R www-data:www-data /app-data
# copy static files for nginx
COPY otterwiki/static /app/otterwiki/static
# copy supervisord configs (nginx is configured in the entrypoint.sh)
COPY docker/uwsgi.ini /app/uwsgi.ini
COPY docker/supervisord.conf /etc/supervisor/conf.d/
COPY --chmod=0755 docker/stop-supervisor.sh /etc/supervisor/
# Copy the entrypoint that will generate Nginx additional configs
COPY --chmod=0755 ./docker/entrypoint.sh /entrypoint.sh
# configure a healthcheck
HEALTHCHECK --interval=5m --timeout=3s --retries=3  --start-period=30s --start-interval=5s \
    CMD curl -A "docker-healthcheck" -f http://localhost:8080/-/healthz || exit 1
# configure the entrypoint
ENTRYPOINT ["/entrypoint.sh"]
# and the default command: supervisor which takes care of nginx and uWSGI
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]

# vim:set et ts=8 sts=4 sw=4 ai fenc=utf-8:
