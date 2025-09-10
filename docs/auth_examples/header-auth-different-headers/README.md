# Example for testing `AUTH_METHOD=PROXY_HEADER`

This is a second example for testing the `PROXY_HEADER` auth method,
it shows how to use non-default header names.
This may be useful when you use a proxy that doesn't allow you to rename the security headers.

Here a Caddy sets the headers as if they were configured by an auth
service, using their well-known names.

Usage:

    make run

Testing:

- On <http://localhost:8080> the otterwiki is listening, no header is
set. The access results in a 403 Forbidden
- On <http://localhost:8081> a caddy server is listening, which does a
reverse proxy into the otterwiki service with additional headers
providing information about the user.

## Requirements
1. each header's name can be set independently
2. headers with user and email are required
3. permissions header is optional
