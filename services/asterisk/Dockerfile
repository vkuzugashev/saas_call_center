FROM andrius/asterisk:18.11.2-alpine
LABEL maintainer="KS42 team"
EXPOSE 5060/udp 
EXPOSE 5038 
EXPOSE 10000-10100/udp
#VOLUME /var/lib/asterisk/sounds /var/lib/asterisk/keys /var/lib/asterisk/phoneprov /var/spool/asterisk /var/log/asterisk
VOLUME /var/lib/asterisk/sounds /var/log/asterisk /var/spool/asterisk/monitor
ADD conf/globals.conf /etc/asterisk/globals.conf
ADD conf/manager.conf /etc/asterisk/manager.conf
ADD conf/modules.conf /etc/asterisk/modules.conf
ADD conf/rtp.conf /etc/asterisk/rtp.conf
ADD conf/extensions.conf /etc/asterisk/extensions.conf
ADD conf/pjsip.conf /etc/asterisk/pjsip.conf
ADD conf/users.conf /etc/asterisk/users.conf
ADD conf/users_template.conf /etc/asterisk/users_template.conf
ADD conf/users_extensions.conf /etc/asterisk/users_extensions.conf
ADD conf/queues.conf etc/asterisk/queues.conf
ADD conf/queue_operators.conf etc/asterisk/queue_operators.conf
ADD conf/members_operators.conf etc/asterisk/members_operators.conf
ADD conf/http.conf /etc/asterisk/http.conf
RUN apk add sox
RUN apk add --update tcpdump && rm -rf /var/cache/apk/*
WORKDIR /var/lib/asterisk/static-http
RUN ln -s /var/spool/asterisk/monitor/ monitor
ENTRYPOINT ["/docker-entrypoint.sh"]