FROM pgcheck-postgres
MAINTAINER Vladimir Borodin <root@simply.name>

ARG pg_version=10

ENV DEBIAN_FRONTEND noninteractive
ENV PG_VERSION ${pg_version}

USER root

RUN apt-get update -qq \
    && apt-get install -y \
        postgresql-${pg_version}-plproxy \
        python-pip \
    && pip install -U setuptools

COPY entrypoint.sh /entrypoint.sh

EXPOSE 6432

USER postgres

CMD ["master"]
ENTRYPOINT ["/entrypoint.sh"]
