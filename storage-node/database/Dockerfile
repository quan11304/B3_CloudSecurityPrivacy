FROM mysql:8.0

ENV MYSQL_ROOT_PASSWORD=root
ENV MYSQL_DATABASE=musicdb

COPY init.sql /init.sql
COPY entrypoint.sh /docker-entrypoint-initdb.d/entrypoint.sh


EXPOSE 3306
