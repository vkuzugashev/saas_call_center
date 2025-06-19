FROM mariadb:lts

# Открытие порта
EXPOSE 3306

# Скрипт для автоматического создания базы данных
ADD init.sql /docker-entrypoint-initdb.d/init.sql
RUN chmod -R 775 /docker-entrypoint-initdb.d

# Запуск MariaDB
CMD ["mariadbd"]
