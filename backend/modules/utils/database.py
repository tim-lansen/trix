# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

# PostgreSQL interface
# Users, tables, etc.: look trix_config.json
# CLI interface: "C:\Program Files\PostgreSQL\9.6\bin\psql.exe" --username=trix --host=localhost trix_db
# su - trix
# psql trix_db


import re
import sys
import uuid
import select
from typing import List
from pprint import pformat
import psycopg2
import psycopg2.extras
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from .log_console import Logger, tracer
from .types import Guid
from modules.config import TRIX_CONFIG
from modules.models import Asset, Interaction, Job, Task, MediaChunk, MediaFile, Machine, Node, Record, Collector, Fileset


# Establish a connection to db using args
def connect_to_db(args):
    try:
        psycopg2.extras.register_uuid()
        conn = psycopg2.connect(**args)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    except psycopg2.Error as e:
        Logger.error("Unable to connect to DB: {}\n{}\n{}\n".format(args, e.pgerror, e.diag.message_detail))
        return None
    return conn


# Execute a request using cursor supplied
def request_db(cur, req, exit_on_fail=False):
    Logger.debug('Request:\n{}\n'.format(req), Logger.LogLevel.LOG_NOTICE)
    result = True
    try:
        cur.execute(req)
    except psycopg2.Error as e:
        Logger.error('Failed to execute request\n{}\n{}\n'.format(e.pgerror, e.diag.message_detail))
        Logger.error('{}\n'.format(req), Logger.LogLevel.LOG_ERR)
        Logger.traceback(Logger.LogLevel.LOG_ERR)
        if exit_on_fail:
            cur.connection.close()
            sys.exit(1)
        result = False
    return result


# Execute a request using supplied cursor, table data (from config, including fields list) and condition string
# Condition has SQL form, for example 'WHERE status=1'
# return [{field:value, ...}, ...]
def request_db_return_dl(cur, tdata, fields, condition):
    # We must have list of column names to build dict
    # if fields is None:
    #     fields = [f[0] for f in tdata['fields']]
    # request = "SELECT {fields} FROM {relname}{cond};".format(fields=', '.join(fields), relname=tdata['relname'], cond=condition)
    if fields is None:
        fstr = '*'
        fields = [f[0] for f in tdata['fields']]
    else:
        fstr = ','.join(fields)
    request = "SELECT {fields} FROM {relname}{cond};".format(fields=fstr, relname=tdata['relname'], cond=condition)
    Logger.debug('Request: {}\n'.format(request), Logger.LogLevel.LOG_NOTICE)
    result = []
    try:
        cur.execute(request)
    except psycopg2.Error as e:
        Logger.error('Failed to execute request\n{0}\n{1}\n'.format(e.pgerror, e.diag.message_detail))
        Logger.traceback(Logger.LogLevel.LOG_ERR)
    else:
        rows = cur.fetchall()
        for row in rows:
            result.append(dict(zip(fields, row)))
    return result


# Execute a request using supplied cursor, table data (from config, including fields list) and condition string
# Condition has SQL form, for example 'WHERE status=1'
# return {'row[fields[0]]': {field:value, ...}, ...}
def request_db_return_dict(cur, tdata, key=None, fields=None, condition=''):
    # We must have list of column names to build dict
    # if fields is None:
    #     fields = [f[0] for f in tdata['fields']]
    # request = "SELECT {fields} FROM {relname}{cond};".format(fields=', '.join(fields), relname=tdata['relname'], cond=condition)
    if fields is None:
        fstr = '*'
        fields = [f[0] for f in tdata['fields']]
    else:
        fstr = ','.join(fields)
    if key not in fields:
        Logger.debug('Key {} not in requested field list {}\n'.format(key, fields), Logger.LogLevel.LOG_WARNING)
        key = fields[0]
    request = "SELECT {fields} FROM {relname}{cond};".format(fields=fstr, relname=tdata['relname'], cond=condition)
    result = {}
    try:
        cur.execute(request)
    except psycopg2.Error as e:
        Logger.error('Failed to execute request\n{0}\n{1}\n'.format(e.pgerror, e.diag.message_detail))
        Logger.traceback(Logger.LogLevel.LOG_ERR)
    else:
        rows = cur.fetchall()
        for row in rows:
            d = dict(zip(fields, row))
            result[d[key]] = d
    return result


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
        request = "SELECT relname FROM pg_class WHERE relname LIKE 'trix%' AND reltype<>0;"
        request_db(cur, request, exit_on_fail=True)
        rows = cur.fetchall()
        db_tables = {t[0] for t in rows}
        for t in TRIX_CONFIG.dBase.tables:
            ct = TRIX_CONFIG.dBase.tables[t]
            Logger.debug('{}\n'.format(ct), Logger.LogLevel.LOG_WARNING)
            if ct['relname'] in db_tables:
                # Check table's columns
                request = "SELECT * FROM {relname} WHERE false;".format(relname=ct['relname'])
                request_db(cur, request)
                rows = cur.fetchall()
                # TODO: check field types
                db_fields = {d[0] for d in cur.description}
                # Make all column names from config lowercase
                fields = {k[0].lower() for k in ct['fields']}
                if len(db_fields.symmetric_difference(fields)):
                    Logger.debug('Table {} structure is wrong\nfields:\n  c - d: {}\n  d - c: {}\n'.format(t, fields.difference(db_fields), db_fields.difference(fields)), Logger.LogLevel.LOG_WARNING)
                    # Drop table
                    request = "DROP TABLE {};".format(ct['relname'])
                    request_db(cur, request)
                    db_tables.remove(ct['relname'])
            if ct['relname'] not in db_tables:
                # Create table
                Logger.debug('Creating table {}\n'.format(t), Logger.LogLevel.LOG_INFO)
                fields = ['{0} {1}'.format(k[0], k[1]) for k in ct['fields']]
                if 'fields_extra' in ct:
                    fields += ['{0} ({1})'.format(k[0], k[1]) for k in ct['fields_extra']]
                request = '\n'.join(ct['creation']).format(relname=ct['relname'], fields=', '.join(fields), **config_users)
                # Logger.info(request + '\n')
                request_db(cur, request, exit_on_fail=True)
        cur.close()
        conn.close()

    @staticmethod
    def _drop_all_tables():
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
        # Retrieve/create tables
        request = "SELECT relname FROM pg_class WHERE relname LIKE 'trix%' AND reltype<>0;"
        request_db(cur, request, exit_on_fail=True)
        rows = cur.fetchall()
        if len(rows):
            request = "DROP TABLE {};".format(','.join([t[0] for t in rows]))
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

    @staticmethod
    def request_db(request, user=USER):
        result = False
        conn = DBInterface.connect(user)
        if conn is not None:
            cur = conn.cursor()
            result = request_db(cur, request)
        return result

    # Get records from table filtered by status or status list
    # status may be single value, or list of values: [1, 3, 4]
    # cond is a list of filtering conditions: ['type=2', 'priority>3']
    @staticmethod
    def get_records(table_name, fields=None, status=None, sort=None, cond=None, limit=None, user=USER):
        result = None
        conn = DBInterface.connect(user)
        if conn is not None:
            cur = conn.cursor()
            if cond is None:
                cond = []
            if type(status) is int:
                cond.append('status={}'.format(status))
            elif type(status) is list:
                cond.append(' OR '.join(['status={}'.format(s) for s in status]))
            condition = ''
            if len(cond):
                condition = ' WHERE ' + ' AND '.join(cond)
            if sort is not None:
                condition += ' ORDER BY {}'.format(', '.join(sort))
            if type(limit) is int:
                condition += ' LIMIT {}'.format(limit)
            result = request_db_return_dl(cur, TRIX_CONFIG.dBase.tables[table_name], fields, condition)
            cur.close()
        Logger.debug('{}\n'.format(pformat(result), Logger.LogLevel.LOG_INFO))
        return result

    # Get records from table filtered by status or status list
    @staticmethod
    def get_records_dict(table_name, key=None, fields=None, status=None, cond=None, user=USER):
        result = None
        conn = DBInterface.connect(user)
        if conn is not None:
            cur = conn.cursor()
            if cond is None:
                cond = []
            if type(status) is int:
                cond.append('status={}'.format(status))
            elif type(status) is list:
                cond.append(' OR '.join(['status={}'.format(s) for s in status]))
            condition = ''
            if len(cond):
                condition = ' WHERE ' + ' AND '.join(cond)
            result = request_db_return_dict(cur, TRIX_CONFIG.dBase.tables[table_name], key, fields, condition)
            cur.close()
        Logger.debug('{}\n'.format(pformat(result), Logger.LogLevel.LOG_INFO))
        return result

    # Get records from table filtered by status
    @staticmethod
    def get_record(table_name, uid, user=USER):
        result = None
        conn = DBInterface.connect(user)
        if conn is not None:
            cur = conn.cursor()
            result = request_db_return_dl(cur, TRIX_CONFIG.dBase.tables[table_name], None, " WHERE guid='{}'".format(uid))
            cur.close()
        Logger.debug('{}\n'.format(pformat(result), Logger.LogLevel.LOG_INFO))
        return result

    @staticmethod
    def get_record_by_field(table_name, field, value, user=USER):
        result = None
        conn = DBInterface.connect(user)
        if conn is not None:
            cur = conn.cursor()
            result = request_db_return_dl(
                cur,
                TRIX_CONFIG.dBase.tables[table_name],
                None,
                " WHERE {}='{}'".format(field, value)
            )
            cur.close()
        Logger.debug('{}\n'.format(pformat(result), Logger.LogLevel.LOG_INFO))
        return result

    @staticmethod
    def get_record_to_class(table_name, uid, user=USER):
        # table_name is also the class name
        data = DBInterface.get_record(table_name, uid, user)
        if data is None or len(data) != 1:
            return None
        instance = globals()[table_name]()
        instance.update_json(data[0])
        return instance

    @staticmethod
    def get_record_by_field_to_class(table_name, field, value, user=USER):
        # table_name is also the class name
        data = DBInterface.get_record_by_field(table_name, field, value, user)
        if data is None or len(data) != 1:
            return None
        instance = globals()[table_name]()
        instance.update_json(data[0])
        return instance

    @staticmethod
    def delete_records(table_name, ids, user=USER):
        result = False
        conn = DBInterface.connect(user)
        if conn is not Node:
            request = "DELETE FROM {relname} WHERE {condition};".format(
                relname=TRIX_CONFIG.dBase.tables[table_name]['relname'],
                condition=" OR ".join(["guid='{}'".format(_) for _ in ids])
            )

            cur = conn.cursor()
            result = request_db(cur, request)
            cur.close()
        return result

    @staticmethod
    def register_record(rec: Record, user=USER):
        result = False
        conn = DBInterface.connect(user)
        if conn is not None:
            cur = conn.cursor()
            request = 'SELECT localtimestamp;'
            if request_db(cur, request):
                rows = cur.fetchall()
                rec.ctime = str(rows[0][0])
                rec.mtime = str(rows[0][0])
                if rec.guid is None:
                    rec.guid = Guid(0)
                # Select table and fields
                rd = rec.__dict__
                table_name = rec.__class__.__name__
                tdata = TRIX_CONFIG.dBase.tables[table_name]
                fields = [f[0] for f in tdata['fields'] if rd[f[0]] is not None and not (type(rd[f[0]]) is list and len(rd[f[0]]) == 0)]
                # Build request
                request = "INSERT INTO {relname} ({fields}) VALUES ({values});".format(
                    relname=TRIX_CONFIG.dBase.tables[table_name]['relname'],
                    fields=','.join(fields),
                    values=','.join([rec.db_value(f) for f in fields])
                )
                # Register node
                result = request_db(cur, request)
            cur.close()
        return result

    @staticmethod
    def update_record(rec: Record, field_set: set, user=USER):
        result = False
        conn = DBInterface.connect(user)
        if conn is not None:
            cur = conn.cursor()
            request = 'SELECT localtimestamp;'
            if request_db(cur, request):
                rows = cur.fetchall()
                rec.mtime = str(rows[0][0])
                if rec.guid is None:
                    rec.guid = Guid(0)
                # Select table and fields
                rd = rec.__dict__
                table_name = rec.__class__.__name__
                # Build request
                request = "UPDATE {relname} SET {setup};".format(
                    relname=TRIX_CONFIG.dBase.tables[table_name]['relname'],
                    setup=','.join(['{}={}'.format(f, rec.db_value(f)) for f in field_set if rd[f] is not None])
                )
                # Register node
                result = request_db(cur, request)
            cur.close()
        return result

    @staticmethod
    def notify_list(notifications):
        conn = DBInterface.connect()
        request = ''.join(["NOTIFY {}, '{}';".format(c, m) for c, m in notifications])
        cur = conn.cursor()
        cur.execute(request)
        cur.close()

    class Interaction:
        @staticmethod
        def set(inter: Interaction):
            return DBInterface.register_record(inter, user=DBInterface.Machine.USER)

        # Request interactions filtered by status, return list sorted
        # @staticmethod
        # def records(status=None):
        #     return DBInterface.get_records('Interaction',
        #                                    fields=['guid', 'name', 'status', 'ctime', 'mtime'],
        #                                    status=status,
        #                                    sort=['ctime ASC', 'mtime DESC', 'status'])

        @staticmethod
        def records(status, condition):
            fields = TRIX_CONFIG.dBase.fields('Interaction')
            return DBInterface.get_records('Interaction',
                                           # fields=['guid', 'name', 'status'],
                                           fields=fields,
                                           status=status,
                                           cond=condition,
                                           sort=['priority DESC', 'ctime ASC', 'mtime DESC', 'status'])

        @staticmethod
        def get(uid):
            return DBInterface.get_record_to_class('Interaction', uid)

        # Lock the interaction
        @staticmethod
        def lock(uid):
            conn = DBInterface.connect()
            cur = conn.cursor()
            # First, try to lock an interaction
            table_name = TRIX_CONFIG.dBase.tables['Interaction']['relname']
            new_status = Interaction.Status.LOCK
            req = "UPDATE {tname} SET status={status} WHERE guid='{guid}' AND status<>{status};".format(
                tname=table_name,
                status=new_status,
                guid=uid
            )
            return request_db(cur, req)

        @staticmethod
        def unlock(uid):
            conn = DBInterface.connect()
            cur = conn.cursor()
            # First, try to lock an interaction
            table_name = TRIX_CONFIG.dBase.tables['Interaction']['relname']
            new_status = Interaction.Status.FREE
            req = "UPDATE {tname} SET status={status} WHERE guid='{guid}' AND status<>{status};".format(
                tname=table_name,
                status=new_status,
                guid=uid
            )
            return request_db(cur, req)

        # @staticmethod
        # def get_all_sorted():
        #     ia = redis_data.get_free_interactions(inter_server)
        #     # Resort interactions
        #     interactions = redis_data.get_stuff_sorted(ia)
        #     return {'result': interactions}

    class Asset:
        @staticmethod
        def records(uids):
            fields = TRIX_CONFIG.dBase.fields('Asset')
            condition = ["guid=ANY('{{{}}}'::uuid[])".format(','.join(uids))]
            return DBInterface.get_records('Asset',
                                           fields=fields,
                                           cond=condition)

        @staticmethod
        def get(uid):
            return DBInterface.get_record_to_class('Asset', uid)

        @staticmethod
        def get_dict(uid):
            data = DBInterface.get_record('Asset', uid)
            if data is None or len(data) != 1:
                return None
            return data[0]

        @staticmethod
        def set(asset: Asset):
            # Logger.warning('{}\n'.format(asset.dumps(indent=2)))
            return DBInterface.register_record(asset, user=DBInterface.Machine.USER)
            # return DBInterface.Asset.set_str(asset.dumps())

        @staticmethod
        def set_str(asset: str):
            ass = Asset()
            ass.update_str(asset)
            return DBInterface.register_record(ass, user=DBInterface.Machine.USER)

        @staticmethod
        def update_videoStreams(asset: Asset):
            return DBInterface.update_record(asset, {'videoStreams'})
            # vstrs = ','.join([_.dumps() for _ in asset.videoStreams])  # Asset.jsoner_list_to_json(asset.videoStreams)
            # request = "UPDATE trix_assets SET videoStreams = ARRAY[{vs}]::json WHERE guid='{id}';".format(
            #     vs=vstrs,
            #     id=asset.guid
            # )
            # return DBInterface.request_db(request)

        @staticmethod
        def delete(uid):
            DBInterface.delete_records('Asset', [uid])

    class MediaFile:
        @staticmethod
        def get(uid):
            return DBInterface.get_record_to_class('MediaFile', uid)

        @staticmethod
        def get_dict(uid):
            data = DBInterface.get_record('MediaFile', uid)
            if data is None or len(data) != 1:
                return None
            return data[0]

        @staticmethod
        def set(mediafile: MediaFile):
            return DBInterface.register_record(mediafile, user=DBInterface.Machine.USER)

        @staticmethod
        def set_str(mediaFile: str):
            mf: MediaFile = MediaFile(guid=None)
            mf.update_str(mediaFile)
            return DBInterface.register_record(mf, user=DBInterface.Machine.USER)

        @staticmethod
        def update_videoTrack(mf: MediaFile, index):
            request = "UPDATE {table} SET videoTracks[{index}]='{vtrack}' WHERE guid='{guid}'".format(
                table=TRIX_CONFIG.dBase.tables['MediaFile']['relname'],
                index=index + 1,
                vtrack=mf.videoTracks[index].dumps(),
                guid=mf.guid
            )
            return DBInterface.request_db(request)

    class Machine:
        USER = 'node'

        @staticmethod
        def get(uid) -> Machine:
            return DBInterface.get_record_to_class('Machine', uid)

        @staticmethod
        def get_by_ip(ip: str) -> Machine:
            return DBInterface.get_record_by_field_to_class('Machine', 'ip', ip)

        @staticmethod
        def register(machine: Machine):
            return DBInterface.register_record(machine, user=DBInterface.Machine.USER)

    class Node:
        USER = 'node'

        @staticmethod
        def get(uid) -> Node:
            return DBInterface.get_record_to_class('Node', uid)

        # @staticmethod
        # def list_by_ip(ip: str) -> List[str]:
        #     # Retrieve all registered nodes which name is like '<ip>#%'
        #     cond = "name LIKE '{}#%'".format(ip)
        #     return DBInterface.get_records('Node', fields=['guid', 'name'], cond=[cond])

        # Register node in db
        @staticmethod
        def register(node: Node):
            return DBInterface.register_record(node, user=DBInterface.Node.USER)

        # Unregister node
        @staticmethod
        def remove(node: Node, backend=True):
            conn = DBInterface.connect(DBInterface.USER if backend else DBInterface.Node.USER)
            if conn is None:
                Logger.warning('DBInterface.Node.register({}): connection is None\n'.format(node.name))
                return False
            # Ask server time
            cur = conn.cursor()
            request = "DELETE FROM {relname} WHERE guid='{uid}';".format(
                relname=TRIX_CONFIG.dBase.tables['Node']['relname'],
                uid=node.guid
            )
            result = request_db(cur, request)
            cur.close()
            if not backend:
                DBInterface.disconnect(DBInterface.Node.USER)
            return result

        @staticmethod
        def set_fields(uid, fields: dict):
            fields['mtime'] = 'localtimestamp'
            setup = ','.join(['{}={}'.format(k, fields[k]) for k in fields])
            request = "UPDATE {relname} SET {setup} WHERE guid='{uid}';".format(
                relname=TRIX_CONFIG.dBase.tables['Node']['relname'],
                setup=setup,
                uid=uid
            )
            return DBInterface.request_db(request)

        @staticmethod
        def set_status(uid, status):
            return DBInterface.Node.set_fields(uid, {'status': status})

        @staticmethod
        def pong(node: Node):
            conn = DBInterface.connect(DBInterface.Node.USER)
            if conn is None:
                Logger.warning('DBInterface.Node.register({}): DBInterface.CONN is None\n'.format(node.name))
                return False
            # Ask server time
            cur = conn.cursor()
            request = 'SELECT localtimestamp;'
            result = False
            if request_db(cur, request):
                rows = cur.fetchall()
                node.mtime = str(rows[0][0])
                # Update node's mtime
                request = "UPDATE {relname} SET mtime=localtimestamp,status={status} WHERE guid='{node_id}';".format(
                    relname=TRIX_CONFIG.dBase.tables['Node']['relname'],
                    # mtime=node.mtime,
                    status=node.status,
                    node_id=node.guid
                )
                result = request_db(cur, request)
            cur.close()
            return result

        @staticmethod
        def records(status=None):
            return DBInterface.get_records('Node',
                                           fields=['guid', 'name', 'status', 'ctime', 'mtime'],
                                           status=status,
                                           sort=['ctime ASC', 'mtime DESC', 'status'])

        @staticmethod
        def listen(node: Node, blocking=True):
            conn = DBInterface.connect(DBInterface.Node.USER)
            if conn is None:
                Logger.warning('DBInterface.Node.register({}): DBInterface.CONN is None\n'.format(node.name))
                return None
            cur = conn.cursor()
            request = "LISTEN {};".format(node.channel)
            cur.execute(request)
            notifications = []
            while 1:
                a = select.select([conn], [], [], 5)[0]
                if len(a) > 0:
                    conn.poll()
                    while conn.notifies:
                        notifications.append(conn.notifies.pop(0))
                    break
                # else:
                    # Logger.info('DBIinterface.Node.listen: timeout\n')
                if not blocking:
                    break

            return notifications

    class Job:
        USER = 'node'

        @staticmethod
        def get(uid) -> Job:
            return DBInterface.get_record_to_class('Job', uid)

        @staticmethod
        def register(job: Job):
            return DBInterface.register_record(job, user=DBInterface.Job.USER)

        @staticmethod
        def delete(uid):
            return DBInterface.delete_records('Job', [uid])

        @staticmethod
        def set_fields(uid, fields: dict):
            fields['mtime'] = 'localtimestamp'
            setup = ','.join(['{}={}'.format(k, fields[k]) for k in fields])
            request = "UPDATE {relname} SET {setup} WHERE guid='{uid}';".format(
                relname=TRIX_CONFIG.dBase.tables['Job']['relname'],
                setup=setup,
                uid=uid
            )
            return DBInterface.request_db(request)

        @staticmethod
        def set_fields_list(uids, fields: dict):
            fields['mtime'] = 'localtimestamp'
            condition = ["guid=ANY('{{{}}}'::uuid[])".format(','.join(uids))]
            setup = ','.join(['{}={}'.format(k, fields[k]) for k in fields])
            request = "UPDATE {relname} SET {setup} WHERE {condition};".format(relname=TRIX_CONFIG.dBase.tables['Job']['relname'],
                                                                               setup=setup,
                                                                               condition=condition)
            return DBInterface.request_db(request)

        @staticmethod
        def set_fields_by_groups(group_ids, fields: dict):
            fields['mtime'] = 'localtimestamp'
            condition = "'{{{}}}'::uuid[] && groupIds".format(','.join(group_ids))
            setup = ','.join(['{}={}'.format(k, fields[k]) for k in fields])
            request = "UPDATE {relname} SET {setup} WHERE {condition};".format(relname=TRIX_CONFIG.dBase.tables['Job']['relname'],
                                                                               setup=setup,
                                                                               condition=condition)
            return DBInterface.request_db(request)

        @staticmethod
        def set_status(uid, status):
            return DBInterface.Job.set_fields(uid, {'status': status})

    class Task:
        USER = 'node'

        @staticmethod
        def get(uid) -> Task:
            return DBInterface.get_record_to_class('Task', uid)

        @staticmethod
        def register(task: Task):
            return DBInterface.register_record(task, user=DBInterface.Task.USER)

        @staticmethod
        def delete(uid):
            return DBInterface.delete_records('Task', [uid])

        @staticmethod
        def set_fields(uid, fields: dict):
            fields['mtime'] = 'localtimestamp'
            setup = ','.join(['{}={}'.format(k, fields[k]) for k in fields])
            request = "UPDATE {relname} SET {setup} WHERE guid='{uid}';".format(
                relname=TRIX_CONFIG.dBase.tables['Task']['relname'],
                setup=setup,
                uid=uid
            )
            return DBInterface.request_db(request)

        @staticmethod
        def set_status(uid, status):
            return DBInterface.Task.set_fields(uid, {'status': status})

    class Collector:
        USER = 'node'

        @staticmethod
        def get(uid) -> Collector:
            return DBInterface.get_record_to_class('Collector', uid)

        @staticmethod
        def set(collector: Collector):
            # request = "INSERT INTO trix_collector (guid,name,ctime,mtime,collected) VALUES ('{guid}','{name}',localtimestamp,localtimestamp,ARRAY[{var}]::text[]);".format(
            #     guid=str(collector.guid),
            #     name=collector.name,
            #     var=','.join(["'{}'".format(_) for _ in collector.collected])
            # )
            # return DBInterface.request_db(request)
            return DBInterface.register_record(collector, user=DBInterface.Collector.USER)

        @staticmethod
        def records(uids):
            fields = TRIX_CONFIG.dBase.fields('Collector')
            condition = ["guid=ANY('{{{}}}'::uuid[])".format(','.join(uids))]
            return DBInterface.get_records('Collector',
                                           fields=fields,
                                           cond=condition)

        @staticmethod
        def register(collector_name: str, collector_id: str):
            collector: Collector = Collector(name=collector_name, guid=collector_id)
            return DBInterface.register_record(collector, user=DBInterface.Collector.USER)

        # Temporary use text mode
        @staticmethod
        def append_slice_result(collector_id: str, slice_result: Collector.SliceResult):
            request = "UPDATE trix_collector SET sliceResults = sliceResults || '{sr}'::text WHERE guid='{id}';".format(
                sr=slice_result.dumps(),
                id=collector_id
            )
            return DBInterface.request_db(request)

    class Fileset:
        USER = 'backend'

        @staticmethod
        def get(uid) -> Fileset:
            return DBInterface.get_record_to_class('Fileset', uid)

        @staticmethod
        def get_dict(uid):
            return DBInterface.get_record('Fileset', uid)

        @staticmethod
        def set(fs: Fileset):
            return DBInterface.register_record(fs, user=DBInterface.Fileset.USER)

        @staticmethod
        def records_by_uids(uids):
            fields = TRIX_CONFIG.dBase.fields('Fileset')
            condition = ["guid=ANY('{{{}}}'::uuid[])".format(','.join(uids))]
            return DBInterface.get_records('Fileset', fields=fields, cond=condition)

        @staticmethod
        def records_fields(fields: set):
            return DBInterface.get_records('Fileset', fields=fields)

        @staticmethod
        def record_by_name(name):
            return DBInterface.get_record_by_field_to_class('Fileset', field='name', value=name, user=DBInterface.Fileset.USER)

        @staticmethod
        def update_fields(fs: Fileset, field_set: set):
            return DBInterface.update_record(fs, field_set, user=DBInterface.Fileset.USER)

        @staticmethod
        def remove_by_names(names: List[str]):
            conn = DBInterface.connect(DBInterface.Fileset.USER)
            if conn is None:
                return False
            cur = conn.cursor()
            request = "DELETE FROM {relname} WHERE name=ANY('{{{names}}}'::name[]);".format(
                relname=TRIX_CONFIG.dBase.tables['Fileset']['relname'],
                names=','.join(names)
            )
            result = request_db(cur, request)
            cur.close()
            return result

