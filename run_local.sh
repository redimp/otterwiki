#!/bin/bash

# Make sure content dirs exists
APP_DATA='app-data'
mkdir -p $APP_DATA

# Content stored in git; initialise the repo if required
export REPOSITORY="${PWD}/${APP_DATA}/repository"
[[ ! -d ${REPOSITORY}/.git ]] && git init $REPOSITORY

export SQLALCHEMY_DATABASE_URI="sqlite:///${PWD}/${APP_DATA}/db.sqlite" 
export SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex())') 

# Start the server
waitress-serve --host 127.0.0.1 otterwiki.server:app
