#FROM andrius/asterisk:alpine-13.3.2
FROM andrius/asterisk:18.11.2-alpine

LABEL maintainer="KS42 team"

EXPOSE 5060/udp 
EXPOSE 5038 
EXPOSE 10000-10001/udp

#VOLUME /var/lib/asterisk/sounds /var/lib/asterisk/keys /var/lib/asterisk/phoneprov /var/spool/asterisk /var/log/asterisk
VOLUME /var/lib/asterisk/keys /var/lib/asterisk/phoneprov /var/spool/asterisk /var/log/asterisk

ADD ru /var/lib/asterisk/sounds/ru
ADD manager.conf /etc/asterisk/manager.conf
ADD modules.conf /etc/asterisk/modules.conf
ADD rtp.conf /etc/asterisk/rtp.conf
ADD extensions.conf /etc/asterisk/extensions.conf
#ADD sip.conf /etc/asterisk/sip.conf
ADD pjsip.conf /etc/asterisk/pjsip.conf

 
RUN apk add --update tcpdump && rm -rf /var/cache/apk/*
RUN apk add busybox-extras

#ENV EXTERNADDR=192.168.1.107
#ENV LOCALNET=192.168.0.0/255.255.0.0

ENTRYPOINT ["/docker-entrypoint.sh"]