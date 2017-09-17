# -*- coding: utf-8 -*-
# tim.lansen@gmail.com


from modules.utils.job_utils import JobUtils


def test_job_utils_ingest_prepare():
    JobUtils.CreateJob.ingest_prepare_sliced('/mnt/server1_id/crude/watch/test.src.av')


if __name__ == '__main__':
    test_job_utils_ingest_prepare()

