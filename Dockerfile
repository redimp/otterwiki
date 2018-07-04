FROM tiangolo/uwsgi-nginx:python3.5

# By default, allow unlimited file sizes, modify it to limit the file sizes
# To have a maximum of 1 MB (Nginx's default) change the line to:
# ENV NGINX_MAX_UPLOAD 1m
ENV NGINX_MAX_UPLOAD 0

# By default, Nginx listens on port 80.
# To modify this, change LISTEN_PORT environment variable.
# (in a Dockerfile or with an option for `docker run`)
ENV LISTEN_PORT 80

# Which uWSGI .ini file should be used, to make it customizable
ENV UWSGI_INI /app/uwsgi.ini

# URL under which static (not modified by Python) files will be requested
# They will be served by Nginx directly, without being handled by uWSGI

ENV STATIC_URL /static
# Absolute path in where the static files wil be
ENV STATIC_PATH /app/static

# Add otterwiki app
COPY ./otterwiki /app
WORKDIR /app

# # upgrade pip
# RUN pip install --upgrade pip

# install packages
ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

# RUN apt-get update
# RUN apt-get install -y git

# Make /app/* available to be imported by Python globally to
# better support several use cases like Alembic migrations.
ENV PYTHONPATH=/app

ENV OTTERWIKI_SETTINGS=/app-data/settings.cfg
ENV OTTERWIKI_REPOSITORY=/app-data/repository

# add and install otterwiki
ADD . /app

RUN mkdir -p /app-data
RUN chown -R www-data:www-data /app-data

VOLUME /app-data
WORKDIR /app-data

# Copy the entrypoint that will generate Nginx additional configs
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

# Start Supervisor, with Nginx and uWSGI
CMD ["/usr/bin/supervisord"]
