# -*- coding: utf-8 -*-
# The Trix API
# Each request must contain 'method': <method name>, 'guid': <request guid>
# Method data should be in 'data': {<method data>}
# Methods may be cascaded: interaction.getList.filter

import sys
from concurrent.futures import ThreadPoolExecutor
from modules.utils.log_console import Logger, tracer
from modules.utils.database import DBInterface
from modules.utils.jsoner import NonJSONSerializibleEncoder
import time
import json
import threading
from pprint import pformat
from modules.websocket_server import ApiClassBase, ApiClientClassBase, WebsocketServer
from modules.models import Asset, Stream, Collector, MediaFile, Fileset
from modules.utils.job_utils import JobUtils
from modules.utils.watch import Fileset, TRIX_CONFIG
import traceback


# def traceback_debug():
#     Logger.debug('===traceback===\n')
#     for frame in traceback.extract_tb(sys.exc_info()[2]):
#         Logger.debug('{}\n'.format(frame))
#     Logger.debug('===============\n')


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
            Logger.debug('{}\n'.format(data), Logger.LogLevel.LOG_NOTICE)

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
            class lock(meth):
                @staticmethod
                def handler(*args):
                    return DBInterface.Interaction.lock(args[0]['guid'])

            class unlock(meth):
                @staticmethod
                def handler(*args):
                    return DBInterface.Interaction.unlock(args[0]['guid'])

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
                    # TODO: archive interaction

                    # New asset from interaction result
                    asset: Asset = Asset()
                    asset.update_json(args[0]['asset'])
                    Logger.debug('{}\n'.format(asset.dumps(indent=2)), Logger.LogLevel.LOG_NOTICE)
                    JobUtils.CreateJob.create_archive_with_asset(asset)
                    return True

        class asset:
            class get(meth):
                @staticmethod
                def handler(*args):
                    params = args[0]
                    asset = DBInterface.Asset.get_dict(params['guid'])
                    return asset

            class get_expanded(meth):
                @staticmethod
                def _preview_guid_to_url_(mf: MediaFile):
                    for t in mf.videoTracks:
                        previews = []
                        for preview_guid in t.previews:
                            Logger.debug('Get preview media file: {}\n'.format(preview_guid), Logger.LogLevel.LOG_NOTICE)
                            preview_mf: MediaFile = DBInterface.MediaFile.get(preview_guid)
                            previews.append(preview_mf.source.url)
                        t.previews = previews
                    for t in mf.audioTracks:
                        previews = []
                        for preview_guid in t.previews:
                            preview_mf: MediaFile = DBInterface.MediaFile.get(preview_guid)
                            previews.append(preview_mf.source.url)
                        t.previews = previews
                    for t in mf.subTracks:
                        previews = []
                        for preview_guid in t.previews:
                            preview_mf: MediaFile = DBInterface.MediaFile.get(preview_guid)
                            previews.append(preview_mf.source.url)
                        t.previews = previews

                # Load MediaFile(s) objects in place of their GUIDs, and source urls of previews in place of their guids
                @staticmethod
                def handler(*args):
                    params = args[0]
                    asset: Asset = DBInterface.Asset.get_dict(params['guid'])
                    # Collect mediafiles
                    media_files = []
                    media_files_extra = []
                    for guid in asset['mediaFiles']:
                        mf = DBInterface.MediaFile.get(guid)
                        ApiTrix.Request.asset.get_expanded._preview_guid_to_url_(mf)
                        media_files.append(json.loads(mf.dumps()))
                    if type(asset['mediaFilesExtra']) is list:
                        for guid in asset['mediaFilesExtra']:
                            mf = DBInterface.MediaFile.get(guid)
                            if mf is None:
                                Logger.warning('MediaFile {} is not registered\n'.format(guid))
                            else:
                                ApiTrix.Request.asset.get_expanded._preview_guid_to_url_(mf)
                                media_files_extra.append(json.loads(mf.dumps()))
                    asset['mediaFiles'] = media_files
                    asset['mediaFilesExtra'] = media_files_extra
                    # Collect collectors, add them to the asset
                    collectors = []

                    if 'videoStreams' in asset and type(asset['videoStreams']) is list:
                        collectors += DBInterface.Collector.records([_['collector'] for _ in asset['videoStreams'] if 'collector' in _])
                    if 'audioStreams' in asset and type(asset['audioStreams']) is list:
                        collectors += DBInterface.Collector.records([_['collector'] for _ in asset['audioStreams'] if 'collector' in _])
                    if 'subStreams' in asset and type(asset['subStreams']) is list:
                        collectors += DBInterface.Collector.records([_['collector'] for _ in asset['subStreams'] if 'collector' in _])
                    cmap = {}
                    for c in collectors:
                        cc: Collector = Collector()
                        cc.update_json(c)
                        cmap[str(cc.guid)] = json.loads(cc.dumps())
                    Logger.debug('{}\n'.format(cmap), Logger.LogLevel.LOG_NOTICE)
                    mfex_map = {}
                    for mfex in media_files_extra:
                        mfex_map[mfex['guid']] = mfex

                    def mfindex(atindex):
                        for _i, _mf in enumerate(asset['mediaFiles']):
                            if atindex < len(_mf['audioTracks']):
                                return _i, atindex
                            atindex -= len(_mf['audioTracks'])
                        return None, None

                    # Copy audio scan info from collectors to mediafile's tracks
                    mf_changed = set([])
                    if 'audioStreams' in asset and type(asset['audioStreams']) is list:
                        for asi, astr in enumerate(asset['audioStreams']):
                            astr_index = astr['channels'][0]['src_stream_index']
                            mf_index, tr_index = mfindex(astr_index)
                            if mf_index is not None:
                                mf = media_files[mf_index]
                                coll = cmap[astr['collector']]
                                mf['audioTracks'][tr_index]['astats'] = coll['audioResults']['astats']
                                mf_changed.add(mf['guid'])

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

        class fileset:
            class getList(meth):
                @staticmethod
                def handler(*args):
                    fsdb = DBInterface.Fileset.records_fields(Fileset.FIELDS_FOR_LIST)
                    return fsdb

            class get(meth):
                @staticmethod
                def handler(*args):
                    fsdb = DBInterface.Fileset.get_dict(args[0]['guid'])
                    return fsdb

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
            Logger.traceback(Logger.LogLevel.LOG_WARNING)

    @staticmethod
    def dispatch(message, client: ApiClient):
        Logger.debug('ApiTrix.dispatch({}, {})\n'.format(message, client.data))
        try:
            request = json.loads(message)
        except ValueError as e:
            Logger.warning('{}\n'.format(e))
            Logger.traceback(Logger.LogLevel.LOG_WARNING)
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
            Logger.debug('{}\n'.format(e), Logger.LogLevel.LOG_INFO)
            Logger.traceback(Logger.LogLevel.LOG_DEBUG, Logger.LogLevel.LOG_INFO)
            ApiTrix.Pool.submit(ApiTrix.execute, meth, request, client)

    def new_client(self, client: ApiClient, server):
        Logger.info('Client connected: {} / {}\n'.format(client.addr, client.ws_handler.guid))

    def client_left(self, client: ApiClient, server):
        Logger.info('Client disconnected: {} / {}\n'.format(client.addr, client.ws_handler.guid))

    def message_received(self, client: ApiClient, server, msg):
        self.dispatch(msg, client)



