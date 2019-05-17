# coding=utf-8

import time
import datetime
import calendar
import json
import operator

from oslo_config import cfg
from oslo_log import log

from report import utils
from report.client.zeus_client import ZeusClient
from report.client.influx import Client as influxdbClient
from report.agent.tasks import Task
from report.agent.tasks import TimeUtil
from report.drawutils.report_pic import PicDriver
from reportlab.lib import colors


LOG = log.getLogger(__name__)
CONF = cfg.CONF

TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

default_performance_metrics = [
    'node.cpu.total.percent',
    'node.mem.percent',
    'node.swap.percent'
]

default_vmperformance_metrics = [
    'vm.cpu.total.percent',
    'vm.mem.percent',
    'vm.swap.percent'
]

default_disk_metrics = [
    'partition.percent'
]

default_vmdisk_metrics = [
    'vpartition.percent'
]

i18n = {
    # metric:[Name in table, Name in Picture, Desc in PDF]
    'node.cpu.total.percent': ['CPU Usage Percent(%)',
                               'CPU Utilization Details TOPN'],
    'node.mem.percent': ['Mem Usage Percent(%)',
                         'Mem Utilization Details TOPN'],
    'node.swap.percent': ['Swap Usage Percent(%)',
                          'Swap Space Usage Details TOPN'],
    'partition.percent': ['Partition Usage Percent(%)',
                          'Growth Trend Of Disk Partition Utilization'],
    'vm.cpu.total.percent': ['CPU Usage Percent(%)',
                             'CPU Utilization Details TOPN'],
    'vm.mem.percent': ['Mem Usage Percent(%)',
                       'Mem Utilization Details TOPN'],
    'vm.swap.percent': ['Swap Usage Percent(%)',
                        'Swap Space Usage Details TOPN'],
    'vpartition.percent': ['Partition Usage Percent(%)',
                           'Growth Trend Of Disk Partition Utilization']
}

x_range = {
    "day": "1h",
    "week": "6h",
    "month": "1d"
}


class MonitorTask(Task):

    def __init__(self, taskinfo, conn):
        super(MonitorTask, self).__init__(taskinfo, conn)
        self.influx = influxdbClient()
        self.zeusclient = ZeusClient.from_url()
        self.hostlist = self.task_content.get('hostlist', [])
        metrics = self.task_content.get('meterlist', [])

        self.performance_metrics = []
        self.disk_metrics = []
        self.vm_performance_metrics = []
        self.vm_disk_metrics = []

        if not metrics:
            self.performance_metrics = default_performance_metrics
            self.disk_metrics = default_disk_metrics
            self.vm_performance_metrics = default_vmperformance_metrics
            self.vm_disk_metrics = default_vmdisk_metrics
        else:
            for metric in metrics:
                if metric in default_performance_metrics:
                    self.performance_metrics.append(metric)
                    self.vm_performance_metrics.append(
                        metric.replace('node', 'vm'))
                elif metric in default_disk_metrics:
                    self.disk_metrics.append(metric)
                    self.vm_disk_metrics.append('v' + metric)

        self.ts = [
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
            ('SPAN', (0, 0), (0, 1)),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, 1), colors.lightblue),
            ('FONTNAME', (0, 0), (-1, 1), 'song'),
            ('FONTNAME', (0, 1), (0, -1), 'hei')
        ]

        for i in range(0, len(self.performance_metrics)):
            self.ts.append(('SPAN', (i*3 + 1, 0), (i*3 + 3, 0)))
            self.ts.append(('ALIGN', (i*3 + 1, 0), (i*3 + 3, 0), 'CENTER'))

        global _
        _ = self.i18n

    def parse_content(self):
        pass

    def get_statistics_data(self, start, end,
                            measurmentlist, hostlist):
        """
        Get statistics data(mean, max, min)
        :param start:
        :param end:
        :param measurementlist:
        :return: dict
        {
            hostname:{measurement1:[mean,max,min],measurement2:[mean,max,min]...}
        }
        """
        datadict = {}

        measurement = "|".join(measurmentlist)

        queryURL = "select mean(value),max(value),min(value) from /%s/ " % measurement + \
                   "where time > '%s' and time < '%s' " % (start, end)
        if hostlist:
            params = '|'.join(hostlist)
            queryURL += ' and hostname =~ /' + params + '/'

        queryURL += ' group by hostname'

        datas = self.influx.get_data_byurl(queryURL)
        if datas is None:
            LOG.warn("get data failed, queryURL: %s.", queryURL)
            return None

        for data in datas:
            hostname = data['tags']['hostname']
            metric = data['name']
            values = data['values'][0][1:]

            if hostname not in datadict:
                datadict[hostname] = {}

            datadict[hostname][metric] = values

        return datadict

    def get_statistics_table_data(self, data, data_type):
        table = []
        first_row = [_("hostname")]
        second_row = [""]
        for metric in data_type:
            first_row.extend([_(i18n[metric][0]), "", ""])
            second_row.extend([_("Avg"),
                               _("Max"),
                               _("Min")])

        table.append(first_row)
        table.append(second_row)
        for hostname, datas in data.items():
            row_table = [hostname]
            for metric in data_type:
                if metric not in datas.keys():
                    datas[metric] = [0, 0, 0]
                row_table.extend(["%.2f" % (float(a)) for a in datas[metric]])

            table.append(row_table)

        return table

    def get_statistics_topn_host(self, data, topn):
        """
        get topn hostlist by mean data
        :param aggdata:
        :param n:
        :return: dict
        {
            measurement1:[host1,host2,.....]
        }
        """
        d = {}
        for host, datas in data.items():
            hostname = host
            for meter, values in datas.items():
                mean = values[0]
                if meter not in d:
                    d[meter] = {}

                d[meter][hostname] = mean

        result = {}
        for key, values in d.items():
            hostlist = []
            sortvalue = sorted(values.iteritems(),
                               key=operator.itemgetter(1),
                               reverse=True)
            topN = topn if topn < len(sortvalue) else len(sortvalue)
            for i in range(0, topN):
                host = sortvalue[i][0]
                hostlist.append(host)

            result[key] = hostlist

        return result

    def get_detail_data(self, start, end, measurement, host):
        """
        get detail data
        :param start:
        :param end:
        :param measurement:
        :param hostlist:
        :return:
         tuple:
         data[0]: x_data
         data[1]: y_data_list
        """
        queryURL = "select max(value) from \"%s\" " % measurement + \
                   "where time > '%s' and time < '%s' and hostname = '%s' " % (start, end, host) + \
                   "group by time(%s),hostname,resname" % \
                   x_range[self.task_period]

        datas = self.influx.get_data_byurl(queryURL)
        if datas is None:
            LOG.warn("get data failed, queryURL: %s.", queryURL)
            return None

        result = []
        for info in datas:
            xdata = []
            ydata = []
            resname = info['tags']['resname']
            for value in info['values']:
                if value[1] is None:
                    ydata.append(0)
                else:
                    ydata.append(float("%.2f" % (float(value[1]))))

                time = datetime.datetime.strptime(value[0], TIME_FORMAT)
                xdata.append(time)

            result.append((resname, ydata))

        return xdata, result

    def draw_server_file(self, fileutil, title_h1, metrics, disk_metrics):
        period = TimeUtil.get_period(self.task_period)
        start, end = period['time_s'], period['time_e']
        # start, end = '2016-02-22', '2016-02-29'
        if(metrics):
            hostlist = None
            statistics_data = self.get_statistics_data(start, end,
                                                       metrics,
                                                       hostlist)

            if statistics_data is None:
                fileutil.draw_title(title_h1, 1)
                return fileutil

            data_type = metrics
            statistics_table = self.get_statistics_table_data(
                statistics_data, data_type)
            fileutil.draw_title(title_h1, 1)
            fileutil.draw_title(_("Summary Data Tables"), 2)
            fileutil.draw_table(statistics_table, self.ts)
            topN_hosts = self.get_statistics_topn_host(statistics_data, 5)
            topN_keys = []
            topN_keys.append(sorted(list(topN_hosts.keys())))
            for key in topN_keys[0]:
                hostlist = topN_hosts[key]
                fileutil.draw_title(_(i18n[key][1]), 2)
                datas = {}
                datas['value_list'] = []
                for host in hostlist:
                    xdata, data = self.get_detail_data(start, end, key, host)
                    datas['value_list'].extend(data)
                datas['x_label_list'] = xdata
                datas['title'] = i18n[key][0]
                picpath = PicDriver.line_chart(data=datas,
                                               time_format=self.task_period)
                fileutil.draw_pic(picpath)

        if len(disk_metrics):
            if not len(metrics):
                hostlist = None
                if disk_metrics == default_disk_metrics:
                    metrics = ['node.mem.percent']
                else:
                    metrics = ['vm.mem.percent']
                statistics_data = self.get_statistics_data(start, end,
                                                           metrics,
                                                           hostlist)
                if statistics_data is None:
                    return None
                # topN_hosts = self.get_statistics_topn_host(statistics_data, 5)
                # hostlist = topN_hosts[metrics[0]]
                hostlist = statistics_data.keys()
                fileutil.draw_title(title_h1, 1)

            fileutil.draw_title(_("Disk Partition"), 2)
            for host in statistics_data.keys():
                fileutil.draw_title(host, 3)
                for metric in disk_metrics:
                    datas = {}
                    datas['value_list'] = []
                    detaildata = self.get_detail_data(start, end, metric, host)
                    if detaildata is None:
                        fileutil.draw_text('No data found, please check it!')
                        continue
                    datas['value_list'].extend(detaildata[1])
                    datas['x_label_list'] = detaildata[0]
                    datas['title'] = i18n[metric][0]
                    picpath = PicDriver.line_chart(
                        data=datas, time_format=self.task_period)
                    fileutil.draw_pic(picpath)
        return fileutil

    def create_report_file(self):
        now = str(datetime.datetime.now().date())
        file_name = CONF.report_file.rptfile_path + \
            self.task_name + '_' + now + '.' + self.filetype
        fileutil = self.filedriver(file_name)
        fileutil.add_catalog_title(_('Contents'))
        fileutil.draw_title(_(self.task_name))

        physical_h1_title = _("Physical machine resource statistics")
        virtual_h1_title = _("Virtual machine resource statistics")

        fileutil = self.draw_server_file(fileutil, physical_h1_title,
                                         self.performance_metrics,
                                         self.disk_metrics)

        fileutil = self.draw_server_file(fileutil, virtual_h1_title,
                                         self.vm_performance_metrics,
                                         self.vm_disk_metrics)
        fileutil.flush()
        return file_name
