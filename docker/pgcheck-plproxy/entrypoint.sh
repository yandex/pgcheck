#!/bin/bash
if [ "$1" = 'bash' ]
then
    /bin/bash
elif [ "$1" = 'master' ]
then
    sudo cp /tmp/samples/etc/pgcheck.yml /etc/pgcheck.yml
    sudo cp /tmp/samples/etc/pgcheck-hosts.json /etc/pgcheck-hosts.json
    sudo mkdir -p /var/log/pgcheck /var/run/pgcheck
    sudo chown postgres /var/log/pgcheck /var/run/pgcheck

    pgbouncer -d /etc/pgbouncer/pgbouncer.ini
    sudo pg_ctlcluster 10 main start
    while ! psql -c "select 1" > /dev/null
    do
        echo "PostgreSQL has not started yet. Sleeping for a second."
        sleep 1
    done

    psql -c "CREATE DATABASE db1"
    psql db1 -f /tmp/samples/sql/00_pgproxy.sql
    psql db1 -f /tmp/samples/sql/30_get_cluster_partitions.sql
    psql db1 -f /tmp/samples/sql/30_get_cluster_version.sql
    psql db1 -f /tmp/samples/sql/30_inc_cluster_version.sql
    psql db1 -f /tmp/samples/sql/50_is_master.sql
    psql db1 -f /tmp/samples/sql/50_select_part.sql
    psql db1 -f /tmp/samples/sql/99_data.sql

    /tmp/pgcheck
else
    eval "$@"
fi
