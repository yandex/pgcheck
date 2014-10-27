# encoding: utf-8
#
#    Copyright (c) 2014 Yandex <https://github.com/yandex>
#    Copyright (c) 2014 Other contributors as noted in the AUTHORS file.
#
#    This is free software; you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    This software is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#


import os
import os.path
import socket
import json
import logging
import time

import requests


class ObserverConfigError(Exception):
    pass


class ObserverError(Exception):
    pass


class AbstractDCObserver:
    def get_host_dc(self, host):
        return NotImplemented

    def get_my_dc(self):
        return NotImplemented


class RESTfulDCObserver(AbstractDCObserver):
    # Get DC from http api

    def __init__(self, url, cache_dir=None, retry=5, retry_pause=5, timeout=5, myhostname=None):
        self.myhostname = myhostname or socket.gethostname()
        self.cache_dir = cache_dir
        if cache_dir:
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir)
        self.url = url
        self.retry = int(retry)
        self.retry_pause = float(retry_pause)
        self.timeout = float(timeout)

    def _cache_get(self, host):
        if self.cache_dir:
            fn = os.path.join(self.cache_dir, host)
            if os.path.exists(fn):
                return open(fn, 'r').read().rstrip()

    def _cache_put(self, host, value):
        if self.cache_dir:
            fn = os.path.join(self.cache_dir, host)
            open(fn, 'w').write('%s\n' % value)

    def _real_get_host_dc(self, hostname):
        dc = None
        url = self.url % {'hostname': hostname}
        for i in xrange(self.retry):
            resp = requests.get(url)
            if resp.status_code == 200:
                dc = resp.content.rstrip().upper()
                break
            logging.warning("Could not get info about DC of %s from %s. Will retry in %s sec",
                            hostname, url, self.retry_pause)
            time.sleep(self.retry_pause)
        return dc

    def get_host_dc(self, host):
        r = self._cache_get(host)
        if r is None:
            r = self._real_get_host_dc(host)
            if r is None:
                raise ObserverError('Can not observe DC for %s', host)
            else:
                self._cache_put(host, r)
        logging.debug('get_host_dc(%s)=%s', host, r)
        return r

    def get_my_dc(self):
        try:
            return self.get_host_dc(self.myhostname)
        except ObserverError:
            r = self._cache_get('my_dc')
            if r is None:
                raise


class HardcodedDCObserver(AbstractDCObserver):
    # Load hostnames from file

    def __init__(self, filename, myhostname=None):
        self.filename = filename
        if filename.endswith('json'):
            self.data = json.loads(open(filename, 'r').read())
        # TODO: add more formats (csv, yaml, ...)
        else:
            raise ObserverConfigError('Only json files supported yet')
        self.myhostname = myhostname or socket.gethostname()

    def get_host_dc(self, host):
        if host in self.data:
            return self.data[host]
        else:
            raise ObserverError('Can not observe DC for %s', host)

    def get_my_dc(self):
        try:
            return self.get_host_dc(self.myhostname)
        except ObserverError:
            return self.get_host_dc('my_dc')
