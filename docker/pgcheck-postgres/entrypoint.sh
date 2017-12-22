#!/bin/bash
if [ "$1" = 'bash' ]
then
    /bin/bash
elif [ "$1" = 'master' ]
then
    pgbouncer -d /etc/pgbouncer/pgbouncer.ini
    sudo pg_ctlcluster 10 main start
    while ! psql -c "select 1" > /dev/null
    do
        echo "PostgreSQL has not started yet. Sleeping for a second."
        sleep 1
    done
    psql -c "CREATE DATABASE db1"
    psql db1 -f /tmp/fake.sql
    # Loop is needed for generating some write activity for fake repl_mon
    while true; do
        psql db1 -c "INSERT INTO tmp_table VALUES (current_timestamp)" >/dev/null
        sleep 3
    done
elif [ "$1" = 'replica' ]
then
    while ! psql -h $2 -c "select 1" > /dev/null
    do
        echo "Master has not started yet. Sleeping for a second."
        sleep 1
    done;
    pgbouncer -d /etc/pgbouncer/pgbouncer.ini
    rm -rf /var/lib/postgresql/${PG_VERSION}/main/
    /usr/lib/postgresql/${PG_VERSION}/bin/pg_basebackup \
        -D /var/lib/postgresql/${PG_VERSION}/main/ \
        --write-recovery-conf \
        --wal-method=fetch \
        -h $2
    /usr/lib/postgresql/${PG_VERSION}/bin/postgres \
        -D /var/lib/postgresql/${PG_VERSION}/main/ \
        -c config_file=/etc/postgresql/${PG_VERSION}/main/postgresql.conf
else
    eval "$@"
fi
