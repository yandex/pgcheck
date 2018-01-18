#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import yaml
import docker

import steps.helpers as helpers


def before_all(context):
    """
    Setup environment
    """
    # Connect to docker daemon
    context.docker = docker.from_env()
    context.plproxy_port = helpers.get_container_tcp_port(
        helpers.get_container_by_name('plproxy'), 6432)


def after_step(context, step):
    debug = True if os.environ.get('DEBUG', 0) != 0 else False
    if debug and step.status == 'failed':
       # -- ENTER DEBUGGER: Zoom in on failure location.
       # NOTE: Use IPython debugger, same for pdb (basic python debugger).
       try:
           import ipdb
       except ImportError:
           import pdb as ipdb
       ipdb.post_mortem(step.exc_traceback)
