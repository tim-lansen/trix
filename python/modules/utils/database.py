# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

# PostgreSQL interface
# Users, tables, etc.: look trix_config.json


import sys
import uuid
import select
from pprint import pformat
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from .log_console import Logger, DebugLevel, tracer
from ..config.trix_config import TRIX_CONFIG
from ..models import Job, Node, Asset, Interaction


# Establish a connection to db using args
def connect_to_db(args):
    try:
        # Try to connect to DB as superuser
        conn = psycopg2.connect(**args)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    except psycopg2.Error as e:
        Logger.error("Unable to connect to DB\n{0}\n{1}\n".format(e.pgerror, e.diag.message_detail))
        return None
    return conn


# Execute a request using supplied cursor
def request_db(cur, req, exit_on_fail=False):
    Logger.info('Request:\n{}\n'.format(req))
    result = True
    try:
        cur.execute(req)
    except psycopg2.Error as e:
        Logger.error('Failed to execute request\n{0}\n{1}\n'.format(e.pgerror, e.diag.message_detail))
        if exit_on_fail:
            cur.connection.close()
            sys.exit(1)
        result = False
    return result


# Execute a request using supplied cursor, table data (from config, including fields list) and condition string
# Condition has SQL form, for example 'WHERE status=1'
# return [{field:value, ...}, ...]
def request_db_return_dl(cur, tdata, fields, condition):
    if fields is None:
        fields = [f[0] for f in tdata['fields']]
    request = "SELECT {fields} FROM {relname}{cond};".format(fields=', '.join(fields), relname=tdata['relname'], cond=condition)
    Logger.info('Request:\n{}\n'.format(request))
    result = []
    try:
        cur.execute(request)
    except psycopg2.Error as e:
        Logger.error('Failed to execute request\n{0}\n{1}\n'.format(e.pgerror, e.diag.message_detail))
    else:
        rows = cur.fetchall()
        for row in rows:
            result.append(dict(zip(fields, row)))
    return result


# Execute a request using supplied cursor, table data, fields list and condition string
# Condition has SQL form, for example 'WHERE status=1'
# return [[value, ...], ...]
# def request_db_return_list(cur, tdata, fields, condition):
#     request = "SELECT {fields} FROM {relname}{cond};".format(fields=fields, relname=tdata['relname'], cond=condition)
#     Logger.info('Request:\n{}\n'.format(request))
#     result = []
#     try:
#         cur.execute(request)
#     except psycopg2.Error as e:
#         Logger.error('Failed to execute request\n{0}\n{1}\n'.format(e.pgerror, e.diag.message_detail))
#     else:
#         rows = cur.fetchall()
#         for row in rows:
#             result.append(row)
#     return result


class DBInterface:
    # CONN = None
    CONNECTIONS = {}
    USER = 'backend'
    SUPERUSER = 'superuser'

    @staticmethod
    def initialize():
        # Try to connect to DB as superuser
        params = {
            'host': TRIX_CONFIG.dBase.connection.host,
            'port': TRIX_CONFIG.dBase.connection.port,
            'dbname': TRIX_CONFIG.dBase.connection.dbname,
            'user': TRIX_CONFIG.dBase.users[DBInterface.SUPERUSER]['login'],
            'password': TRIX_CONFIG.dBase.users[DBInterface.SUPERUSER]['password']
        }
        conn = connect_to_db(params)
        if conn is None:
            sys.exit(1)

        cur = conn.cursor()
        # Retrieve users and check if there are necessary records
        request = 'SELECT usename FROM pg_user;'
        request_db(cur, request, exit_on_fail=True)
        rows = cur.fetchall()
        db_users = {u[0] for u in rows}
        config_users = {}
        for u in TRIX_CONFIG.dBase.users:
            cu = TRIX_CONFIG.dBase.users[u]
            config_users[u] = cu['login']
            if u != 'superuser':
                if cu['login'] not in db_users:
                    # Add user to DB
                    print('Creating user {}'.format(u))
                    request = '''CREATE USER {0} WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT NOREPLICATION CONNECTION LIMIT -1 PASSWORD '{1}';'''.format(cu['login'], cu['password'])
                    request_db(cur, request, exit_on_fail=True)
                    # Check result
                    request = "SELECT usename FROM pg_user WHERE usename='{}';".format(cu['login'])
                    request_db(cur, request, exit_on_fail=True)
                    answ = cur.fetchall()
                    if len(answ) != 1 and answ[0][0] == cu['login']:
                        print('Failed to add user {}({}) to DB', u, cu['login'])
        # Retrieve/create tables
        request = "SELECT relname FROM pg_class WHERE relname LIKE 'trix%';"
        request_db(cur, request, exit_on_fail=True)
        rows = cur.fetchall()
        db_tables = {t[0] for t in rows}
        for t in TRIX_CONFIG.dBase.tables:
            ct = TRIX_CONFIG.dBase.tables[t]
            if ct['relname'] in db_tables:
                # Check table's columns
                request = "SELECT * FROM {relname} WHERE false;".format(relname=ct['relname'])
                request_db(cur, request)
                rows = cur.fetchall()
                # TODO: check field types
                db_fields = {d[0] for d in cur.description}
                fields = {k[0] for k in ct['fields']}
                if len(db_fields.difference(fields)) != 0 or len(fields.difference(db_fields)) != 0:
                    Logger.warning('Table {} structure is wrong\n'.format(t))
                    # Drop table
                    request = "DROP TABLE {};".format(ct['relname'])
                    request_db(cur, request)
                    db_tables.remove(ct['relname'])
            if ct['relname'] not in db_tables:
                # Create table
                Logger.info('Creating table {}\n'.format(t))
                fields = ['{0} {1}'.format(k[0], k[1]) for k in ct['fields']]
                if 'fields_extra' in ct:
                    fields += ['{0} ({1})'.format(k[0], k[1]) for k in ct['fields_extra']]
                request = '\n'.join(ct['creation']).format(relname=ct['relname'], fields=', '.join(fields), **config_users)
                Logger.info(request + '\n')
                request_db(cur, request, exit_on_fail=True)
        cur.close()
        conn.close()

    @staticmethod
    def connect(user=USER):
        if user not in DBInterface.CONNECTIONS or DBInterface.CONNECTIONS[user] is None:
            params = {
                'host': TRIX_CONFIG.dBase.connection.host,
                'port': TRIX_CONFIG.dBase.connection.port,
                'dbname': TRIX_CONFIG.dBase.connection.dbname,
                'user': TRIX_CONFIG.dBase.users[user]['login'],
                'password': TRIX_CONFIG.dBase.users[user]['password']
            }
            DBInterface.CONNECTIONS[user] = connect_to_db(params)
        Logger.log("DBInterface.connect('{}'): {}\n".format(user, DBInterface.CONNECTIONS[user]))
        return DBInterface.CONNECTIONS[user]

    @staticmethod
    def disconnect(user=USER):
        if user in DBInterface.CONNECTIONS and DBInterface.CONNECTIONS[user] is not None:
            DBInterface.CONNECTIONS[user].close()
            DBInterface.CONNECTIONS[user] = None
            Logger.log("DBInterface.disconnect('{}')\n".format(user))

    # Get records from table filtered by status
    @staticmethod
    def get_records(table_name, fields=None, status=None, sort=None):
        result = None
        conn = DBInterface.connect()
        if conn is not None:
            cur = conn.cursor()
            condition = ''
            if status is not None:
                condition = ' WHERE status={}'.format(status)
            if sort is not None:
                condition += ' ORDER BY {}'.format(', '.join(sort))
            result = request_db_return_dl(cur, TRIX_CONFIG.dBase.tables[table_name], fields, condition)
            cur.close()
        Logger.info(pformat(result) + '\n')
        return result

    # Get records from table filtered by status
    @staticmethod
    def get_record(table_name, uid, conn=None):
        result = None
        if conn is None:
            conn = DBInterface.connect()
        if conn is not None:
            cur = conn.cursor()
            result = request_db_return_dl(cur, TRIX_CONFIG.dBase.tables[table_name], None, " WHERE id='{}'".format(uid))
            cur.close()
        Logger.info(pformat(result) + '\n')
        return result

    class Interaction:

        # Request interactions filtered by status, return list sorted
        @staticmethod
        def records(status=None):
            return DBInterface.get_records('Interaction',
                                           fields=['id', 'name', 'status', 'ctime', 'mtime'],
                                           status=status,
                                           sort=['ctime ASC', 'mtime DESC', 'status'])

        @staticmethod
        def get(uid):
            return DBInterface.get_record('Interaction', uid)

        # @staticmethod
        # def get_all_sorted():
        #     ia = redis_data.get_free_interactions(inter_server)
        #     # Resort interactions
        #     interactions = redis_data.get_stuff_sorted(ia)
        #     return {'result': interactions}

    class Node:
        USER = 'node'

        @staticmethod
        def get(uid):
            return DBInterface.get_record('Node', uid, DBInterface.connect(DBInterface.Node.USER))

        # Register node in db
        @staticmethod
        def register(_node: Node):
            conn = DBInterface.connect(DBInterface.Node.USER)
            if conn is None:
                Logger.warning('DBInterface.Node.register({}): connection is None\n'.format(_node.name))
                return False
            # Ask server time
            cur = conn.cursor()
            request = 'SELECT localtimestamp;'
            result = False
            if request_db(cur, request):
                rows = cur.fetchall()
                _node.ctime = rows[0][0]
                _node.mtime = rows[0][0]
                # Register node
                ndict = _node.__dict__
                fields = [f for f in _node.get_members_list() if ndict[f] is not None]

                request = "INSERT INTO {relname} ({fields}) VALUES ({values});".format(
                    relname=TRIX_CONFIG.dBase.tables['Node']['relname'],
                    fields=', '.join(fields),
                    values=', '.join(["'{}'".format(ndict[m]) for m in fields])
                )
                result = request_db(cur, request)
            cur.close()
            return result

        # Register node in db
        @staticmethod
        def unregister(_node: Node, backend=True):
            if backend:
                conn = DBInterface.connect(DBInterface.USER)
            else:
                conn = DBInterface.connect(DBInterface.Node.USER)
            if conn is None:
                Logger.warning('DBInterface.Node.register({}): connection is None\n'.format(_node.name))
                return False
            # Ask server time
            cur = conn.cursor()
            request = "DELETE FROM {relname} WHERE id='{id}';".format(
                relname=TRIX_CONFIG.dBase.tables['Node']['relname'],
                id=_node.id
            )
            result = request_db(cur, request)
            cur.close()
            if not backend:
                DBInterface.disconnect(DBInterface.Node.USER)
            return result

        # Register node in db
        @staticmethod
        def pong(_node: Node):
            conn = DBInterface.connect(DBInterface.Node.USER)
            if conn is None:
                Logger.warning('DBInterface.Node.register({}): DBInterface.CONN is None\n'.format(_node.name))
                return False
            # Ask server time
            cur = conn.cursor()
            request = 'SELECT localtimestamp;'
            result = False
            if request_db(cur, request):
                rows = cur.fetchall()
                _node.mtime = rows[0][0]
                # Update node's mtime
                request = "UPDATE {relname} SET mtime='{mtime}' WHERE id='{node_id}';".format(
                    relname=TRIX_CONFIG.dBase.tables['Node']['relname'],
                    mtime=_node.mtime,
                    node_id=_node.id
                )
                result = request_db(cur, request)
            cur.close()
            return result

        @staticmethod
        def records(status=None):
            return DBInterface.get_records('Node',
                                           fields=['id', 'name', 'status', 'ctime', 'mtime'],
                                           status=status,
                                           sort=['ctime ASC', 'mtime DESC', 'status'])

        @staticmethod
        def listen(_node: Node):
            conn = DBInterface.connect(DBInterface.Node.USER)
            if conn is None:
                Logger.warning('DBInterface.Node.register({}): DBInterface.CONN is None\n'.format(_node.name))
                return None
            cur = conn.cursor()
            request = "LISTEN {};".format(_node.channel)
            cur.execute(request)
            notifications = []
            while 1:
                if select.select([conn], [], [], 5) == ([], [], []):
                    Logger.info('timeout\n')
                else:
                    conn.poll()
                    while conn.notifies:
                        notifications.append(conn.notifies.pop(0))
                    break
            return notifications

    class Job:
        USER = 'node'

        @staticmethod
        def get(uid):
            return DBInterface.get_record('Job', uid, DBInterface.connect(DBInterface.Job.USER))


