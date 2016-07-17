# encoding: utf-8
#
#    Copyright (c) 2014-2016 Yandex <https://github.com/yandex>
#    Copyright (c) 2014-2016 Other contributors as noted in the AUTHORS file.
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

import time
import logging
import sys
import ConfigParser
from optparse import OptionParser
import multiprocessing

from .database import Database
from . import dc_observer


def loop_for_current_priorities(dbname, config, my_dc, get_host_dc_func):
    db = Database(dbname, config=config, my_dc=my_dc, get_host_dc_func=get_host_dc_func)
    logging.info("Started fast loop for %s", dbname)
    while True:
        logging.debug('Starting new iteration for "%s"', db.local_conn_string)
        try:
            db.check_hosts_for_db()
        except Exception as err:
            logging.error(str(err), exc_info=1)
            pass
        time.sleep(1)


def loop_for_base_priorities(dbname, config, my_dc, get_host_dc_func):
    timeout = int(config.get('global', 'base_prio_timeout')) if config.has_option('global', 'base_prio_timeout') else 60
    db = Database(dbname, config=config, my_dc=my_dc, get_host_dc_func=get_host_dc_func)
    db.set_all_dcs()
    logging.info("Started slow loop for %s" % dbname)
    while True:
        try:
            db.check_base_priorities()
        except Exception as err:
            logging.error(str(err), exc_info=1)
            pass
        time.sleep(timeout)


def load_observer_from_config(config):
    def _load_params(section, prefix):
        # prefix_A = 1  => {'A':1}
        return dict([(k[len(prefix):], v) for (k, v) in config.items(section) if k.startswith(prefix)])

    params = _load_params('global', 'observer_')

    dotted_path = params.pop('class')
    if '.' not in dotted_path:
        dotted_path = '.' + dotted_path

    module_name, cls_name = dotted_path.rsplit('.', 1)

    if module_name:
        import importlib
        module = importlib.import_module(module_name)
    else:
        module = dc_observer

    cls = getattr(module, cls_name)
    return cls(**params)


def do_all_magic(config):
    logging.debug("Entered do_all_magic function")

    o = load_observer_from_config(config)

    try:
        my_dc = o.get_my_dc()
    except dc_observer.ObserverError:
        logging.error("Could not get my DC from anywhere, exit")
        sys.exit(1)

    logging.debug("My DC is %s" % my_dc)

    databases = [section for section in config.sections() if section != 'global']
    get_host_dc_func = o.get_host_dc
    processes = [multiprocessing.Process(target=loop_for_current_priorities, args=(db, config, my_dc, get_host_dc_func))
                 for db in databases]
    processes += [multiprocessing.Process(target=loop_for_base_priorities, args=(db, config, my_dc, get_host_dc_func))
                  for db in databases]

    logging.debug("Starting different processes for next databases: %s", ','.join(databases))
    for process in processes:
        process.daemon = True
        process.start()
    for process in processes:
        process.join()


def parse_cmd_args():
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-c", "--config", dest="config_file", default='/etc/pgcheck.conf')
    parser.add_option("-p", "--pid-file", dest="pid_file", default=None)
    parser.add_option("-l", "--log-file", dest="log_file", default=None)
    parser.add_option("", "--log-level", dest="log_level", default=None)
    parser.add_option("-w", "--working-dir", dest="working_dir", default=None)
    parser.add_option("", "--no-detach", dest="no_detach", action="store_true", default=False)
    return parser.parse_args()


def read_config(filename=None, options=None, defaults=None):
    config = ConfigParser.RawConfigParser()
    if not filename:
        filename = options.config_file

    logging.info('Reading config from %s', filename)
    config.read(filename)

    # Appending default config with default values
    if defaults:
        for (k, v) in defaults.items():
            if not config.has_option('global', k):
                config.set('global', k, v)

    # Rewriting global config with parameters from command line
    if options:
        for (k, v) in vars(options).items():
            if v is not None:
                config.set('global', k, v)

    return config


def init_logging(config):
    level = getattr(logging, config.get('global', 'log_level').upper())
    filename = config.get('global', 'log_file')
    root = logging.getLogger()
    root.setLevel(level)
    _format = logging.Formatter("%(levelname)s\t%(asctime)s\t\t%(message)s")
    _handler = logging.FileHandler(filename)
    _handler.setFormatter(_format)
    _handler.setLevel(level)
    root.handlers = [_handler, ]


def start(config):
    if not config.get('global', 'no_detach'):
        import daemon
        from daemon.pidfile import PIDLockFile

        pid_file = config.get('global', 'pid_file')
        working_dir = config.get('global', 'working_dir')
        logfile = open(config.get('global', 'log_file').replace('.log', '.out'), 'w+')
        logging.info("Starting daemon")
        with daemon.DaemonContext(working_directory=working_dir, stdout=logfile, stderr=logfile,
                                  pidfile=PIDLockFile(pid_file), files_preserve=[logging.root.handlers[-1].stream, ]):
            do_all_magic(config)
    else:
        do_all_magic(config)


def main():

    CONFIG_DEFAULTS = {
        'pid_file': '/tmp/pgcheck.pid',
        'log_file': '/tmp/pgcheck.log',
        'log_level': 'debug',
        'working_dir': '.'
    }

    options, _ = parse_cmd_args()
    config = read_config(filename=options.config_file, options=options, defaults=CONFIG_DEFAULTS)
    init_logging(config)
    start(config)


if __name__ == '__main__':
    main()
