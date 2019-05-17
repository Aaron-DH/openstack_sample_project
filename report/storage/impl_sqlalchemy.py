#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""SQLAlchemy storage backend."""

from __future__ import absolute_import
import os

from oslo_config import cfg
from oslo_log import log
from oslo_db.sqlalchemy import session as db_session

from report.storage.sqlalchemy import models
from report.storage import base
import datetime
from oslo_utils import timeutils


LOG = log.getLogger(__name__)


class Connection(base.Connection):

    def __init__(self, url):
        # Set max_retries to 0, since oslo.db in certain cases may attempt
        # to retry making the db connection retried max_retries ^ 2 times
        # in failure case and db reconnection has already been implemented
        # in storage.__init__.get_connection_from_config function
        options = dict(cfg.CONF.database.items())
        options['max_retries'] = 0
        self._engine_facade = db_session.EngineFacade(url, **options)

    def upgrade(self):
        # NOTE(gordc): to minimise memory, only import migration when needed
        from oslo_db.sqlalchemy import migration
        path = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            'sqlalchemy', 'migrate_repo')
        migration.db_sync(self._engine_facade.get_engine(), path)

    def clear(self):
        engine = self._engine_facade.get_engine()
        for table in reversed(models.Base.metadata.sorted_tables):
            engine.execute(table.delete())
        self._engine_facade._session_maker.close_all()
        engine.dispose()

    def get_rpttasks(self, time_s=None, time_e=None, task_id=None, task_name
                     =None, task_type=None,task_status=None,task_updatetime=None):
        tasklist = []
        session = self._engine_facade.get_session()
        query = session.query(models.ReportTasks)
        if task_id is not None:
            query = query.filter(models.ReportTasks.task_id == task_id)
        elif task_name is not None:
            query = query.filter(models.ReportTasks.task_name == task_name)
        elif task_type is not None:
            query = query.filter(models.ReportTasks.task_type == task_type)
        elif task_status is not None:
            query = query.filter(models.ReportTasks.task_status == task_status)
        elif time_s and time_e:
            query = query.filter(models.ReportTasks.task_updatetime > time_s).\
                filter(models.ReportTasks.task_updatetime <= time_e)

        for x in query.all():
            tasklist.append(x.to_dict())

        return tasklist

    def add_rpttask(self, task):
        session = self._engine_facade.get_session()
        task_row = models.ReportTasks(task_id=task['task_id'])
        task_row.update(task)
        with session.begin():
            session.add(task_row)
        return task_row

    def update_rpttask(self, task):
        session = self._engine_facade.get_session()
        task_row = models.ReportTasks(task_id=task['task_id'])
        task_row.update(task)
        with session.begin():
            session.merge(task_row)
        return task_row

    def del_rpttask(self, task_id):
        session = self._engine_facade.get_session()
        with session.begin():
            session.query(models.ReportTasks).filter(
                models.ReportTasks.task_id == task_id).delete()

    def add_rptfile(self, file):
        session = self._engine_facade.get_session()
        file_row = models.ReportFiles(file_id=file['file_id'])
        file_row.update(file)
        with session.begin():
            session.add(file_row)
        return file_row

    def get_rptfiles(self, task_id=None, task_type=None, task_period=None, file_id=None):
        filelist = []
        session = self._engine_facade.get_session()
        query = session.query(models.ReportFiles)
        # if task_type and task_period:
        #    query = query.filter(models.ReportFiles.task_type == task_type).\
        #        filter(models.ReportFiles.task_period == task_period)

        if task_period and task_type:
            query = query.filter(models.ReportFiles.task_period == task_period).\
                filter(models.ReportFiles.task_type == task_type)

        if task_id:
            query = query.filter(models.ReportFiles.task_id == task_id)

        if file_id:
            query = query.filter(models.ReportFiles.file_id == file_id)

        for x in query.all():
            filelist.append(x.to_dict())

        return filelist

    def del_rptfiles(self, file_id):
        session = self._engine_facade.get_session()
        with session.begin():
            session.query(models.ReportFiles).filter(
                models.ReportFiles.file_id == file_id).delete()
