#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time

import database
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
