# encoding: utf-8
import logging
import sys

import psycopg2

from .timings import timelimit, TimeoutError


class Database:
    def __init__(self, dbname, config, my_dc, get_host_dc_func):
        self.my_dc = my_dc
        self.dbname = dbname
        self.config = config
        self.get_host_dc_func = get_host_dc_func
        self.host_ids = []
        self.hosts = {}
        self.last_priorities = {}
        self.local_conn_string = config.get(dbname, 'local_conn_string')
        self.append_conn_string = config.get(dbname, 'append_conn_string')
        self.quorum = int(config.get(dbname, 'quorum'))
        self.hysterisis = int(config.get(dbname, 'hysterisis'))
        try:
            self.conn_local = psycopg2.connect(self.local_conn_string)
            self.conn_local.autocommit = True

            self.get_all_hosts()
            for host_id in self.host_ids:
                self.last_priorities[host_id] = [self.get_current_priority_of_host(host_id), ]

        except psycopg2.OperationalError:
            logging.error('Could not connect to "%s". Exiting', self.local_conn_string)
            sys.exit(1)

    def get_current_priority_of_host(self, host_id):
        try:
            cur = self.conn_local.cursor()
            cur.execute('select max(priority) from plproxy.priorities where host_id=%d;' % host_id)
            return cur.fetchone()[0]
        except Exception as err:
            logging.error("Could not get current priority of host %d", host_id, exc_info=1)
            return 100

    def get_all_hosts(self):
        try:
            cur = self.conn_local.cursor()
            cur.execute('select distinct(host_id) from plproxy.hosts;')
            for i in cur.fetchall():
                self.host_ids.append(i[0])
        except Exception:
            logging.error("Could not get hosts of the cluster")
            sys.exit(1)

    def set_all_dcs(self):
        logging.debug("Started updating information about DC for hosts of %s", self.dbname)
        try:
            cur = self.conn_local.cursor()
            for host_id in self.host_ids:
                cur.execute("select host_name from plproxy.hosts where host_id=%d;" % host_id)
                dc = self.get_host_dc_func(cur.fetchone()[0])
                if dc:
                    cur.execute("update plproxy.hosts set dc = '%s' where host_id=%d;" % (dc, host_id))
            cur.close()
        except Exception as err:
            logging.error(str(err), exc_info=1)

    def check_hosts_for_db(self):
        cur = self.conn_local.cursor()
        for host_id in self.host_ids:
            cur.execute("""select h.host_id, c.conn_string, p.priority
                from plproxy.priorities p, plproxy.connections c, plproxy.hosts h
                where h.host_id=%d and h.host_id=p.host_id and c.conn_id=p.conn_id;""" % host_id)
            res = cur.fetchone()
            try:
                self.check_host_status(res)
            except TimeoutError as err:
                self.update_host_priority(host_id, 100, "Request timed out")
        cur.close()

    @timelimit(1.5)
    def check_host_status(self, arg):
        host_id, conn_string, priority = arg
        try:
            logging.debug("[%s] Connecting to '%s %s'", self.dbname, conn_string, self.append_conn_string)
            conn = psycopg2.connect('%s %s' % (conn_string, self.append_conn_string))
            conn.autocommit = True
        except psycopg2.OperationalError:
            self.update_host_priority(host_id, 100, "Connection timed out")
            return 0

        try:
            cur = conn.cursor()
            cur.execute("select public.is_master(1000);")
            is_master = cur.fetchone()[0]
        except psycopg2.ProgrammingError:
            self.update_host_priority(host_id, 100, "Could not check health of host [Probably, no function public.is_master(1000);]")
            return 0

        if is_master:
            self.update_host_priority(host_id, 0, "Seems alive")
        elif is_master == 0:
            self.update_host_priority(host_id, 10, "Seems alive")
        else:
            pass
        cur.close()
        conn.close()

    def update_host_priority(self, host_id, priority, comment):
        cur = self.conn_local.cursor()
        cur.execute("select host_name, base_prio, prio_diff from plproxy.hosts where host_id=%d;" % host_id)
        host, base_prio, prio_diff = cur.fetchone()

        if priority != 0 and priority != 100:
            if base_prio is not None and 0 < base_prio < 100:
                priority = base_prio
            if prio_diff is not None:
                priority += prio_diff

        if len(self.last_priorities[host_id]) == self.quorum + self.hysterisis:
            self.last_priorities[host_id].pop(0)
        self.last_priorities[host_id].append(priority)
        current_priority = self.get_current_priority_of_host(host_id)

        if priority == current_priority:
            logging.debug("Priority of host %s has not changed (%d)", host, priority)
            return None
        if self.last_priorities[host_id].count(priority) < self.quorum:
            logging.info("Priority of host %s has not been changed to %d (%s) due to not enough quorum: %s", host,
                         priority, comment, str(self.last_priorities[host_id]))
            return None
        # here we think that quorum has been gathered
        logging.debug("Last priorities for host %s are %s", host, str(self.last_priorities[host_id]))
        cur.execute("update plproxy.priorities set priority=%d where host_id=%d;" % (priority, host_id))
        log_level = 40 if priority > 90 else 20
        logging.log(log_level, 'Priority of host %s has been updated to %d (%s)', host, priority, comment)
        self.conn_local.commit()
        cur.close()

    def check_base_priorities(self):
        self.repl_append_string = self.config.get('global', 'repl_append_string')
        self.hosts = self.get_base_priorities()
        for host_name in self.hosts.keys():
            self.calculate_base_priority(host_name)
        self.update_base_priorities()

    def get_base_priorities(self):
        cur = self.conn_local.cursor()
        cur.execute("""select h.host_id, h.host_name, h.dc, h.base_prio, c.conn_string """
                    """from plproxy.connections c, plproxy.hosts h, plproxy.priorities p """
                    """where h.host_id=p.host_id and c.conn_id=p.conn_id;""")
        hosts = {}
        for res in cur.fetchall():
            hosts[res[1]] = {'host_id': res[0], 'dc': res[2], 'base_prio': res[3], 'conn_string': res[4]}
        logging.debug("get_base_priorities: %s", hosts)
        cur.close()
        return hosts

    def calculate_base_priority(self, host_name):
        try:
            conn = psycopg2.connect('%s %s' % (self.hosts[host_name]['conn_string'], self.repl_append_string))
            conn.autocommit = True
            cur = conn.cursor()
            cur.execute("select public.is_master(1000);")
            is_master = cur.fetchone()[0]
            if is_master:
                self.hosts[host_name]['base_prio'] = 0
                cur.execute(
                    "select client_hostname, sync_state from pg_stat_replication "
                    "where application_name != 'pg_basebackup';")
                replics_info = cur.fetchall()
                logging.debug("replics_info: %s", replics_info)
                replics_weights = self.config.get('global', 'replics_weights')
                for i in replics_info:
                    replica_host_name = i[0]
                    replica_state = i[1]
                    if replica_host_name is None or replica_host_name not in self.hosts.keys():
                        logging.warning(replics_info)
                        continue
                    if replica_state == 'sync':
                        if replics_weights != 'yes' and replics_weights != 'YES':
                            self.hosts[replica_host_name]['base_prio'] = 10
                        else:
                            self.hosts[replica_host_name]['base_prio'] = self.get_priority_according_to_load(
                                self.hosts[replica_host_name]['conn_string']) - 20
                    else:
                        if self.hosts[replica_host_name]['dc'] == self.my_dc:
                            if replics_weights != 'yes' and replics_weights != 'YES':
                                self.hosts[replica_host_name]['base_prio'] = 20
                            else:
                                self.hosts[replica_host_name]['base_prio'] = self.get_priority_according_to_load(
                                    self.hosts[replica_host_name]['conn_string']) - 10
                        else:
                            if replics_weights != 'yes' and replics_weights != 'YES':
                                self.hosts[replica_host_name]['base_prio'] = 30
                            else:
                                self.hosts[replica_host_name]['base_prio'] = self.get_priority_according_to_load(
                                    self.hosts[replica_host_name]['conn_string'])
            cur.close()
        except psycopg2.OperationalError:
            pass
        except psycopg2.ProgrammingError:
            pass

    def get_priority_according_to_load(self, conn_string):
        logging.debug("Going to count load for replic: %s", conn_string)
        load_calculation = self.config.get('global', 'load_calculation')
        if load_calculation == 'pgbouncer':
            conn_string = self.config.get('global', 'pgbouncer_conn_string')

        logging.debug('%s %s', conn_string, self.repl_append_string)
        conn = psycopg2.connect('%s %s' % (conn_string, self.repl_append_string))
        conn.autocommit = True
        cur = conn.cursor()

        if load_calculation == 'pgbouncer':
            cur.execute("show config;")
            max = [int(i[1]) for i in cur.fetchall() if i[0] == 'max_client_conn'][0]
            cur.execute("show clients;")
            current = len(cur.fetchall())
        elif load_calculation == 'postgres':
            cur.execute("select setting from pg_settings where name='max_connections';")
            max = int(cur.fetchone()[0])
            cur.execute("select count(*) from pg_stat_activity;")
            current = cur.fetchone()[0]
        else:
            return 30
        cur.close()
        conn.close()
        logging.debug('%d/%d', current, max)
        # should be from 50 to 100
        new_priority = 50 + int(current * 100.0 / max / 2)
        if 50 <= new_priority <= 100:
            return new_priority
        else:
            return 30

    def update_base_priorities(self):
        cur = self.conn_local.cursor()
        for k, v in self.hosts.items():
            # k = 'pgtest01e.domain.com'
            # v = {'host_id': 2, 'conn_string': ..., 'dc': 'IVA', 'base_prio': 0}
            cur.execute("select base_prio from plproxy.hosts where host_id=%d;" % v['host_id'])
            current_base_prio = cur.fetchone()[0]
            if current_base_prio != v['base_prio']:
                logging.info("Base priority of host %s has been updated to %d", k, v['base_prio'])
                cur.execute("update plproxy.hosts set base_prio=%d where host_id=%d;" % (v['base_prio'], v['host_id']))
        self.conn_local.commit()
        cur.close()
