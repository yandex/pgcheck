#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time

import database
import moby

LOG = logging.getLogger('helpers')


def retry_on_assert(function):
    """
    Decorator for retrying. It catches AssertionError
    while timeout not exceeded.
    """

    def wrapper(*args, **kwargs):
        timeout = kwargs['timeout']
        max_time = time.time() + timeout
        while True:
            try:
                return function(*args, **kwargs)
            except AssertionError as error:
                LOG.info('%s call asserted: %s', function.__name__, error)
                # raise exception if timeout exceeded
                if time.time() > max_time:
                    raise
                time.sleep(1)

    return wrapper


def assert_results_are_equal(expected_table, result):
    expected_rows_num = len(expected_table.rows)
    actual_rows_num = len(result.records)
    assert expected_rows_num == actual_rows_num, \
        "Expected {} rows, got {}".format(expected_rows_num,
                                          actual_rows_num)

    if expected_rows_num > 0:
        expected_headings = expected_table.headings
        actual_headings = list(result.records[0].keys())
        LOG.info(expected_headings)
        assert expected_headings == actual_headings, \
            "Tables structure mismatch, expected: {}".format(expected_headings)

    for i in range(0, expected_rows_num):
        expected = {}
        for j in range(0, len(expected_headings)):
            expected[expected_headings[j]] = expected_table.rows[i][j]

        actual = result.records[i]
        assert expected == actual, "Incorrect result in line " \
            "{}, expected {}, got {}".format(i, expected, actual)


def container_action(container, action):
    if action == 'start':
        container.start()
    elif action == 'stop':
        container.stop()
    elif action == 'pause':
        container.pause()
    elif action == 'unpause':
        container.unpause()
    else:
        raise RuntimeError('Unsupported action')


def container_sql(container, statement):
    port = moby.get_container_tcp_port(
        moby.get_container_by_name(container), 6432)
    conn_string = "host=localhost port={port} dbname=db1 user=postgres " + \
                  "connect_timeout=1"
    conn_string = conn_string.format(host=container, port=port)

    conn = database.Connection(conn_string)
    res = conn.get(statement)
    if res.errcode:
        log.info(res)
        raise RuntimeError('Could not execute statement')