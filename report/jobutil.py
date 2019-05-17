
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from oslo_log import log

from apscheduler.events import *
from oslo_config import cfg

aps_job_opts = [
    cfg.IntOpt('misfire_grace_time',
                default=1800),
    cfg.BoolOpt('coalesce',
                default=False),
    cfg.IntOpt('max_instances',
                default=100),
]
aps_executor_opts = [
    cfg.IntOpt('ThreadPoolExecutor',
               default=12),
    cfg.IntOpt('ProcessPoolExecutor',
               default=4),
]
CONF = cfg.CONF
CONF.register_opts(aps_job_opts, group='apscheduler')
CONF.register_opts(aps_executor_opts, group='apscheduler')

LOG = log.getLogger(__name__)

JOB_DEFAULTS = {
    'misfire_grace_time': CONF.apscheduler.misfire_grace_time,
    'coalesce': CONF.apscheduler.coalesce,
    'max_instances': CONF.apscheduler.max_instances
}

EXECUTORS = {
    'default': ThreadPoolExecutor(CONF.apscheduler.ThreadPoolExecutor),
    'processpool': ProcessPoolExecutor(CONF.apscheduler.ProcessPoolExecutor)
}


class JobManager(object):
    def __init__(self):
        self.scheduler = BackgroundScheduler(executors=EXECUTORS,
                                             job_defaults=JOB_DEFAULTS,
                                             timezone='Asia/Shanghai')
        self.jobs = {}
        self.scheduler.start()

    def add_job_store(self):
        pass

    def add_job(self, method, jobtype, trigger, jobid, args=None, kwargs=None):
        job = None
        if jobtype == 'interval':
            job = self.scheduler.add_job(method, 'interval', seconds=trigger,
                                         id=jobid, args=args, kwargs=kwargs)

        if jobtype == 'cron':
            Trigger = CronTrigger(**trigger)
            job = self.scheduler.add_job(method, Trigger,
                                         id=jobid, args=args, kwargs=kwargs)

        if jobtype == 'once':
            job = self.scheduler.add_job(method, 'date', run_date=trigger,
                                         id=jobid, args=args, kwargs=kwargs)

        LOG.debug("add job: %s", jobid)
        if job is not None:
            self.jobs[jobid] = job

    def delete_job(self, jobid):
        if jobid in self.jobs:
            self.scheduler.remove_job(jobid)
            del self.jobs[jobid]

    def disable_job(self, jobid):
        if jobid in self.jobs:
            self.scheduler.pause_job(jobid)

    def enable_job(self, jobid):
        if jobid in self.jobs:
            self.scheduler.resume_job(jobid)

    def get_job_next_run_time(self, jobid):
        job = self.scheduler.get_job(jobid)

        if not job:
            return None

        next_run_time = job.next_run_time

        return next_run_time.strftime("%Y-%m-%d %H:%M:%S")
        #return next_run_time
