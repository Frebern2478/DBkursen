FROM mysql:latest


COPY ./table-creation.sql /docker-entrypoint-initdb.d
COPY ./products.sql /docker-entrypoint-initdb.d