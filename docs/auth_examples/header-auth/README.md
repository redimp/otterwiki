# Example for testing `AUTH_METHOD=PROXY_HEADER`

This is a minimal example for testing the `PROXY_HEADER` auth method.
Here a Caddy sets the headers as if they were configured by an auth
service.

Usage:

    make run

Testing:

- On <http://localhost:8080> the otterwiki is listening, no header is
set. The access results in a 403 Forbidden
- On <http://localhost:8081> a caddy server is listening, which does a
reverse proxy into the otterwiki service with additional headers
providing information about the user.

