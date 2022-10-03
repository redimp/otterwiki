#
# compile image
#
FROM nginx:1.23.1 AS compile-image

LABEL maintainer="Ralph Thesen <mail@redimp.de>"

# install python environment
RUN \
    apt-get -y update && apt-get install -y python3.9 python3.9-venv python3-pip \
    libjpeg-dev zlib1g-dev

# install supervisord
RUN apt-get install -y supervisor

# prepare environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install -U pip && pip install "uWSGI==2.0.20"

RUN mkdir -p /app/otterwiki
COPY setup.py /app
COPY otterwiki /app/otterwiki
WORKDIR /app
RUN find /app
RUN pip install .

#
# package image
#
FROM nginx:1.23.1
# environment variables (I'm not sure if anyone ever would modify this)
ENV OTTERWIKI_SETTINGS=/app-data/settings.cfg
ENV OTTERWIKI_REPOSITORY=/app-data/repository
# install supervisord and python
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get -y update && \
  apt-get install -y --no-install-recommends \
  supervisor git \
  python3.9 python3.9-venv libpython3.9 \
  && rm -rf /var/lib/apt/lists/*
# copy virtual environment
COPY --from=compile-image /opt/venv /opt/venv
# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"
# create directories
RUN mkdir -p /app-data /app/otterwiki
VOLUME /app-data
RUN chown -R www-data:www-data /app-data
WORKDIR /app
# copy supervisord configs (nginx is configured in the entrypoint.sh)
COPY docker/uwsgi.ini /app/uwsgi.ini
COPY docker/supervisord.conf /etc/supervisor/conf.d/
COPY --chmod=0755 docker/stop-supervisor.sh /etc/supervisor/
# otterwiki app
COPY setup.py /app/
COPY otterwiki /app/otterwiki
# Copy the entrypoint that will generate Nginx additional configs
COPY --chmod=0755 ./docker/entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

# Start Supervisor, with Nginx and uWSGI
CMD ["/usr/bin/supervisord"]

# vim:set et ts=8 sts=2 sw=2 ai fenc=utf-8:
