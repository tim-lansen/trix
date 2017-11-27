# -*- coding: utf-8 -*-

from modules.utils.api_trix import ApiTrix, ApiClient, WebsocketServer
# from modules import websocket_client
from modules.config import TRIX_CONFIG
from pprint import pprint
from modules.utils.log_console import Logger, tracer
from modules.utils.mount_paths import mount_paths

import signal
import json
import sys
import ssl
import threading
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
        'guid': '522c8370-5689-4e1f-8169-c0ec9e905ce9',           ### Interaction guid
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
    redis_data.update_record(inter_server, data['guid'], {'interacted': d})
    # publish
    inter_server.publish(data['guid'], d)
    return {'result': 'success'}


def interaction_get(interaction_id):
    # If interaction is already locked, 'smove' will return False
    if not inter_server.smove('inter_free', 'inter_lock', interaction_id):
        return {'result': 'fail', 'error': {'description': "The interaction is locked or doesn't exist"}}
    inter = inter_server.hgetall(interaction_id)
    inter.update({'guid': interaction_id})
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


# def get_interactions(params, profile):
#     # TODO: implement interactions filtering
#     interactions = DBInterface.Interaction.records()
#     return {'result': interactions}


def get_interaction(params, profile):
    interaction = DBInterface.Interaction.get(params['guid'])
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


# API_METHOD_VECTORS = {
#     'get_interactions'   : get_interactions,
#     'get_interaction'    : get_interaction,
#     'submit_interaction' : submit_interaction,
#     'cancel_interaction' : cancel_interaction,
#     'cancel_all_interactions' : cancel_all_interactions,
#     'get_tasks'          : get_tasks
# }


if __name__ == "__main__":
    Logger.set_console_level(Logger.LogLevel.TRACE)
    mount_paths({'watch'})
    api_server = WebsocketServer(port=TRIX_CONFIG.apiServer.port, host='0.0.0.0', apiClass=ApiTrix, clientClass=ApiClient)
    api_server.serve_forever()
