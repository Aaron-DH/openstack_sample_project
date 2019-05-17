# coding=utf-8
import re
import copy
import json
import datetime
from datetime import datetime as dt_time

from oslo_config import cfg
from oslo_log import log
from itertools import groupby
from reportlab.lib import colors

from report.drawutils.report_pic import PicDriver
from report.agent.tasks import Task
from report.agent.tasks import TimeUtil
from report.client.zeus_client import ZeusClient
from report.client.keystone_client import KeystoneClient


LOG = log.getLogger(__name__)
CONF = cfg.CONF
"""
INTERVAL_SWITCH = {
    "day": "_daily_query",
    "week": "_weekly_query",
    "month": "_monthly_query"
}
"""
CHART_OPTS = {
    "host distribute": "_host_distribute",
    "user distribute": "_user_distribute",
    "status distribute": "_status_distribute",
    "type distribute": "_type_distribute",
    "severity distribute": "_severity_distribute",
    "time distribute": "get_alarm_time_distribute",
    "response time distribute": "get_alarm_response_time_distribute",
    # "alarm detail table": "get_alarm_detail_table",
}

TABLESTYLE = [('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
              ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
              ('SPAN', (0, 0), (0, 1)),
              ('SPAN', (1, 0), (1, 1)),
              ('SPAN', (2, 0), (2, 1)),
              ('SPAN', (3, 0), (5, 0)),
              ('SPAN', (6, 0), (8, 0)),
              ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
              ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
              ('BACKGROUND', (0, 0), (-1, 1), colors.lightblue),
              ('FONTNAME', (0, 0), (-1, 1), 'song'),
              ('FONTNAME', (0, 1), (0, -1), 'hei')]


class AlarmTask(Task):
    def __init__(self, taskinfo, conn):
        super(AlarmTask, self).__init__(taskinfo, conn)
        self.cli = ZeusClient.from_url()
        self.ks_cli = KeystoneClient().from_url()

        self.countlist = None
        if self.task_content.get('meterlist'):
            self.countlist = self.task_content.get('meterlist')
        else:
            self.countlist = CHART_OPTS.keys()

        global _
        _ = self.i18n

    def _filter(self, **kwargs):
        filter = dict(start=TimeUtil.get_period(self.task_period)['time_s'],
                      end=TimeUtil.get_period(self.task_period)['time_e'])
        # filter = dict(start='2016-03-15', end='2016-03-16')
        if kwargs:
            for key, value in kwargs.item():
                filter[key] = value
        return filter

    def _all_alarm_event(self):
        kwargs = self._filter()
        # kwargs = {}
        alarm_event_list = self.cli.alarm_events(**kwargs)
        return self._attach_hostinfo(alarm_event_list)

    def _attach_hostinfo(self, alarm_event_list):
        if not alarm_event_list:
            return
        list_with_hostinfo = []
        # dt_by_id's structure is like [[],[]]
        dt_by_id = self._group_by_argue(alarm_event_list, 'resource_id')
        hostlist = self.task_content.get('hostlist')
        userlist = self.ks_cli.get_users().get('users')
        userdict = {}
        if userlist:
            for user in userlist:
                userdict[user['id']] = user.get('username')

        for alarm_event_by_id in dt_by_id:
            resource_type = (alarm_event_by_id[0].get('resource_type')
                             .split(".")[0])
            resource_id = alarm_event_by_id[0].get('resource_id')
            if resource_type == 'vm':
                vm_or_node = self.cli.get_vm(resource_id)
            elif resource_type == 'node':
                vm_or_node = self.cli.get_node(resource_id)
            else:
                url = '/v1/%ss/%s' % (resource_type, resource_id)
                res = self.cli.get_resource(url=url)
                if not res:
                    continue
                if res.get('node_id'):
                    resource_id = res.get('node_id')
                    vm_or_node = self.cli.get_node(resource_id)
                else:
                    resource_id = res.get('vm_id')
                    vm_or_node = self.cli.get_vm(resource_id)
            if not vm_or_node:
                continue
            if hostlist:
                if (vm_or_node.get('uuid') not in hostlist):
                    continue
            for alarm_event in alarm_event_by_id:
                VmOrNode = {}
                username = userdict.get(vm_or_node.get('user_id'))
                VmOrNode['username'] = username
                VmOrNode['user_id'] = vm_or_node.get('user_id')
                VmOrNode['uuid'] = vm_or_node.get('uuid')
                VmOrNode['hostname'] = vm_or_node.get('hostname')
                VmOrNode['ip'] = vm_or_node.get('ip')
                alarm_event.update(VmOrNode)
                list_with_hostinfo.append(alarm_event)
        LOG.info("Get %s alarm records." % len(list_with_hostinfo))
        return list_with_hostinfo

    def _table_data(self, alarm_data):
        result = []

        host_distribute = self._group_by_argue(alarm_data, 'uuid')
        for host in host_distribute:
            count = {}
            count['alarm_sum'] = len(host)
            count['uuid'] = host[0].get('uuid')
            count['hostname'] = host[0].get('hostname')
            # count['resource_type'] = host[0].get('resource_type')
            type = host[0].get('resource_type')
            r = re.compile('^v')
            if r.match(type):
                count['resource_type'] = 'vm'
            else:
                count['resource_type'] = 'physical'

            severity_distribute = self._group_by_argue(host, 'severity')
            status_distribute = self._group_by_argue(host, 'status')
            for severity in severity_distribute:
                count[severity[0]['severity']] = len(severity)
            for status in status_distribute:
                count[status[0]['status']] = len(status)
            result.append(count)
        sorted(result, key=lambda x: x['alarm_sum'], reverse=True)
        return result

    def _status_distribute(self, alarm_data):
        count_status = {
            'processed': [0],
            'unprocessed': [0],
            'ignored': [0]
        }
        for record in alarm_data:
            count_status[record.get('status')][0] += 1
        return{
            "status distribute":
            {
                'value_list': count_status.items(),
                'chart_type': 'pie'
            }
        }

    def _severity_distribute(self, alarm_data):
        count_severity = {
            'low': [0],
            'moderate': [0],
            'critical': [0]
        }
        for record in alarm_data:
            count_severity[record.get('severity')][0] += 1
        return{
            "severity distribute":
            {
                'value_list': count_severity.items(),
                'chart_type': 'pie'
            }
        }

    def _type_distribute(self, alarm_data):
        count_type = {}
        for record in alarm_data:
            type = record.get('resource_type')
            r = re.compile('^v')
            if r.match(type):
                record['resource_type'] = 'vm'
            else:
                record['resource_type'] = 'physical'

            if not count_type.get(record.get('resource_type')):
                count_type[record.get('resource_type')] = 1
            else:
                count_type[record.get('resource_type')] += 1
        return{
            "type distribute":
            {
                'value_list': count_type.items(),
                'chart_type': 'pie'
            }
        }

    def _host_distribute(self, table_data):
        count_host = {}
        i = 1
        for record in table_data:
            hostname = (record.get('hostname') if
                        record.get('hostname') else "Host%d" % i)
            count_host[hostname] = [record['alarm_sum']]
            i += 1
        return{
            "host distribute":
            {
                'value_list': count_host.items(),
                'chart_type': 'pie'
            }
        }

    def _user_distribute(self, alarm_data):
        count_user = []
        group_data = self._group_by_argue(alarm_data, 'user_id')
        for record in group_data:
            username = (record[0].get('username') if
                        record[0].get('username') else "unknown user")
            count_user.append((username, [len(record)]))
        return {
            "user distribute":
            {
                'value_list': count_user,
                'chart_type': 'pie'
            }
        }

    def get_alarm_response_time_distribute(self, alarm_data):
        alarm_event_list = self._convert_time2tuple(alarm_data)
        x_label_list, value_list = \
            self._response_time_distribute(alarm_event_list)
        return {
            "response time distribute": {
                'x_label_list': x_label_list,
                'value_list': value_list,
                'chart_type': 'bar'
            }
        }

    def _convert_time2tuple(self, alarm_data):
        i = 0
        alarm_event_list = copy.deepcopy(alarm_data)
        for alarm_event in alarm_event_list:
            creation_time = alarm_event.get('timestamp')
            update_time = alarm_event.get('update_time')
            ct_tuple = dt_time.strptime(creation_time, '%Y-%m-%dT%H:%M:%S')
            ut_tuple = dt_time.strptime(update_time, '%Y-%m-%dT%H:%M:%S')
            alarm_event_list[i]['timestamp'] = ct_tuple
            alarm_event_list[i]['update_time'] = ut_tuple
            i += 1
        return alarm_event_list

    def _response_time_distribute(self, alarm_event_list):
        response_list = []
        seconds2hour = 3600
        for alarm_event in alarm_event_list:
            response_time = (alarm_event.get("update_time") -
                             alarm_event.get("timestamp"))
            response_list.append(response_time.total_seconds()/seconds2hour)
        max_time = round(max(response_list), 2)
        min_time = round(min(response_list), 2)
        avg_time = round(sum(response_list)/len(response_list))
        result = [max_time, min_time, avg_time]
        x_label_list = ["max", "min", "avg"]
        value_list = [('time(h)', result)]
        return x_label_list, value_list

    def get_alarm_time_distribute(self, alarm_data, time_range):
        alarm_event_list = self._convert_time2tuple(alarm_data)
        x_label_list, value_list = self._time_distribute(
            alarm_event_list,
            time_range)
        return {
            "time distribute": {
                'x_label_list': x_label_list,
                'value_list': value_list,
                'chart_type': 'bar'
            }
        }

    def _time_distribute(self, alarm_event_list, time_range):
        tm_range = {
            "month": "day",
            "week": "day",
            "day": "hour"
        }
        timeline = []
        value_list = []
        x_label_list = None
        group_data = self._group_by_argue(alarm_event_list,
                                          'timestamp',
                                          time_range)
        for recordlist in group_data:
            time_tuple = getattr(
                recordlist[0].get('timestamp'),
                tm_range[time_range]
            )
            timeline.append(time_tuple)
            value_list.append(len(recordlist))
        x_label_list = timeline
        value_list = [('timeline', value_list)]

        return x_label_list, value_list

    def get_alarm_detail_table(self, alarm_data):
        tb_dt_li = self._group_by_argue(alarm_data, "hostname")
        table_list = []
        for tb_dt in tb_dt_li:
            sorted(tb_dt, key=lambda x: x['update_time'], reverse=True)
            table = []
            host_name = tb_dt[0].get("hostname", "No Host name")
            number = 0

            for record in tb_dt:
                number += 1
                status = record.get("status")
                severity = record.get("severity")
                reason = list(record.get("reason"))
                i = len(reason)/15
                while i:
                    reason.insert(i*15, '\n')
                    i -= 1
                reason = ''.join(reason)
                creation_time = record.get("timestamp")
                update_time = record.get("update_time")
                table.append([number, status, severity,
                             reason, creation_time, update_time])
            table_list.append((host_name, table))
        return table_list

    def _group_by_argue(self, data, argue, index=None):
        ret = []
        if not index:
            data.sort(key=lambda x: x.get(argue))
            for _, group in groupby(data, lambda x: x.get(argue)):
                ret.append(list(group))
        elif index == 'day':
            data.sort(key=lambda x: x.get(argue).hour)
            for _, group in groupby(data, lambda x: x.get(argue).hour):
                ret.append(list(group))
        elif index == 'month' or index == 'week':
            data.sort(key=lambda x: x.get(argue).day)
            for _, group in groupby(data, lambda x: x.get(argue).day):
                ret.append(list(group))
        else:
            data.sort(key=lambda x: getattr(x.get(argue), index))
            for _, group in groupby(data,
                                    lambda x: getattr(x.get(argue), index)):
                ret.append(list(group))
        return ret

    def get_table_data(self, alarm_data):
        data = alarm_data
        table_data = []
        first_row = [_("hostname"),
                     _("Resource Name"),
                     _("Total Alarm"),
                     _("severity distribute"),
                     "", "", _("status distribute"), "", ""]
        second_row = ["", "", "",
                      _("critical"),
                      _("moderate"),
                      _("low"),
                      _("processed"),
                      _("unprocessed"),
                      _("ignored")]
        table_data.append(first_row)
        table_data.append(second_row)
        if not data:
            return table_data

        for record in data:
            table_data.append([record.get('hostname', '-'),
                               record.get('resource_type', '-'),
                               record.get('alarm_sum', 0),
                               record.get("critical", 0),
                               record.get("moderate", 0),
                               record.get("low", 0),
                               record.get("processed", 0),
                               record.get("unprocessed", 0),
                               record.get("ignored", 0)
                               ])
        return table_data

    def get_pic(self, title, data):
        data['title'] = title
        if data.get('chart_type') == 'line':
            time_format = (self.task_period if
                           self.task_period != 'once' else 'day')
            path = PicDriver.line_chart(data, "png", time_format)
        elif data.get('chart_type') == 'bar':
            path = PicDriver.bar_chart(data, "png")
        else:
            path = PicDriver.pie_chart(data, "png")
        if path:
            LOG.info("Create a chart at %s" % path)
        else:
            LOG.info("No chart!")
        return path

    def create_report_file(self):
        alarm_data = self._all_alarm_event()
        now = str(datetime.datetime.now().date())
        file_name = CONF.report_file.rptfile_path + \
            self.task_name + '_' + now + '.' + self.filetype
        fileutil = self.filedriver(file_name)
        fileutil.add_catalog_title(_('Contents'))
        fileutil.draw_title(self.task_name)
        if not alarm_data:
            table_data = self.get_table_data(alarm_data)
            fileutil.draw_title(_('Alarm Summary Data'), 1)
            fileutil.draw_table(table_data, TABLESTYLE)
            fileutil.flush()
            return file_name

        _tb_dt_without_header = self._table_data(alarm_data)
        table_data = self.get_table_data(_tb_dt_without_header)
        fileutil.draw_title(_('Alarm Summary Data'), 1)
        fileutil.draw_table(table_data, TABLESTYLE)
        chart_data = {}
        for chart in self.countlist:
            f = CHART_OPTS.get(chart)
            if f:
                if f == "_host_distribute":
                    chart_data.update(getattr(self, f)(_tb_dt_without_header))
                elif f == "get_alarm_time_distribute":
                    chart_data.update(getattr(self, f)(
                        alarm_data,
                        self.task_period))
                else:
                    chart_data.update(getattr(self, f)(alarm_data))
        for pic_key, pic_value in chart_data.items():
            pic_path = self.get_pic(pic_key, pic_value)
            fileutil.draw_title(_(pic_key), 1)
            fileutil.draw_pic(pic_path)
        fileutil.flush()
        return file_name


if __name__ == "__main__":
    cli = ZeusClient(host='192.168.138.2', port=8888)
    data = cli.alarm_events(severity='low')
    print data[1]
