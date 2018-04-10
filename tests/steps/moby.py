#!/usr/bin/env python
# -*- coding: utf-8 -*-

import docker

DOCKER = docker.from_env()

def get_container_by_name(name):
    """
    Returns container object
    """
    for container in DOCKER.containers.list():
        if container.attrs['Config']['Hostname'] == name:
            return container


def get_container_tcp_port(container, port):
    """
    Returns exposed to host container port
    """
    binding = container.attrs['NetworkSettings']['Ports'].get(
        '{port}/tcp'.format(port=port))
    if binding:
        return binding[0]['HostPort']


def container_action(container, action):
    """
    Performs desired action with container
    """
    if action == 'pause':
        container.pause()
    elif action == 'unpause':
        container.unpause()
    else:
        raise RuntimeError('Unsupported action')


def container_conn_string(container):
    """
    Returns connection string to container
    """
    port = get_container_tcp_port(get_container_by_name(container), 6432)
    conn_string = "host=localhost port={port} dbname=db1 user=postgres " + \
                  "connect_timeout=1"
    return conn_string.format(port=port)