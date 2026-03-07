# FROM andrius/asterisk:alpine-3.2-18.20.2
FROM andrius/asterisk:22.8-cert1_debian-trixie-amd64
LABEL maintainer="KS42 team"

EXPOSE 5060/udp 
EXPOSE 5038 
EXPOSE 10000-10100/udp
EXPOSE 8088
EXPOSE 8089

#VOLUME /var/lib/asterisk/sounds /var/lib/asterisk/keys /var/lib/asterisk/phoneprov /var/spool/asterisk /var/log/asterisk
VOLUME /var/lib/asterisk/sounds /var/log/asterisk /var/spool/asterisk/monitor

USER root

RUN apt-get update
# RUN apt-get install asterisk-srtp asterisk-opus
RUN apt-get -y install sox
RUN apt-get -y install tcpdump
# RUN apt-get -y install asterisk-odbc 
RUN apt-get -y install unixodbc
RUN apt-get -y install odbc-mariadb

# ADD conf/manager.conf /etc/asterisk/manager.conf
# ADD conf/modules.conf /etc/asterisk/modules.conf
# ADD conf/rtp.conf /etc/asterisk/rtp.conf
ADD conf/extensions.conf /etc/asterisk/extensions.conf
ADD conf/pjsip.conf /etc/asterisk/pjsip.conf
# ADD conf/users.conf /etc/asterisk/users.conf
ADD conf/cdr.conf /etc/asterisk/cdr.conf
# ADD conf/users_template.conf /etc/asterisk/users_template.conf
# ADD conf/users_extensions.conf /etc/asterisk/users_extensions.conf
# ADD conf/queues.conf etc/asterisk/queues.conf
# ADD conf/queue_operators.conf etc/asterisk/queue_operators.conf
# ADD conf/members_operators.conf etc/asterisk/members_operators.conf
# ADD conf/http.conf /etc/asterisk/http.conf
ADD conf/extconfig.conf /etc/asterisk/extconfig.conf
ADD conf/sorcery.conf /etc/asterisk/sorcery.conf
ADD conf/res_odbc.conf /etc/asterisk/res_odbc.conf
ADD etc/odbc.ini /etc/odbc.ini
ADD etc/odbcinst.ini /etc/odbcinst.ini

# Для WebRTC
# ADD certs/server.crt /etc/asterisk/keys/server.crt
# ADD certs/server.key /etc/asterisk/keys/server.key
# RUN chmod 755 -R /etc/asterisk/keys


# WORKDIR /var/lib/asterisk/static-http
# RUN ln -s /var/spool/asterisk/monitor/ monitor

# USER asterisk
# WORKDIR /home/asterisk

# CMD ["/usr/sbin/asterisk", "-vvvdddf", "-T", "-W", "-U", "asterisk", "-p"]