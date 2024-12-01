FROM almalinux:9

COPY *.ldif /

RUN dnf install -y epel-release procps \
 && dnf install -y openldap-clients openldap-servers \
 && slapd -u ldap -h ldapi:/// \
 && ldapadd -Y EXTERNAL -H ldapi:/// -f /etc/openldap/schema/cosine.ldif \
 && ldapadd -Y EXTERNAL -H ldapi:/// -f /etc/openldap/schema/inetorgperson.ldif \
 && ldapadd -Y EXTERNAL -H ldapi:/// -f /etc/openldap/schema/nis.ldif \
 && ldapmodify -Y EXTERNAL -H ldapi:/// -f /config.ldif \
 && ldapadd -H ldapi:/// -D "cn=Manager,dc=ldap,dc=local" -w secret -f /directory.ldif \
 && pkill -INT slapd \
 && dnf clean all && rm -rf /var/cache/yum

EXPOSE 389/tcp

ENTRYPOINT /sbin/slapd -u ldap -h "ldap:/// ldapi:///" -d 1
