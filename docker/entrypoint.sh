#!/usr/bin/env bash
# vim:set et ts=8 sts=4 sw=4 ai fenc=utf-8:

set -e

# take care of repository dictionary
if [ ! -d ${OTTERWIKI_REPOSITORY} ]; then
    mkdir -p ${OTTERWIKI_REPOSITORY}
fi

if [ ! -d ${OTTERWIKI_REPOSITORY}/.git ]; then
    git init -b main ${OTTERWIKI_REPOSITORY}
fi

# take care of the otterwiki settings file
if [ ! -f ${OTTERWIKI_SETTINGS} ]; then
    RANDOM_SECRET_KEY=$(echo "$(date) ${RANDOM} ${RANDOM} ${RANDOM}" | md5sum | head -c 32)
    echo "DEBUG = False" >> ${OTTERWIKI_SETTINGS}
    echo "REPOSITORY = '/app-data/repository'" >> ${OTTERWIKI_SETTINGS}
    echo "SECRET_KEY = '${RANDOM_SECRET_KEY}'" >> ${OTTERWIKI_SETTINGS}
    echo "SQLALCHEMY_DATABASE_URI = 'sqlite:////app-data/db.sqlite'" >> ${OTTERWIKI_SETTINGS}
fi

chown -R www-data:www-data /app-data

# Get the maximum upload file size for Nginx, default to 0: unlimited
USE_NGINX_MAX_UPLOAD=${NGINX_MAX_UPLOAD:-0}
# Get the number of workers for Nginx, default to 1
USE_NGINX_WORKER_PROCESSES=${NGINX_WORKER_PROCESSES:-1}
# Modify the number of worker processes in Nginx config
sed -i "/worker_processes\s/c\worker_processes ${USE_NGINX_WORKER_PROCESSES};" /etc/nginx/nginx.conf

# Get the URL for static files from the environment variable
USE_STATIC_URL=${STATIC_URL:-'/static'}
# Get the absolute path of the static files from the environment variable
USE_STATIC_PATH=${STATIC_PATH:-'/app/otterwiki/static'}
# Get the listen port for Nginx, default to 80
USE_LISTEN_PORT=${LISTEN_PORT:-80}
if [ "${USE_LISTEN_PORT}" != "8080" ]; then
    LISTEN_EXTRA_PORT="listen 8080;"
fi

# Generate Nginx config first part using the environment variables
echo "server {
    listen ${USE_LISTEN_PORT};
    ${LISTEN_EXTRA_PORT}
    client_max_body_size $USE_NGINX_MAX_UPLOAD;
" > /etc/nginx/sites-enabled/default

if [ ! -z "${REAL_IP_FROM}" ]; then
echo "    set_real_ip_from $REAL_IP_FROM;
    real_ip_header X-Real-IP;
    real_ip_recursive on;" >> /etc/nginx/sites-enabled/default
fi


echo "    location / {
        try_files \$uri @app;
    }
    location @app {
        include uwsgi_params;
        uwsgi_pass unix:///tmp/uwsgi.sock;
    }
    location $USE_STATIC_URL {
        alias $USE_STATIC_PATH;
    }" >> /etc/nginx/sites-enabled/default

# close the server block
echo "}" >> /etc/nginx/sites-enabled/default

# install plugins found in /app-data/plugins and /plugins
for PLUGIN in /app-data/plugins/*/ /plugins/*/; do
    test -d "$PLUGIN" || continue
    echo Installing: $PLUGIN
    cd "$PLUGIN"
    pip install -U . || echo "Error: Installation of plugin in $PLUGIN failed." >&2
done

exec "$@"
