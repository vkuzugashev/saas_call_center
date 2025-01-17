FROM andrius/asterisk:alpine-latest-18.15.1

LABEL maintainer="KS42 team"

EXPOSE 5060/udp 5060/tcp
EXPOSE 5038

VOLUME /var/lib/asterisk/sounds /var/lib/asterisk/keys /var/lib/asterisk/phoneprov /var/spool/asterisk /var/log/asterisk

ADD manager.conf /etc/asterisk/manager.conf
ADD modules.conf /etc/asterisk/modules.conf
ADD extensions.conf /etc/asterisk/extensions.conf
ADD sip.conf /etc/asterisk/sip.conf

ENTRYPOINT ["/docker-entrypoint.sh"]