# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

import re
import json
from modules.models.job import Job
from .log_console import Logger


# Assume that text is a regular JSON string
def resolve_aliases(params):
    collection: dict = params['collection']
    text: str = params['text']
    resolved = 0
    missed = 0
    while True:
        aliases = set(re.findall(r'\${([a-zA-Z0-9\-_]+?)}', text))
        if len(aliases) == missed:
            break
        missed = 0
        for v in aliases:
            if v in collection:
                text = text.replace('${{{0}}}'.format(v), collection[v])
                resolved += 1
            else:
                missed += 1
                Logger.warning('resolve_aliases: {0} value not found\n'.format(v))
                # post-replace loop to resolve inherited links
    # params['resolved'] = resolved
    if resolved > 0:
        params['json'] = json.loads(text)
    return resolved


def resolve_job_aliases(job: Job):
    aliases = job.info.aliases
    if aliases is None or len(aliases) == 0:
        return
        # aliases = {}
    # aliases['src_asset'] = job.info.src_asset
    # aliases['dst_asset'] = job.info.dst_asset
    params = {
        'collection': aliases,
        'text': json.dumps(aliases)
    }
    if resolve_aliases(params):
        aliases = params['json']
    job.info.aliases = aliases

    # Scan job.info.steps
    for i, step in enumerate(job.info.steps):
        params = {
            'collection': aliases,
            'text': step.dumps()
        }
        if resolve_aliases(params):
            step_new = Job.Info.Step()
            step_new.update_json(params['json'])
            job.info.steps[i] = step_new


# Testing Job class initialization and alias resolving
def test():
    job = Job()
    initial = '''
{
  "guid": "3631f021-8dd0-4197-a29d-27fc3180a242",
  "name": "Test job",
  "type": "encode",
  "info": {
    "src_asset": "f22ba38e-7c50-4760-81c9-d8b3a4724fc1",
    "dst_asset": "f22ba38e-7c50-4760-81c9-d8b3a4724fc3",
    "aliases": {
      "temp": "/tmp/${dst_asset}",
      "alias": "Disney.Frozen",
      "p_fv1": "${temp}/${alias}.fv1.sox",
      "p_fv2": "${temp}/${alias}.fv2.sox",
      "p_bv1": "${temp}/${alias}.bv1.sox",
      "p_bv2": "${temp}/${alias}.bv2.sox",
      "p_lf1": "${temp}/${alias}.lf1.sox",
      "p_lf2": "${temp}/${alias}.lf2.sox",
      "p_FLFR": "${temp}/${alias}.FLFR.sox",
      "p_BLBR": "${temp}/${alias}.BLBR.sox",
      "p_LFE": "${temp}/${alias}.LFE.sox",
      "p_FC": "${temp}/${alias}.FC.sox",
      "f_src": "/mnt/SAS_vol1/Source-01/Fox/Epic/${src_asset}@AT_movie_audio@lang_rus@CL_stereo.ac3",
      "f_tmp": "${temp}/${dst_asset}.5.1.aac",
      "f_dst": "/mnt/SAS_vol1/Production-01/Fox/Epic/${dst_asset}@AT_movie_audio@CL_5.1@lang_rus@job1.mp4"
    },
    "steps": [
      {
        "name": "Convert audio stereo -> 5.1",
        "weight": 1.0,
        "pipes": [
          "${p_fv1}", "${p_fv2}", "${p_bv1}", "${p_bv2}", "${p_lf1}", "${p_lf2}", "${p_FLFR}", "${p_BLBR}", "${p_LFE}", "${p_FC}"
        ],
        "chains": [
          {
            "procs": [
              ["ffmpeg", "-loglevel", "error", "-stats", "-y", "-i", "${f_src}", "-t", "600", "-acodec", "pcm_s32le", "-f", "sox", "-"],
              ["sox", "-t", "sox", "-", "-t", "sox", "${p_fv1}", "remix", "1v0.5,2v-0.5", "sinc", "-p", "10", "-t", "5", "100-3500", "-t", "10"]
            ],
            "return_codes": [[0, 2], [0]],
            "progress": {
              "capture": 0,
              "parser": "ffmpeg",
              "top": 600.0
            }
          }
        ]
      },
      {
        "name": "Rewrap audio to mp4",
        "weight": 0.1,
        "chains": [
          {
            "procs": [
              ["MP4Box", "-out", "${f_dst}", "-tmp", "${temp}", "-new", "/dev/null", "-add", "${f_tmp}#audio"]
            ],
            "return_codes": [[0]],
            "progress": {
              "capture": 0,
              "parser": "mp4box",
              "top": 100.0
            }
          }
        ]
      }
    ]
  }
}

    '''
    job.update_str(initial)
    resolve_job_aliases(job)
    print(job.dumps(indent=2))



