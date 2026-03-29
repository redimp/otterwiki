# Make sure content dirs exists
$AppData = "app-data"
New-Item -ItemType Directory -Force -Path $AppData | Out-Null

# Content stored in git; initialise the repo if required
$env:REPOSITORY = "$PWD\$AppData\repository"
if (-not (Test-Path "$env:REPOSITORY\.git")) {
    git init $env:REPOSITORY
}

$env:SQLALCHEMY_DATABASE_URI = "sqlite:///$PWD/$AppData/db.sqlite"
$env:SECRET_KEY = python3 -c 'import secrets; print(secrets.token_hex())'

# Start the server
waitress-serve --host 127.0.0.1 otterwiki.server:app
