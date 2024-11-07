#!/bin/sh
#
set -e

. ../.env.prod.nginx

CWD=$(pwd)

cd $OTTERWIKI_CONTEXT

# This requires that port redirection is done on the host from port 80 to port 8080
podman run -it --rm --name certbot -p 8080:80 -v "${OTTERWIKI_VOLUME}:/etc/letsencrypt:rw,Z" certbot/certbot:latest certonly --standalone --non-interactive --agree-tos --email $OTTERWIKI_CERTBOT_EMAIL -d $OTTERWIKI_DOMAIN

podman-compose restart nginx 2>/dev/null || echo "nginx container not running, not restarting it"

cd $CWD
