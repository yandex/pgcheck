#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import docker

DOCKER = docker.from_env()
LOG = logging.getLogger('helpers')


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


def get_container_by_name(name):
    for container in DOCKER.containers.list():
        if container.attrs['Config']['Hostname'] == name:
            return container


def get_container_tcp_port(container, port):
    binding = container.attrs['NetworkSettings']['Ports'].get(
        '{port}/tcp'.format(port=port))
    if binding:
        return binding[0]['HostPort']