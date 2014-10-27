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


import ConfigParser
import StringIO
import os.path

from pgcheck.pgcheck import load_observer_from_config


def _cfg(s):
    config = ConfigParser.RawConfigParser()
    config.readfp(StringIO.StringIO(s))
    return config


def test_restfulobserver():
    CONFIG = """[global]
observer_class = RESTfulDCObserver
observer_url = http://apihost.domain.com/api/host_query.sbml?hostname=%(hostname)s&columns=short_dc
observer_retry = 5
observer_retry_pause = 1
observer_timeout = 3"""
    o = load_observer_from_config(_cfg(CONFIG))
    o.get_host_dc('hostforcheck.domain.com')


def test_hardcodedobserver():
    CONFIG = """[global]
observer_class = .HardcodedDCObserver
observer_filename = data-pgcheck-hosts.json
"""
    config = _cfg(CONFIG)
    THIS_DIR = os.path.abspath(os.path.dirname(__file__))
    config.set('global', 'observer_filename', os.path.join(THIS_DIR, config.get('global', 'observer_filename')))
    o = load_observer_from_config(config)
    assert o.get_host_dc('host1') == 'DC1'
