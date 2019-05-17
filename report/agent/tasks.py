# coding=utf-8


# if possible, instead with oslo_utils.timeutils
import uuid
import os
import re
import calendar
import json
import ast
from datetime import timedelta
from datetime import datetime
from datetime import date

from stevedore import driver
from oslo_config import cfg
from oslo_log import log
from oslo_utils import timeutils

from report.utils import MailUtil
from report import storage

LOG = log.getLogger(__name__)
CONF = cfg.CONF

FILE_TYPE = ['pdf', 'excel']

MailContent = "This mail auto send by system, don't need to reply"
MailFrom = "Awcloud-Report Team"

MAIL_OPTS = {
    cfg.StrOpt('from_mail',
               secret=True,
               default='awcloud@awcloud.com',
               help='The email to post report file'),
    cfg.StrOpt('password',
               secret=True,
               default='awcloud-report'),
    cfg.StrOpt('smtp_host',
               secret=True,
               default='smtp.qq.com'),
    cfg.StrOpt('template_path',
               secret=True,
               default='/etc/report/mail_template.xml')
}

RPT_FILE = {
    cfg.StrOpt('rptfile_path',
               secret=True,
               default='',
               help='The path to store the report file'),
    cfg.StrOpt('local_url',
               secret=True,
               default='',
               help='The ip to store the apache'),
}

CONF.register_opts(MAIL_OPTS, 'email')
CONF.register_opts(RPT_FILE, 'report_file')

one_day = timedelta(days=1)
one_week = timedelta(weeks=1)
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


default_trigger = {
    # 'day': dict(hour=17, minute=05),
    'day': dict(hour=8),
    'week': dict(day_of_week=0, hour=8),
    'month': dict(day=1, hour=8),
    'year': dict(month=1, day=1, hour=8)
}


class TimeUtil(object):
    @staticmethod
    def _get_next_month(dt):
        month = dt.month
        year = dt.year + month / 12
        month = month + 1 if month < 12 else 1
        return dt.replace(year=year, month=month, day=1)

    @staticmethod
    def get_period(period_str):
        """
        Calculate the begin and end time according to period.
        :param period_str:day,week or month
        :return: dict
         {
             "time_s":xxxx-xx-xx,
             "time_e":xxxx-xx-xx
         }
        """

        today = date.today()
        if period_str == 'day':
            return {
                "time_s": str(today - timedelta(days=1)),
                "time_e": str(today)
            }
        elif period_str == 'week':
            weekday = datetime.now().weekday()
            one_week = 7
            return {
                "time_s": str(today - timedelta(days=weekday + one_week)),
                "time_e": str(today - timedelta(days=weekday))
            }
        elif period_str == 'month':
            year = datetime.now().year
            last_month = datetime.now().month - 1 or 12
            last_month_last_day = calendar.monthrange(year, last_month)[1]
            last_month_today = (datetime.now() -
                                timedelta(days=last_month_last_day))
            return {
                "time_s": str(last_month_today.replace
                              (day=1))[:10],
                "time_e": str(last_month_today.replace
                              (day=last_month_last_day)+timedelta(days=1))[:10]
            }
        else:
            LOG.debug("Got an unexpected type %s !" % period_str)


class Task(object):

    @staticmethod
    def generator_task(taskinfo, conn):
        task_type = taskinfo['task_type']
        task_args = {'taskinfo': taskinfo,
                     'conn': conn}

        task_obj = driver.DriverManager(
            'report.type',
            task_type,
            invoke_on_load=True,
            invoke_kwds=task_args).driver

        return task_obj

    def __init__(self, taskinfo, conn):
        self.conn_mysql = conn
        self.task_id = taskinfo['task_id']
        self.task_name = taskinfo['task_name']
        self.task_type = taskinfo['task_type']
        self.task_period = taskinfo['task_period']
        # self.task_content = json.loads(taskinfo['task_content'])
        self.task_content = ast.literal_eval(taskinfo['task_content'])
        self.task_status = taskinfo['task_status']
        self.task_time = taskinfo.get('task_time', '')

        self.file_language = taskinfo.get('task_language', "English")
        if self.file_language == 'Chinese':
            from report.i18n import _F as _
        else:
            from report.i18n import _LI as _

        self.i18n = _

        # metadata = json.loads(taskinfo['task_metadata'])
        metadata = ast.literal_eval(taskinfo['task_metadata'])

        filetype = metadata.get('filetype', 'pdf')
        if filetype not in FILE_TYPE:
            self.filetype = 'pdf'
        else:
            self.filetype = filetype

        self.needmail = metadata.get('needmail', 'No')
        self.to_maillist = metadata.get('to_maillist', [])
        self.cc_maillist = metadata.get('cc_maillist', [])


        mgr = driver.DriverManager('report.file', self.filetype)
        self.filedriver = mgr.driver

        self.get_trigger()

    def parse_content(self):
        pass

    def get_trigger(self):
        self.task_schedule_type = 'cron'

        if self.task_period == 'once':
            self.task_schedule_type = 'once'
            if self.task_time:
                self.trigger = datetime.strptime(self.task_time, TIME_FORMAT)
            else:
                self.trigger = None

        else:
            if self.task_time:
                self.trigger = json.loads(self.task_time)
            else:
                self.trigger = default_trigger[self.task_period]

    def start(self):
        # report_file_list = self.create_report_file()
        # if report_file_list:
        #     for report_file in report_file_list:
        #         self._save_report(report_file)
        #
        #         if self.needmail == "Y":
        #             self._send_mail(report_file)
        LOG.info("Task start at: " + str(datetime.now()) + "; task_name: " + self.task_name)
        report_file = self.create_report_file()
        if report_file:
            self._save_report(report_file)

            if self.needmail == "Y":
                self._send_mail(report_file)
        LOG.info("Task end at: " + str(datetime.now()) + "; task_name: " + self.task_name)

    def _send_mail(self, report_file):
        mail = {
            "From": MailFrom,
            "Subject": self.task_name,
            "Content": MailContent
        }
        mail_driver = MailUtil(CONF.email.from_mail,
                               CONF.email.password,
                               CONF.email.smtp_host)
        to_maillists = []
        p=re.compile('[^\._-][\w\.-]+@(?:[A-Za-z0-9]+\.)+[A-Za-z]+$|^0\d{2,3}\d{7,8}$|^1[358]')
        for user in self.to_maillist:
            match = p.match(user)
            if match:
                to_maillists.append(match.group())

        mail_driver.send_mail(mail,
                              self.to_maillist,
                              self.cc_maillist,
                              report_file)

    def _save_report(self, file_path):
        record = dict(task_id=self.task_id,
                      file_id=str(uuid.uuid4()),
                      task_name=self.task_name,
                      task_type = self.task_type,
                      task_period = self.task_period,
                      file_path= file_path.split('/')[-1],
                      file_time=datetime.now())
        self.conn_mysql.add_rptfile(record)
