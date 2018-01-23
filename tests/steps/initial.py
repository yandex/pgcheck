#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time

import database
import moby
import helpers

log = logging.getLogger(__name__)

TIMEOUT = 10
ITERATIONS = 6
PLPROXY_CONN_STRING = "host=localhost port={port} dbname=db1 " + \
                      "user=postgres connect_timeout=1"


@given(u'a deployed cluster')
def given_deployed_cluster(context):
    # Since everything is started with compose here we should check
    # that everything has been deployed to PL/Proxy host
    for i in range(0, ITERATIONS):
        try:
            conn = database.Connection(
                PLPROXY_CONN_STRING.format(port=context.plproxy_port))
            res = conn.get('SELECT * FROM plproxy.priorities')
            log.info(res)
            if res.errcode is None and len(res.records) != 0:
                return
            time.sleep(TIMEOUT)
        except Exception as err:
            log.info(err)
            time.sleep(TIMEOUT)


@then(u'connection strings for "{cluster}" cluster are')
def then_connection_strings_are(context, cluster):
    conn = database.Connection(
        PLPROXY_CONN_STRING.format(port=context.plproxy_port))
    res = conn.get_func(
        'plproxy.get_cluster_partitions', i_cluster_name=cluster)
    log.info(context.table.rows)
    helpers.assert_results_are_equal(context.table, res)


@then(u'within {timeout:d} seconds connection strings for "{cluster}" cluster changes to')
@helpers.retry_on_assert
def then_connection_strings_become(context, timeout, cluster):
    then_connection_strings_are(context, cluster)


@when(u'we {action} "{container_name}" container')
def when_action_container(context, action, container_name):
    container = context.containers[container_name]
    helpers.container_action(container, action)


@when(u'we {action} replay on "{container_name}"')
def when_action_replay(context, action, container_name):
    container = context.containers[container_name]
    conn_string = helpers.container_conn_string(container_name)
    statement = 'SELECT pg_wal_replay_{action}()'.format(action=action)

    conn = database.Connection(conn_string)
    res = conn.get(statement)
    if res.errcode:
        log.info(res)
        raise RuntimeError('Could not execute statement')


@when(u'we {action} a lot of connections to "{container_name}"')
def when_action_connections(context, action, container_name):

    def execute_pg_sleep(conn_string):
        db = database.Connection(conn_string)
        res = db.get('SELECT now(), pg_sleep(60)')
        log.info(res)

    conn_string = helpers.container_conn_string(container_name, port=5432)

    if action == 'open':
        helpers.run_threads(50, execute_pg_sleep, conn_string=conn_string)
    elif action == 'close':
        db = database.Connection(conn_string)
        res = db.get("""SELECT pg_terminate_backend(pid) FROM pg_stat_activity
                        WHERE query ~ 'pg_sleep' AND pid != pg_backend_pid()""")
        log.info(res)