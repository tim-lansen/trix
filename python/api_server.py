# -*- coding: utf-8 -*-


from modules.websocket_server import WebsocketServer
from modules import websocket_client
from modules.config import TRIX_CONFIG
from modules.utils import *
from pprint import pprint


# def new_client(client, server):
#     Logger.info("New client connected and was given id {0}\n".format(client['id']))
#     pprint(client)
#     server.send_message_to_all("Hey all, a new client has joined us")
#
#
# def client_left(client, server):
#     print("Client({0}) disconnected".format(client['id']))
#
#
# def message_received(client, server, message):
#     if len(message) > 200:
#         message = message[:200]+'..'
#     print("Client({0}) said: {1}".format(client['id'], message))
#
#
# server = WebsocketServer(port=TRIX_CONFIG.api_server.port, host=TRIX_CONFIG.api_server.host)
# server.set_fn_new_client(new_client)
# server.set_fn_client_left(client_left)
# server.set_fn_message_received(message_received)
# server.run_forever()



import signal
import json
import sys
import ssl
import threading
# import redis
# import redis_data
import uuid
import traceback


def print_traceback():
    print('===traceback===')
    for frame in traceback.extract_tb(sys.exc_info()[2]):
        print(frame)
    print('===============')


def get_all_interactions_sorted():
    ia = redis_data.get_free_interactions(inter_server)
    # Resort interactions
    interactions = redis_data.get_stuff_sorted(ia)
    return {'result': interactions}


def get_all_jobs():
    return redis_data.get_all_jobs(backend)


def get_free_interactions_sorted():
    ia = redis_data.get_free_interactions(inter_server)
    # Resort interactions
    interactions = redis_data.get_stuff_sorted(ia)
    return {'result': interactions}


def interaction_submit(data):
    example = {
        'id': '522c8370-5689-4e1f-8169-c0ec9e905ce9',           ### Interaction id
        'movie_guid': 'e7d90f1f-48f2-4367-9ae5-c2b222240c8c',   ### Movie GUID
        'movie': '21',                                          #   Movie name
        'studio': 'Sony',                                       #   Studio
        'video': {
            'layout': 'mono',                                   #** stereo video format mono|stereo
            'crop': {'x': 0, 'y': 0, 'w': 1920, 'h': 1080},     ### Crop data
            'map': [
                {
                    'disposition': 'center',                    #** center|left|right|TBLR|TBRL|SBS|ILR|IRL
                    'source_index': 0,                          ### Source of type index
                    'in': 0.0,                                  ### In time
                    'out': 6362.123                             ### Out time
                }
            ]
        },
        'audio_map': [                                          ### Audio tracks mapping
            {
                'lang': 'rus',
                'layout': 'stereo',
                'map': ['0', '1'],
                'delay': 0
            },
            {
                'lang': 'eng',
                'layout': '5.1',
                'map': ['2', '3', '4', '5', '6'],
                'delay': -0.3
            }
        ],
        'sample': [             #   Sample data
            [234.4, 40.0],      #   Offset
            [555.7, 40.0],
            [1232.1, 40.0]
        ],
    }
    pprint.pprint(data)
    d = json.dumps(data)
    # update redis record
    redis_data.update_record(inter_server, data['id'], {'interacted': d})
    # publish
    inter_server.publish(data['id'], d)
    return {'result': 'success'}


def interaction_get(interaction_id):
    # If interaction is already locked, 'smove' will return False
    if not inter_server.smove('inter_free', 'inter_lock', interaction_id):
        return {'result': 'fail', 'error': {'description': "The interaction is locked or doesn't exist"}}
    inter = inter_server.hgetall(interaction_id)
    inter.update({'id': interaction_id})
    return {'result': inter}


def interaction_release(interaction_id):
    inter_server.smove('inter_lock', 'inter_free', interaction_id)
    return {'result': 'success'}


def interaction_release_all():
    mems = inter_server.smembers('inter_lock')
    if len(mems):
        pipe = inter_server.pipeline()
        for mem in mems:
            pipe.smove('inter_lock', 'inter_free', mem)
        pipe.execute()
    return {'result': 'success'}


# Method handlers


def get_interactions(params, profile):
    # TODO: implement interactions filtering
    interactions = DBInterface.Interaction.records()
    return {'result': interactions}


def get_interaction(params, profile):
    interaction = DBInterface.Interaction.get(params['id'])
    return {'result': interaction}


def submit_interaction(params, profile):
    if params and 'interaction' in params:
        return interaction_submit(params['interaction'])
    return {}


def cancel_interaction(params, profile):
    if params and 'interaction' in params:
        return interaction_release(params['interaction'])
    return {}


def cancel_all_interactions(params, profile):
    return interaction_release_all()


def get_tasks(params, profile):
    return {}


API_METHOD_VECTORS = {
    'get_interactions'   : get_interactions,
    'get_interaction'    : get_interaction,
    'submit_interaction' : submit_interaction,
    'cancel_interaction' : cancel_interaction,
    'cancel_all_interactions' : cancel_all_interactions,
    'get_tasks'          : get_tasks
}


class ApiClientProfile:

    def __init__(self, ws_handler):
        self.ws_session_id = str(uuid.uuid4())
        self.ws_handler = ws_handler
        # self.phone_number = None
        # self.name = None
        # self.id = None
        # self.device_token = None
        # self.serial_number = None
        # self.authorized = False
        # self.thread = None
        # self.mid = 1
        self.data = {
            'phone_number': None,
            'name': None,
            'profile_id': None,
            'device_token': None,
            'serial_number': None,
            'authorized': False,
            'thread': None,
            'message_id': 1
        }

    def set_info(self, info):

        def _sync_ws_napi_request_(data):
            print('_sync_ws_napi_request_:')
            print(data)
            ws = websocket_client.create_connection('ws://napi.ayyo.ru')
            msg = json.dumps({
                'method': 'connect',
                'id': str(data['message_id']),
                'params': {
                    'version': '2',
                    'device_token': data['device_token'],
                    'application': {
                        'name': 'web_admin',
                        'version': '4.0.1'
                    },
                    'device_info': {
                        'serial_number': data['serial_number'],
                        'type': 'pc',
                        'name': 'PC',
                        'model': 'PC'
                    }
                }
            })
            print(msg)
            ws.send(msg)
            result = json.loads(ws.recv())
            print(result)
            if result['error'] is None and int(result['id']) == data['message_id']:
                data['message_id'] += 1
                msg = json.dumps({
                    'method': 'widgets_all',
                    'id': str(data['message_id']),
                    'params': {}
                })
                ws.send(msg)
                result = json.loads(ws.recv())
                print(result)
                if result['error'] is None and int(result['id']) == data['message_id']:
                    print('Authorized {0}'.format(data['phone_number']))
                    self.data['authorized'] = True
            data['message_id'] += 1
            # pprint.pprint(result)
            data['thread'] = None
            ws.close()

        if self.data['authorized']:
            return
        if self.data['thread'] is not None:
            return
        self.data.update(info)
        t = threading.Thread(target=_sync_ws_napi_request_, args=(self.data,))
        t.run()
        self.data['thread'] = t

    def authorized(self):
        return self.data['authorized']

    def reset(self):
        self.data['profile_id'] = None
        self.data['authorized'] = False


@tracer
def ws_handle_connection(client, server):
    Logger.debug('{0} connected, session_id {1}\n'.format(client.ws_handler.client_address, client.ws_session_id))
    client.reset()


@tracer
def ws_handle_close(client, server):
    Logger.debug('{0} disconnected\n'.format(client.ws_handler.client_address))
    client.reset()


@tracer
def ws_handle_message(client, server, message):
    Logger.debug('ws_handle_message({0})\n'.format(message))
    if message is None:
        message = ''
    try:
        data = json.loads(str(message))
        params = data['params'] if 'params' in data else None
        answer = {'error': None}
        # error = None
        method = data['method']
        if method == 'connect':
            answer['result'] = {'session_id': client.ws_session_id}
        elif method == 'authorize':
            if params['session_id'] == client.ws_session_id:
                print('Authorizing {0}'.format(params['phone_number']))
                client.set_info(params)
            else:
                answer['error'] = {'code': 123, 'text': 'Error while authorizing {0}: SID {1} vs {2}'.format(data['phone_number'], client.session_id, data['session_id'])}
                print(answer['error']['text'])
        elif client.authorized():
            if method in API_METHOD_VECTORS:
                answer.update(API_METHOD_VECTORS[method](params, client))
        #else:
        #    self.sendMessage(str(self.data))
        if params:
            data.pop('params')
        data.update(answer)
        server.send_message(client, json.dumps(data))
    except Exception as n:
        Logger.error('Exception: {}\n'.format(n))
        print_traceback()


if __name__ == "__main__":
    # table_asset = TRIX_CONFIG.dbase.tables['Asset']
    # table_job = TRIX_CONFIG.dbase.tables['Job']
    # table_node = TRIX_CONFIG.dbase.tables['Node']
    # table_interaction = TRIX_CONFIG.dbase.tables['Interaction']

    server = WebsocketServer(port=TRIX_CONFIG.api_server.port, host=TRIX_CONFIG.api_server.host, clientClass=ApiClientProfile)
    server.set_fn_new_client(ws_handle_connection)
    server.set_fn_client_left(ws_handle_close)
    server.set_fn_message_received(ws_handle_message)

    server.serve_forever()
