# -*- coding: utf-8 -*-
# The Trix API
# Each request must contain 'method': <method name>, 'guid': <request guid>
# Method data should be in 'data': {<method data>}
# Methods may be cascaded: interaction.getList.filter

import sys
from concurrent.futures import ThreadPoolExecutor
from .log_console import Logger, tracer
from .database import DBInterface
from .jsoner import NonJSONSerializibleEncoder
import time
import json
import threading
from pprint import pformat
from modules.websocket_server import ApiClassBase, ApiClientClassBase, WebsocketServer
from modules.models.mediafile import MediaFile
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
            Logger.log('{}\n'.format(data))

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

    @staticmethod
    def handler(params, client: ApiClient):
        Logger.warning('Unhandled method: {}, client: {}\n'.format(params, client))


class ApiTrix(ApiClassBase):
    # Trix API
    # Every class' subclass is [sub]method name
    # 'handler' is a method handler
    # For example, if method is 'interaction.getList', then dispatcher calls
    #               ApiTrix.Request.Interaction.GetList.handler(request['data'])

    Pool = ThreadPoolExecutor(max_workers=128)

    class Request:
        class connect(meth):
            need_auth = False

            @staticmethod
            def handler(params, client: ApiClient):
                return {'session_id': client.ws_session_id}

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
                    """:param must contain""" \
                    """    'status': None|<integer>|[<int>, <int>, ...]""" \
                    """    'condition': None|[<condition 1>, <condition 2>, ...]""" \
                    """                 <condition X> is a string like 'type=2' or 'priority>3'"""
                    interactions = DBInterface.Interaction.records(args[0]['status'], args[0]['condition'])
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
                    asset = DBInterface.Asset.get_dict(params['guid'])
                    return asset

            class get_expanded(meth):
                # Load MediaFile(s) objects in place of their GUIDs, and source urls of previews in place of refs
                @staticmethod
                def handler(*args):
                    params = args[0]
                    asset = DBInterface.Asset.get_dict(params['guid'])
                    media_files = []
                    for guid in asset['mediaFiles']:
                        mf = DBInterface.MediaFile.get(guid)
                        mf = json.loads(mf.dumps())
                        for t in mf['videoTracks']:
                            refs = []
                            for ref_guid in t['refs']:
                                ref_mf: MediaFile = DBInterface.MediaFile.get(ref_guid)
                                refs.append(ref_mf.source.url)
                            t['refs'] = refs
                        # if isinstance(mf['audioTracks'], list):
                        for t in mf['audioTracks']:
                            refs = []
                            for ref_guid in t['refs']:
                                ref_mf: MediaFile = DBInterface.MediaFile.get(ref_guid)
                                refs.append(ref_mf.source.url)
                            t['refs'] = refs
                        media_files.append(mf)
                    asset['mediaFiles'] = media_files
                    return asset

            class set(meth):
                @staticmethod
                def handler(*args):
                    params = args[0]
                    asset = DBInterface.Asset.set_str(params['asset'])
                    return asset

        # class mediaFile:
        #     class get(meth):
        #         @staticmethod
        #         def handler(*args):
        #             params = args[0]
        #             asset = DBInterface.Asset.get_dict(params['guid'])
        #             return asset

    @staticmethod
    def execute(target, request, client: ApiClient):
        try:
            params = request['params'] if 'params' in request else None
            response = {
                'method': request['method'],
                'id': request['id']
            }
            if target.need_auth and not client.authorized():
                response['error'] = 'not authorized'
            else:
                result = target.handler(params, client)
                response['result'] = result
            Logger.debug('Response: {}\n'.format(pformat(response, indent=0)))
            client.ws_handler.send_message(json.dumps(response, cls=NonJSONSerializibleEncoder))
        except Exception as e:
            Logger.warning('ApiTrix.execute exception: {}\n'.format(e))

    @staticmethod
    def dispatch(message, client: ApiClient):
        Logger.debug('ApiTrix.dispatch({}, {})\n'.format(message, client.data))
        try:
            request = json.loads(message)
        except ValueError as e:
            Logger.warning('{}\n'.format(e))
            return
        try:
            mpath = request['method'].split('.')
            # Pick target method class
            target = ApiTrix.Request
            for m in mpath:
                target = target.__dict__[m]
            # Call handler in parallel thread
            ApiTrix.Pool.submit(ApiTrix.execute, target, request, client)
        except Exception as e:
            Logger.warning('{}\n'.format(e))
            # traceback_debug()
            ApiTrix.Pool.submit(ApiTrix.execute, meth.handler, request, client)

    def new_client(self, client: ApiClient, server):
        Logger.info('Client connected: {} / {}\n'.format(client.addr, client.ws_handler.guid))

    def client_left(self, client: ApiClient, server):
        Logger.info('Client disconnected: {} / {}\n'.format(client.addr, client.ws_handler.guid))

    def message_received(self, client: ApiClient, server, msg):
        self.dispatch(msg, client)



