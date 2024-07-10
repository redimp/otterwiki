#!/bin/sh
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

# install plugins found in /app-data/plugins and /plugins
for PLUGIN in /app-data/plugins/*/ /plugins/*/; do
    test -d "$PLUGIN" || continue
    echo Installing: $PLUGIN
    cd "$PLUGIN"
    pip install -U . || echo "Error: Installation of plugin in $PLUGIN failed." >&2
done

exec "$@"
