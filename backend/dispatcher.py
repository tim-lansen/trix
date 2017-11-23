# -*- coding: utf-8 -*-
# tim.lansen@gmail.com

# Workers monitor
# Periodically pings workers, checks their statuses and unregisters in case of pong timeout

import time
from modules.models import Task, Job, Node
from modules.utils.log_console import Logger
from modules.utils.database import DBInterface


# 1. Get all NEW jobs
# 1. Get all nodes -> nodes1
# 3. Offer jobs to idle nodes
# 2. Send 'ping' notifications
# 3. Pause
# 4. Get all nodes -> list2
# 5. If list2[node].mtime - list1[node].mtime > timeout: remove node; remove it from list2
# 6. list2 -> list1
# 7. Goto 1


MAX_PARALLEL_TASKS = 3


def dispatch(nodes, jobs):
    """

    :param dobj: {'jobs': [jobs], 'nodes': [nodes], 'notifications': [notifications]}
    :return:
    """
    notifications = []
    while len(jobs) and len(nodes):
        node = nodes.pop(-1)
        job = jobs.pop(0)
        # if test_job_condition(job):
        if not DBInterface.Job.set_status(job['guid'], Job.Status.OFFERED):
            Logger.warning('Failed to change job status\n')
            continue
        notifications.append([node['channel'], 'offer {}'.format(job['guid'])])
    if len(notifications):
        DBInterface.notify_list(notifications)


def run(period=5):
    def test_job_condition(_job_):
        # First, check dependencies
        _dog_ = _job_['dependsongroupid']
        if _dog_ is not None and _dog_ != '00000000-0000-0000-0000-000000000000':
            # Job depends on group
            # Request jobs included to the group and have status != FINISHED
            _jobs_ = DBInterface.get_records(
                'Job',
                fields=['status'],
                cond=[
                    "'{}'=ANY(groupids)".format(_dog_),
                    "guid<>'{}'".format(_dog_),
                    "status<>{}".format(Job.Status.FINISHED)
                ]
            )
            if len(_jobs_):
                return False
        # Check condition
        # if 'condition' in _job_:
        #     _c_ = _job_['condition']
        #     if _c_ is None:
        #         return True
        return True

    def archive_job(uid):
        # TODO: Archive job
        # Remove job from DB
        Logger.log('Archive job: {}\n'.format(uid))
        # DBInterface.Job.delete(uid)

    while True:

        tasks = DBInterface.get_records('Task', fields=['guid'], status=Task.Status.EXECUTING, sort=['ctime'])
        task_slots = MAX_PARALLEL_TASKS - len(tasks)
        # Get idle nodes
        nodes = DBInterface.get_records('Node', fields=['guid', 'channel'], status=Node.Status.IDLE)

        for task in tasks:
            # Check if task have no pending jobs
            jobs = DBInterface.get_records(
                'Job',
                fields=['guid'],
                status=[Job.Status.NEW, Job.Status.WAITING, Job.Status.OFFERED, Job.Status.EXECUTING, Job.Status.FAILED],
                cond=["task='{}'".format(task['guid'])]
            )
            if len(jobs) == 0:
                DBInterface.Task.set_status(task['guid'], Task.Status.FINISHED)
                continue

            # Get all NEW jobs, change their status to WAITING if condition test is True
            jobs = DBInterface.get_records('Job', fields=['guid', 'dependsongroupid', 'condition'], status=Job.Status.NEW, cond=["task='{}'".format(task['guid'])])
            for job in jobs:
                if test_job_condition(job):
                    DBInterface.Job.set_status(job['guid'], Job.Status.WAITING)

            # Monitor jobs: there must not be OFFERED jobs, FINISHED jobs must be archived, FAILED jobs must be relaunched
            jobs = DBInterface.get_records(
                'Job',
                fields=['guid', 'status', 'fails', 'offers'],
                status=[Job.Status.OFFERED, Job.Status.FAILED]
            )
            for job in jobs:
                if job['status'] == Job.Status.OFFERED:
                    # Something wrong happened during offer, reset status to WAITING
                    DBInterface.Job.set_fields(job['guid'], {'status': Job.Status.WAITING, 'offers': job['offers'] + 1})
                elif job['status'] == Job.Status.FAILED:
                    # Job execution failed, reset status to NEW
                    DBInterface.Job.set_fields(job['guid'], {'status': Job.Status.NEW, 'offers': job['fails'] + 1})

            # Get waiting jobs
            task_jobs = DBInterface.get_records('Job', fields=['guid'], status=Job.Status.WAITING, cond=["task='{}'".format(task['guid'])], sort=['priority'])
            dispatch(nodes, task_jobs)

        if task_slots > 0:
            tasks = DBInterface.get_records('Task', fields=['guid'], status=Task.Status.WAITING, sort=['priority', 'ctime'], limit=task_slots)
            for task in tasks:
                DBInterface.Task.set_status(task['guid'], Task.Status.EXECUTING)

        # Get all WAITING jobs sorted by priority and creation time, and IDLE nodes
        # jobs = DBInterface.get_records('Job', fields=['guid'], status=Job.Status.WAITING, sort=['priority', 'ctime'])

        # Monitor nodes
        nodes = DBInterface.get_records('Node', ['mtime', 'guid', 'channel'])
        if len(nodes):
            notifications = [[n['channel'], 'ping'] for n in nodes]
            DBInterface.notify_list(notifications)
            time.sleep(period)
            check = "EXTRACT(EPOCH FROM AGE(localtimestamp, mtime))>{timeout}".format(timeout=5*period)
            suspicious_nodes = DBInterface.get_records('Node', fields=['guid', 'job'], cond=[check])
            if len(suspicious_nodes):
                Logger.warning("Unregister node(s):\n{}\n".format('\n'.join([str(sn['guid']) for sn in suspicious_nodes])))
                DBInterface.delete_records('Node', [sn['guid'] for sn in suspicious_nodes])
                Logger.info("Check jobs were being executed on these nodes...\n")
                jobs = DBInterface.get_records(
                    'Job',
                    fields=['guid', 'fails'],
                    status=Job.Status.EXECUTING,
                    # use str() for sn['job'] to convert UUID() to string
                    cond=["guid=ANY('{{{}}}'::uuid[])".format(','.join([str(sn['job']) for sn in suspicious_nodes if sn['job']]))]
                )
                for job in jobs:
                    Logger.info('Reset job {}\n'.format(job['guid']))
                    DBInterface.Job.set_fields(job['guid'], {'status': Job.Status.NEW, 'offers': job['fails'] + 1})
                time.sleep(period)
        else:
            time.sleep(period)


if __name__ == '__main__':
    run()
