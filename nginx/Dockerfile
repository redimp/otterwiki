FROM nginx:1.25.3
RUN apt-get update && apt-get -y install procps net-tools curl telnet netcat-openbsd less vim
RUN rm -f /etc/nginx/conf.d/default.conf
COPY default-ssl.conf /etc/nginx/templates/default-ssl.conf.template
