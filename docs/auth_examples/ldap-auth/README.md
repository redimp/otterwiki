# Proof of concept: Otterwiki with ldap-auth

Here an example of using ldap authentication in An Otter Wiki can be tested.

After running `docker compose build && docker compose up` or `podman compose
build && podman compose up` open up <http://localhost:8080> and log in with
one of these username/password combinations:

- john@ldap.org / 12345678
- fulano@ldap.org / password
- max@ldap.org / qwertyui

Notes:
- `john@ldap.org` is an admin account.
- `max@ldap.org` is created on login.
