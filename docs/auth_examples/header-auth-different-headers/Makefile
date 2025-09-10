run:
	docker compose up --remove-orphans

caddy-fmt:
	docker run -v $(PWD)/Caddyfile:/srv/Caddyfile:rw caddy:2 caddy fmt --overwrite Caddyfile
