# -*- coding: utf-8 -*-
# The Trix API
# Each request must contain 'method': <method name>, 'guid': <request guid>
# Method data should be in 'data': {<method data>}
# Methods may be cascaded: interaction.getList.filter

import sys
from concurrent.futures import ThreadPoolExecutor
from .log_console import Logger, tracer
from .database import DBInterface
import time
import json
import threading
from modules.websocket_server import ApiClassBase, ApiClientClassBase, WebsocketServer
import traceback


def traceback_debug():
    Logger.debug('===traceback===\n')
    for frame in traceback.extract_tb(sys.exc_info()[2]):
        Logger.debug('{}\n'.format(frame))
    Logger.debug('===============\n')


class ApiClient(ApiClientClassBase):
    AuthParams = {'name', 'phone_number', 'profile_id'}

    def __init__(self, handler):
        super().__init__(handler)
        self.addr = handler.client_address
        self.data = {
            'phone_number': None,
            'name': None,
            'profile_id': None,
            # 'device_token': None,
            # 'serial_number': None,
            'authorized': False,
            # 'thread': None,
            'message_id': 1
        }

    def authorize_by_main_service(self):

        def _check_authority_(data):
            time.sleep(0.5)
            data['authorized'] = True
        #     print(data)
        #     ws = websocket_client.create_connection('ws://napi.ayyo.ru')
        #     msg = json.dumps({
        #         'method': 'connect',
        #         'guid': str(data['message_id']),
        #         'params': {
        #             'version': '2',
        #             'device_token': data['device_token'],
        #             'application': {
        #                 'name': 'web_admin',
        #                 'version': '4.0.1'
        #             },
        #             'device_info': {
        #                 'serial_number': data['serial_number'],
        #                 'type': 'pc',
        #                 'name': 'PC',
        #                 'model': 'PC'
        #             }
        #         }
        #     })
        #     print(msg)
        #     ws.send(msg)
        #     result = json.loads(ws.recv())
        #     print(result)
        #     if result['error'] is None and int(result['guid']) == data['message_id']:
        #         data['message_id'] += 1
        #         msg = json.dumps({
        #             'method': 'widgets_all',
        #             'guid': str(data['message_id']),
        #             'params': {}
        #         })
        #         ws.send(msg)
        #         result = json.loads(ws.recv())
        #         print(result)
        #         if result['error'] is None and int(result['guid']) == data['message_id']:
        #             print('Authorized {0}'.format(data['phone_number']))
        #             self.data['authorized'] = True
        #     data['message_id'] += 1
        #     # pprint.pprint(result)
        #     data['thread'] = None
        #     ws.close()

        if self.data['authorized']:
            return 12345
        Logger.debug('_check_authority_ launched\n')
        _check_authority_(self.data)
        return self.data

    def authorized(self):
        return self.data['authorized']

    def reset(self):
        self.data['profile_id'] = None
        self.data['authorized'] = False


class meth:
    # Method handler default class
    need_auth = True


class ApiTrix(ApiClassBase):
    # Trix API
    # Every class' subclass is [sub]method name
    # 'handler' is a method handler
    # For example, if method is 'interaction.getList', then dispatcher calls
    #               ApiTrix.Request.Interaction.GetList.handler(request['data'])

    Pool = ThreadPoolExecutor(max_workers=128)

    class Request:
        class authorize(meth):
            need_auth = False

            @staticmethod
            def handler(params, client: ApiClient):
                for k in client.AuthParams:
                    if k in params:
                        client.data[k] = params[k]
                return client.authorize_by_main_service()

        class interaction:
            class getLock(meth):
                @staticmethod
                def handler(*args):
                    interaction = DBInterface.Interaction.get_lock(args[0]['guid'])
                    return interaction

            class getList(meth):
                @staticmethod
                def handler(*args):
                    """:param must contain\n""" \
                    """    'status': None|<integer>|[<int>, <int>, ...]\n""" \
                    """    'condition': None|[<condition 1>, <condition 2>, ...]""" \
                    """                 <condition X> is a string like 'type=2' or 'priority>3'"""
                    interactions = DBInterface.Interaction.get_list(args[0]['status'], args[0]['condition'])
                    return interactions

            class submit(meth):
                @staticmethod
                def handler(*args):
                    params = args[0]
                    return True

        class asset:
            class get(meth):
                @staticmethod
                def handler(*args):
                    params = args[0]
                    asset = DBInterface.Asset.get(params['guid'])

    @staticmethod
    def execute(target, request, client: ApiClient):
        try:
            params = request['params'] if 'params' in request else None
            respond = {
                'method': request['method'],
                'guid': request['guid']
            }
            if target.need_auth and not client.authorized():
                respond['error'] = 'not authorized'
            else:
                result = target.handler(params, client)
                respond['result'] = result
            Logger.debug('Respond: {}\n'.format(respond))
            client.ws_handler.send_message(json.dumps(respond))
        except Exception as e:
            Logger.warning('ApiTrix.execute exception: {}\n'.format(e))

    @staticmethod
    def dispatch(message, client: ApiClient):
        Logger.debug('ApiTrix.dispatch({}, {})\n'.format(message, client.data))
        try:
            request = json.loads(message)
            mpath = request['method'].split('.')
            # Pick target method class
            target = ApiTrix.Request
            for m in mpath:
                target = target.__dict__[m]
            # Call handler in parallel thread
            ApiTrix.Pool.submit(ApiTrix.execute, target, request, client)
        except Exception as e:
            Logger.warning('{}\n'.format(e))
            traceback_debug()

    def new_client(self, client: ApiClient, server):
        Logger.info('Client connected: {} / {}\n'.format(client.addr, client.ws_handler.guid))

    def client_left(self, client: ApiClient, server):
        Logger.info('Client disconnected: {} / {}\n'.format(client.addr, client.ws_handler.guid))

    def message_received(self, client: ApiClient, server, msg):
        self.dispatch(msg, client)
