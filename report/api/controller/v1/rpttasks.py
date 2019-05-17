# -*-coding:utf-8-*-
import uuid
import time
import json
from datetime import datetime

import pecan
import wsme
import operator
from oslo_log import log
from pecan import rest
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from report.api.controller import resource
from report.agent import rpcapi as rpcclient
from report import context
from report.i18n import _
from report.agent import task_content

TASK_TYPES = wtypes.Enum(str, 'alarm', 'monitor', 'meter')
PERIOD_TYPES = wtypes.Enum(str, 'month', 'week', 'day')
TASK_STATUS = wtypes.Enum(str, 'Active', 'Inactive')
TASK_LANGUAGE = wtypes.Enum(str, 'Chinese', 'English')

LOG = log.getLogger(__name__)

meter_list = ["user_statistics", "vm_statistics"]
alarm_list = ["host distribute", "user distribute", "status distribute",
              "type distribute","severity distribute","time distribute",
              "response time distribute"]
monitor_list = ['node.cpu.total.percent', 'node.mem.percent',
                'node.swap.percent', 'partition.percent']


class ReportTask(resource.Base):
    """ One Report Task Description"""

    "ID of the task"
    task_id = wsme.wsattr(wtypes.text)

    "The unique name of the task"
    task_name = wsme.wsattr(wtypes.text, mandatory=True)

    "The type of the task"
    task_type = wsme.wsattr(TASK_TYPES, mandatory=True)

    "The period of the task, one of ['month', 'week', 'day']"
    task_period = wsme.wsattr(PERIOD_TYPES, mandatory=True)

    "The content of the task, include hostlist and meter list"
    task_content = wsme.wsattr(wtypes.text, default='{}')

    "The excute time of the task"
    "for once: datetime"
    "for other: {'month':1, 'day_of_week':1, 'day':1, 'hour':1}"
    task_time = wsme.wsattr(wtypes.text)

    "The timerange for collector data of the task"
    task_timerange = wsme.wsattr(wtypes.text)

    "The metadata of the task, include filetype,sendmail"
    task_metadata = wsme.wsattr(wtypes.text, default='{}')

    "The createtime of the task"
    task_createtime = datetime

    "The updatetime of the task"
    task_updatetime = datetime

    "The status of the task, one of ['Active', 'Inactive']"
    task_status = wsme.wsattr(TASK_STATUS, default='Active')

    "The language of the file created by task"
    task_language = wsme.wsattr(TASK_LANGUAGE, default='Chinese')

    "Next run time of the task"
    task_next_rtime = datetime

    def __init__(self, **kwargs):
        super(ReportTask, self).__init__(**kwargs)

    @staticmethod
    def validate(reporttask):
        paramdata = {}
        paramdata['task_name'] = reporttask.task_name
        paramdata['task_type'] = reporttask.task_type
        paramdata['task_period'] = reporttask.task_period
        paramdata['task_language'] = reporttask.task_language
        paramdata['task_content'] = reporttask.task_content
        paramdata['task_status'] = reporttask.task_status
        paramdata['task_metadata'] = reporttask.task_metadata
        for k, value in paramdata.items():
            if value != wtypes.Unset:
                if not value:
                    raise wsme.exc.ClientSideError(
                            _("Error in posting task:"
                            "parameter '%s' is null") % k
                            )
        paramdata['task_id'] = reporttask.task_id
        paramdata['task_time'] = reporttask.task_time
        for k, value in paramdata.items():
            if value != wtypes.Unset:
                if len(value) >= 256:
                    raise wsme.exc.ClientSideError(
                            _("Error in posting task:"
                              "parameter '%s' is too long, 255 limited") % k
                              )

        try:
            paramdata['task_content'] =  json.loads(paramdata['task_content'])
            paramdata['task_metadata'] = json.loads(paramdata['task_metadata'])
        except Exception as e:
            raise wsme.exc.ClientSideError(
                     _("Add the task failed, format error."),
                     500)
        content_type = paramdata['task_content'].get('meterlist', [])

        if content_type == [] or type(content_type) != list:
            raise wsme.exc.ClientSideError(
                    _("task_content format error.")
                    )

        if paramdata['task_type'] == 'meter':
            report_list = meter_list
        elif paramdata['task_type'] == 'monitor':
            report_list = monitor_list
        else:
            report_list = alarm_list

        if not set(content_type).issubset(set(report_list)):
            raise wsme.exc.ClientSideError(
                    _("task_content content error.")
                    )

        return reporttask


class RptTasksController(rest.RestController):

    _custom_actions = {
        'enable': ['PUT'],
        'disable': ['PUT'],
        'content': ['GET'],
        'dels':['PUT'],
    }

    def __init__(self):
        self.rpcclient = rpcclient.AgentAPI()
        super(RptTasksController, self).__init__()

    @wsme_pecan.wsexpose(ReportTask, wtypes.text)
    def get(self, task_id):
        conn = pecan.request.storage_conn
        rpttasks = conn.get_rpttasks(task_id=task_id)
        ctx = context.RequestContext()
        task_next_time = self.rpcclient.get_next_run_time(ctx,task_id=task_id)
        if task_next_time:
            rpttasks[0]['task_next_rtime'] = datetime.strptime(str(task_next_time), "%Y-%m-%d %H:%M:%S")
        else:
            rpttasks[0]['task_next_rtime'] = None

        if not rpttasks:
            LOG.error("Fail to get task %s." % task_id)
            raise wsme.exc.ClientSideError("Reporttask with id=%s not exsit"
                                           % task_id, 404)

        return ReportTask.from_dict(rpttasks[0])

    @wsme_pecan.wsexpose([ReportTask], datetime, datetime)
    def get_all(self, time_s=None, time_e=None):
        result = []
        ctx = context.RequestContext()
        conn = pecan.request.storage_conn
        rpttasks = conn.get_rpttasks(time_s, time_e)
        rpttasks.sort(key=operator.itemgetter('task_createtime'),reverse=True)
        for task in rpttasks:
            result.append(ReportTask.from_dict(task))
        return result

    @wsme_pecan.wsexpose(ReportTask, body=ReportTask)
    def post(self, data):
        ctx = context.RequestContext()
        conn = pecan.request.storage_conn

        tasks = list(conn.get_rpttasks(task_name=data.task_name,
                                       ))

        if tasks:
            raise wsme.exc.ClientSideError(
                _("Task with task_name='%s' exists") %
                (data.task_name),
                409)

        data = data.to_dict()

        now = datetime.now()
        data['task_createtime'] = datetime.now()
        data['task_updatetime'] = datetime.now()
        data['task_id'] = str(uuid.uuid4())

        try:
            conn.add_rpttask(data)
        except Exception as e:
            raise wsme.exc.ClientSideError(
                _("Add the task failed, catch exception: %s") %
                data.task_name,
                500)

        self.rpcclient.add_task(ctx, task=data)

        # sleep 1s and wait for agent update db
        time.sleep(1)

        task_now = conn.get_rpttasks(task_id=data['task_id'])
        return ReportTask.from_dict(task_now[0])

    @wsme_pecan.wsexpose(ReportTask, wtypes.text, body=wtypes.text)
    # body=wtypes.DictType(wtypes.text,wtypes.text)
    def put(self, task_id, data):
        """Update a task"""
        conn = pecan.request.storage_conn
        tasks = conn.get_rpttasks(task_id=task_id)
        if not tasks:
            LOG.error("Fail to get task %s." % task_id)
            raise wsme.exc.ClientSideError(
                _("Reporttask with task_id=%s not exsit") %
                task_id,
                404)
        data['task_updatetime'] = datetime.now()

        def _update(task):
            task_content = json.loads(task.get('task_content'))
            task_metadata = json.loads(task.get('task_metadata'))
            for key in data.keys():
                if task.get(key):
                    task[key] = data.pop(key)
                # elif task_content.get(key):
                #   task_content[key] = data.pop(key)
                # elif task_metadata.get(key):
                #    task_metadata[key] = data.pop(key)

            # task["task_content"] = json.dumps(task_content)
            # task["task_metadata"] = json.dumps(task_metadata)

            return task

        ctx = context.RequestContext()

        task_dict = _update(tasks[0])
        self.rpcclient.update_task(ctx, task_dict)

        # sleep 1s and wait for agent update db
        time.sleep(1)

        task_now = conn.get_rpttasks(task_id=task_id)
        # result = result.append(ReportTask.from_dict(task_now[0]))
        return ReportTask.from_dict(task_now[0])

    @wsme_pecan.wsexpose(wtypes.ArrayType(wtypes.text), wtypes.ArrayType(wtypes.text))
    def dels(self, task_id):
        id_list = []
        for each_id in task_id:
            conn = pecan.request.storage_conn
            id = conn.get_rpttasks(task_id = each_id)
            if not id:
                raise wsme.exc.ClientSideError(
                        _("Task_id %s doesn\'t exist!") %
                        each_id,
                        404)
            ctx = context.RequestContext()
            self.rpcclient.del_task(ctx, task_id=each_id)
            id_list.append(each_id)
        return id_list

    @wsme_pecan.wsexpose(wtypes.ArrayType(wtypes.text), wtypes.ArrayType(wtypes.text))
    # @wsme_pecan.wsexpose(ReportTask, wtypes.text)
    def enable(self, task_id):
        id_list = []
        for each_id in task_id:
            conn = pecan.request.storage_conn
            tasks = conn.get_rpttasks(task_id=each_id)
            if not tasks:
                LOG.error("Fail to get task %s." % each_id)
                raise wsme.exc.ClientSideError(
                    _("Reporttask with task_id=%s not exsit") %
                    each_id,
                    404)

            if tasks[0]['task_status'] == "Active":
                LOG.error("Task with task_id=%s already enabled", each_id)
                raise wsme.exc.ClientSideError(
                    _("Reporttask with task_id=%s already enabled!") %
                    each_id,
                    404)

            ctx = context.RequestContext()
            self.rpcclient.enable_task(ctx, task=tasks[0])

            # sleep 1s and wait for agent update db
            time.sleep(1)

            task_now = conn.get_rpttasks(task_id=each_id)
            id_list.append(each_id)
        return id_list
        # return ReportTask.from_dict(task_now[0])

    @wsme_pecan.wsexpose(wtypes.ArrayType(wtypes.text), wtypes.ArrayType(wtypes.text))
    # @wsme_pecan.wsexpose(ReportTask, wtypes.text)
    def disable(self, task_id):
        id_list = []
        for each_id in task_id:
            conn = pecan.request.storage_conn
            tasks = conn.get_rpttasks(task_id=each_id)
            if not tasks:
                LOG.error("Fail to get task %s." % each_id)
                raise wsme.exc.ClientSideError(
                    _("Reporttask with task_id=%s not exsit") %
                    task_id,
                    404)

            if tasks[0]['task_status'] == "Inactive":
                LOG.error("Task with task_id=%s already disabled", each_id)
                raise wsme.exc.ClientSideError(
                    _("Reporttask with task_id=%s already disabled!") %
                    each_id,
                    404)

            ctx = context.RequestContext()
            self.rpcclient.disable_task(ctx, task=tasks[0])

            # sleep 1s and wait for agent update db
            time.sleep(1)

            task_now = conn.get_rpttasks(task_id=each_id)
            id_list.append(each_id)
        # return ReportTask.from_dict(task_now[0])
        return id_list

    # @wsme_pecan.wsexpose(unicode, wtypes.text)
    # def content(self, tasks_type):
    #    contents = task_content.task_content
    #    return contents[tasks_type]
