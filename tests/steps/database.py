# coding: utf-8

import contextlib
import logging
from collections import namedtuple

import psycopg2

log = logging.getLogger(__name__)


class QueryResult(namedtuple('QueryResult', ['records', 'errcode', 'errmsg'])):
    pass


class Connection(object):
    def __init__(self, connstring):
        self.connstring = connstring
        self._conn = psycopg2.connect(self.connstring)
        self._conn.autocommit = True

    def __create_cursor(self):
        cursor = self._conn.cursor()
        return cursor

    def __exec_query(self, q, **kwargs):
        cur = self.__create_cursor()
        self.errcode = None
        self.errmsg = None
        try:
            cur.execute(q, kwargs)
        except psycopg2.Error as e:
            self.errcode = e.pgcode
            self.errmsg = e.pgerror
        return cur

    def __get_names(self, cur):
        return [r[0].lower() for r in cur.description]

    def __plain_format(self, cur):
        names = self.__get_names(cur)
        for row in cur.fetchall():
            yield dict(zip(names, tuple(row)))

    def get(self, q, **kwargs):
        with contextlib.closing(self.__exec_query(q, **kwargs)) as cur:
            records = list(self.__plain_format(cur)) if self.errcode is None else []
            return QueryResult(
                records,
                self.errcode,
                self.errmsg
            )

    def get_func(self, name, **kwargs):
        arg_names = ', '.join('{0} => %({0})s'.format(k) for k in kwargs)
        q = 'SELECT * FROM {name}({arg_names})'.format(
            name=name,
            arg_names=arg_names,
        )
        res = self.get(q, **kwargs)
        log.info(q, kwargs)
        log.info(res)
        return res
