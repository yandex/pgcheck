#!/usr/bin/env python
# -*- coding: utf-8 -*-

import docker

DOCKER = docker.from_env()

def get_container_by_name(name):
    for container in DOCKER.containers.list():
        if container.attrs['Config']['Hostname'] == name:
            return container


def get_container_tcp_port(container, port):
    binding = container.attrs['NetworkSettings']['Ports'].get(
        '{port}/tcp'.format(port=port))
    if binding:
        return binding[0]['HostPort']