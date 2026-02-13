# Создание самоподписанного сертификата для WebRTC
Для создания сертификатов нужно выполнить команду:
- создать свой корневой сертификат ca.crt, ca.key
- создать сертификат запрос для домена server.csr, server.key
- подписать сертификат домена и получть сертификат домена server.crt
- установить ca.crt как доверенный центр сертификации

```
# Для ca
openssl genrsa -out ca.key 4096
openssl req -new -x509 -days 365 -key ca.key -out ca.crt -subj "/CN=Root CA KS42.RU/L=Novosibirsk/C=RU"

# Для домена
openssl genrsa -out server.key 4096
openssl req -new -key server.key -out server.csr -subj "/CN=90.156.206.67/C=RU/ST=Novosibirsk region/L=Novosibirsk"
openssl x509 -req -days 365  -CA ca.crt -CAkey ca.key -in server.csr -out server.crt
```

```
openssl req -x509 -nodes -newkey rsa:2048 -days 3650 -keyout self-signed.key -out self-signed.crt -subj "/C=RU/ST=Novosibirsk region/L=Novosibirsk/O=ShiftEight/CN=90.156.206.67"
```