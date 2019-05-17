from datetime import datetime

from oslo_config import cfg
from oslo_log import log
from report.openstack.common import service as os_service
from report import storage
from report.agent import default_tasks
from report.agent.tasks import Task
from report.jobutil import JobManager


LOG = log.getLogger(__name__)


class AgentManager(os_service.Service):

    def __init__(self):
        super(AgentManager, self).__init__()
        self.jobmanager = JobManager()
        self.conn = storage.get_connection_from_config(cfg.CONF)
        self.add_default_tasks(default_tasks.default_tasks)
        self.inittasks()

    def inittasks(self):
        tasklist = self.conn.get_rpttasks()

        for rpttask in tasklist:
            LOG.debug("Add task from db,named %s" % rpttask['task_name'])
            self._add_task(rpttask)

    def add_default_tasks(self, default_tasks):
        for task in default_tasks:
            if not self.conn.get_rpttasks(task_id=task['task_id']):
                self.conn.add_rpttask(task)

    def _add_task(self, task):
        next_rtime = None
        if task['task_status'] == 'Active':
            taskobj = Task.generator_task(task, self.conn)
            next_rtime = self.add_task_toJob(taskobj)
            # taskobj.start()

        task['task_next_rtime'] = next_rtime
        self.conn.update_rpttask(task)

    def add_task(self, ctx, task):
        self._add_task(task)

    def update_task(self, ctx, task):
        task_id = task['task_id']
        self.jobmanager.delete_job(task_id)
        self._add_task(task)

    def del_task(self, ctx, task_id):
        self.conn.del_rpttask(task_id)
        self.jobmanager.delete_job(task_id)

    def enable_task(self, ctx, task):
        task_id = task['task_id']
        self.jobmanager.delete_job(task_id)
        task['task_status'] = 'Active'
        self._add_task(task)
        """
        self.jobmanager.enable_job(task_id)
        task_next_rtime = self.jobmanager.get_job_next_run_time(task_id)
        task['task_next_rtime'] = task_next_rtime
        task['task_updatetime'] = datetime.now()
        self.conn.update_rpttask(task)
        """

    def disable_task(self, ctx, task):
        task_id = task['task_id']
        self.jobmanager.disable_job(task_id)
        task['task_status'] = 'Inactive'
        task['task_next_rtime'] = None
        task['task_updatetime'] = datetime.now()
        self.conn.update_rpttask(task)

    def get_next_run_time(self, ctx, task_id):
        return self.jobmanager.get_job_next_run_time(task_id)

    def add_task_toJob(self, rpttask):
        jobid = rpttask.task_id
        jobtype = rpttask.task_schedule_type
        jobtrigger = rpttask.trigger
        self.jobmanager.add_job(rpttask.start,
                                jobtype,
                                jobtrigger,
                                jobid)

        return self.jobmanager.get_job_next_run_time(jobid)
