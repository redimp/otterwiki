#! /usr/bin/env bash
set -e -x

# take care of repository dictionary
if [ ! -d ${OTTERWIKI_REPOSITORY} ]; then
	mkdir -p ${OTTERWIKI_REPOSITORY}
fi

if [ ! -d ${OTTERWIKI_REPOSITORY}/.git ]; then
	git init ${OTTERWIKI_REPOSITORY}
fi

# take care of the otterwiki settings file
if [ ! -f ${OTTERWIKI_SETTINGS} ]; then
	# copy settings.cfg skeleton
	sed -e "s#^DEBUG.*#DEBUG = False#" \
		-e "s#^REPOSITORY.*#REPOSITORY = '/app-data/repository'#" \
		-e "s#^SITE_NAME.*#SITE_NAME = 'Otter Wiki'#" \
		-e "s#^SQLALCHEMY_DATABASE_URI.*#SQLALCHEMY_DATABASE_URI = 'sqlite:////app-data/db.sqlite'#" \
	< /app/settings.cfg.skeleton > ${OTTERWIKI_SETTINGS}
	#RUN sed -e "s#^LOG_DIR.*#LOG_DIR = '/app-data/log'#" -i $OTTERWIKI_SETTINGS
fi

chown -R www-data:www-data /app-data

# Get the maximum upload file size for Nginx, default to 0: unlimited
USE_NGINX_MAX_UPLOAD=${NGINX_MAX_UPLOAD:-0}
# Generate Nginx config for maximum upload file size
echo "client_max_body_size $USE_NGINX_MAX_UPLOAD;" > /etc/nginx/conf.d/upload.conf

# Get the number of workers for Nginx, default to 1
USE_NGINX_WORKER_PROCESSES=${NGINX_WORKER_PROCESSES:-1}
# Modify the number of worker processes in Nginx config
sed -i "/worker_processes\s/c\worker_processes ${USE_NGINX_WORKER_PROCESSES};" /etc/nginx/nginx.conf

# Get the URL for static files from the environment variable
USE_STATIC_URL=${STATIC_URL:-'/static'}
# Get the absolute path of the static files from the environment variable
USE_STATIC_PATH=${STATIC_PATH:-'/app/static'}
# Get the listen port for Nginx, default to 80
USE_LISTEN_PORT=${LISTEN_PORT:-80}

# Generate Nginx config first part using the environment variables
echo "server {
    listen ${USE_LISTEN_PORT};
    location / {
        try_files \$uri @app;
    }
    location @app {
        include uwsgi_params;
        uwsgi_pass unix:///tmp/uwsgi.sock;
    }
    location $USE_STATIC_URL {
        alias $USE_STATIC_PATH;
    }" > /etc/nginx/conf.d/nginx.conf

# If STATIC_INDEX is 1, serve / with /static/index.html directly (or the static URL configured)
if [[ $STATIC_INDEX == 1 ]] ; then 
echo "    location = / {
        index $USE_STATIC_URL/index.html;
    }" >> /etc/nginx/conf.d/nginx.conf
fi

echo "    set_real_ip_from 172.21.0.1;
    real_ip_header X-Real-IP;
    real_ip_recursive on;" >> /etc/nginx/conf.d/nginx.conf

# Finish the Nginx config file
echo "}" >> /etc/nginx/conf.d/nginx.conf

# wsgi.file_wrapper is an optimization of the WSGI standard. In some
# corner case it can raise an error. For example when returning an
# in-memory bytes buffer (io.Bytesio) in Python 3.5.
# see https://uwsgi-docs.readthedocs.io/en/latest/ThingsToKnow.html
if ! grep -q "^command=/usr/local/bin/uwsgi.*--wsgi-disable-file-wrapper" /etc/supervisor/conf.d/supervisord.conf; then
	sed -i '/^command=\/usr\/local\/bin\/uwsgi/ s/$/ --wsgi-disable-file-wrapper/' /etc/supervisor/conf.d/supervisord.conf
fi

# enable threads, which are disabled by default
# see https://uwsgi-docs.readthedocs.io/en/latest/WSGIquickstart.html#a-note-on-python-threads
if ! grep -q "^command=/usr/local/bin/uwsgi.*--enable-threads" /etc/supervisor/conf.d/supervisord.conf; then
       sed -i '/^command=\/usr\/local\/bin\/uwsgi/ s/$/ --enable-threads/' /etc/supervisor/conf.d/supervisord.conf
fi

# tell nginx not to start an instance on its own
if ! grep -q "^command=/usr/sbin/nginx.*-g 'daemon off;'" /etc/supervisor/conf.d/supervisord.conf; then
	sed -i "/^command=\/usr\/sbin\/nginx/ s/$/ -g 'daemon off;'/" /etc/supervisor/conf.d/supervisord.conf
fi

# and ake care that this is not duplicate in the /etc/nginx/nginx.conf
if grep -q "^daemon off;" /etc/nginx/nginx.conf; then
	sed -i "s/^daemon off;/# daemon off;/" /etc/nginx/nginx.conf
fi

exec "$@"
