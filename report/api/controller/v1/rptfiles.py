
import datetime

import os
import wsme
import pecan
from oslo_config import cfg
import operator
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan
from pecan import rest

from urlparse import urlparse
from report.api.controller import resource
from report.i18n import _

CONF = cfg.CONF
CONF.import_opt('rptfile_path', 'report.agent.tasks', group="report_file")
CONF.import_opt('local_url', 'report.agent.tasks', group="report_file")

TASK_TYPES = wtypes.Enum(str, 'alarm', 'monitor', 'meter')
PERIOD_TYPES = wtypes.Enum(str, 'month', 'week', 'day', 'year', 'once')

class ReportFile(resource.Base):
    file_id = wsme.wsattr(wtypes.text, mandatory=False)
    task_id = wsme.wsattr(wtypes.text, mandatory=True)
    task_name = wsme.wsattr(wtypes.text, mandatory=True)
    task_type = wsme.wsattr(TASK_TYPES, mandatory=True)
    task_period = wsme.wsattr(PERIOD_TYPES, mandatory=True)
    file_path = wsme.wsattr(wtypes.text, mandatory=True)
    file_time = datetime.datetime


class RptFilesController(rest.RestController):
    _custom_actions = {
        'download': ['GET'],
    }

    @wsme_pecan.wsexpose([ReportFile], wtypes.text, wtypes.text, wtypes.text)
    def get_all(self, task_id=None, task_type=None, task_period=None):
        result = []
        conn = pecan.request.storage_conn
        rptfiles = conn.get_rptfiles(task_id=task_id, task_type=task_type,
                                     task_period=task_period)
        rptfiles.sort(key=operator.itemgetter('file_time'),reverse=True)
        for rptfile in rptfiles:
            rptfile['file_path'] = CONF.report_file.local_url + rptfile['file_path']
            result.append(ReportFile.from_dict(rptfile))
        return result

    @wsme_pecan.wsexpose(None, wtypes.text, status_code=204)
    def delete(self, file_id):
        conn = pecan.request.storage_conn
        try:
            file_detail = conn.get_rptfiles(file_id=file_id)
            url_path = file_detail[0]['file_path']
            # file_path = CONF.report_file.rptfile_path + urlparse(url_path).path
            file_path = CONF.report_file.rptfile_path + url_path
            os.remove(file_path)
        except:
            # LOG.error("File is already remove")
            raise wsme.exc.ClientSideError(
                _("File with file_id=%s doesn\'t exit!") %
                file_id,
                404)
        conn.del_rptfiles(file_id=file_id)

    """
    @wsme_pecan.wsexpose(ReportFile, wtypes.text)
    def get(self, id):
        conn = pecan.request.storage_conn
        model = conn.get_rptfiles(file_id=id)[0]
        file = ReportFile.from_dict(model)
        return file
    """
