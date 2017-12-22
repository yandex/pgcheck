FROM ubuntu:xenial
MAINTAINER Vladimir Borodin <root@simply.name>

ARG pg_version=10

ENV DEBIAN_FRONTEND noninteractive
ENV PG_VERSION ${pg_version}

COPY trusted_keys /tmp/trusted_keys

RUN apt-key add /tmp/trusted_keys/pgdg.gpg \
    && rm -rf /tmp/trusted_keys \
    && echo "deb http://apt.postgresql.org/pub/repos/apt/ xenial-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update -qq \
    && apt-get install -y \
        postgresql-${pg_version} \
        postgresql-contrib-${pg_version} \
        pgbouncer \
        sudo \
    && echo "postgres ALL=(ALL) NOPASSWD: ALL" >>/etc/sudoers

COPY entrypoint.sh /entrypoint.sh
COPY pg.conf /etc/postgresql/${pg_version}/main/
COPY pg_hba.conf /etc/postgresql/${pg_version}/main/
COPY pgbouncer.ini /etc/pgbouncer/pgbouncer.ini
COPY userlist.txt /etc/pgbouncer/userlist.txt
COPY fake.sql /tmp/fake.sql
RUN echo "include 'pg.conf'" >> /etc/postgresql/${pg_version}/main/postgresql.conf

EXPOSE 5432 6432

USER postgres

CMD ["master"]
ENTRYPOINT ["/entrypoint.sh"]
