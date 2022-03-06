FROM tiangolo/uwsgi-nginx:python3.8

# By default, allow unlimited file sizes, modify it to limit the file sizes
# To have a maximum of 1 MB (Nginx's default) change the line to:
# ENV NGINX_MAX_UPLOAD 1m
ENV NGINX_MAX_UPLOAD 0

# By default, Nginx listens on port 80.
# To modify this, change LISTEN_PORT environment variable.
# (in a Dockerfile or with an option for `docker run`)
ENV LISTEN_PORT 80

# Which uWSGI .ini file should be used, to make it customizable
ENV UWSGI_INI /app/otterwiki-uwsgi.ini

# URL under which static (not modified by Python) files will be requested
# They will be served by Nginx directly, without being handled by uWSGI
ENV STATIC_URL /static
# Absolute path in where the static files wilk be
ENV STATIC_PATH /app/otterwiki/static

# Absolute paths to otterwiki settings and repository
ENV OTTERWIKI_SETTINGS=/app-data/settings.cfg
ENV OTTERWIKI_REPOSITORY=/app-data/repository

# create directories
RUN mkdir -p /app-data /app/otterwiki

# Add otterwiki app
ADD setup.py settings.cfg.skeleton /app/
ADD ./otterwiki /app/otterwiki
WORKDIR /app

# install packages
RUN pip install --disable-pip-version-check --use-feature=in-tree-build .

VOLUME /app-data

# Copy the entrypoint that will generate Nginx additional configs
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]

# Start Supervisor, with Nginx and uWSGI
CMD ["/usr/bin/supervisord"]

# vim:set et ts=8 sts=2 sw=2 ai fenc=utf-8:
