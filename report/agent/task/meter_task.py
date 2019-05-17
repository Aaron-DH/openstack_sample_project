# -*- coding:utf-8 -*-
import json
import time
import datetime
import calendar
import operator

from stevedore import driver
from oslo_config import cfg
from oslo_log import log
from oslo_utils import netutils

from report import utils
from report.client.nova_client import NovaClient
from report.client.zeus_client import ZeusClient
from report.client.keystone_client import KeystoneClient
from report.agent.tasks import TimeUtil
from report.agent.tasks import Task
from reportlab.lib import colors
from report.drawutils.report_pic import PicDriver

LOG = log.getLogger(__name__)
CONF = cfg.CONF

TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
TIME_ORMAT = '%Y-%m-%dT%H:%M:%S'

TABLESTYLE = [('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
              ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
              ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
              ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
              ('BACKGROUND', (0, 0), (-1, 0), colors.lightskyblue),
              ('FONTNAME', (0, 0), (-1, 0), 'song'),
              ('FONTNAME', (0, 1), (0, -1), 'hei')]

TABLESTYLF = [('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
              ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
              ('SPAN', (0, 0), (0, 1)),
              ('SPAN', (1, 0), (1, 1)),
              ('SPAN', (2, 0), (2, 1)),
              ('SPAN', (3, 0), (3, 1)),
              ('SPAN', (4, 0), (-1, 0)),
              ('VALIGN', (0, 0), (-1, 1), 'MIDDLE'),
              ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
              ('BACKGROUND', (0, 0), (-1, 1), colors.lightskyblue),
              ('FONTNAME', (0, 0), (-1, 1), 'song'),
              ('FONTNAME', (0, 0), (0, -1), 'hei')]

SUCCESS_EVENT_TYPE = [
    'compute.instance.create.end'
]

FAIL_EVENT_TYPE = [
    'compute.instance.volume.attach.error',
    'compute.instance.instance.create.error',
    'compute.instance.create.error',
    'orchestration.stack.delete.error',
    'orchestration.stack.create.error',
    'orchestration.stack.rollback.error',
    'compute.instance.volume.detach.error',
    'orchestration.stack.update.error',
    'orchestration.autoscaling.error',
    'compute.libvirt.error'
]

report_content = [
    # "resource_statistics",
    "user_statistics",
    "vm_statistics",
]


class MeterTask(Task):
    def __init__(self, taskinfo, conn):
        super(MeterTask, self).__init__(taskinfo, conn)
        self.cli_zeus = ZeusClient.from_url()
        self.cli_nova = NovaClient.from_url()
        self.cli_ks = KeystoneClient.from_url()

        self.contentlist = self.task_content.get('meterlist')
        if not self.contentlist:
            self.contentlist = report_content

        self.flavor_info = {}
        flavors = self.cli_nova.get_flavors()
        if flavors:
            for flavor in flavors['flavors']:
                flavor_id = flavor['id']
                self.flavor_info[flavor_id] = dict(
                    disk=flavor['disk'],
                    vcpus=flavor['vcpus'],
                    ram=flavor['ram']
                )

        global _
        _ = self.i18n

    def time_distribution(self, events):
        now_date = datetime.datetime.now()
        days = calendar.monthrange(now_date.year, now_date.month)[1]
        days_list = range(1, days+1)

        create_day_count = {}
        delete_day_count = {}
        day_list = []
        for event in events:
            gen = event['generated']
            gen_format = datetime.datetime.strptime(gen, TIME_ORMAT)
            generated_day = int(gen_format.strftime('%d'))
            day_list.append(generated_day)
            if event['event_type'] == 'compute.instance.create.end':
                if generated_day not in create_day_count:
                    create_day_count[generated_day] = 0
                create_day_count[generated_day] += 1
            elif event['event_type'] == 'compute.instance.delete.end':
                if generated_day not in delete_day_count:
                    delete_day_count[generated_day] = 0
                delete_day_count[generated_day] += 1

        x_days = sorted(set(day_list))

        for x_day in x_days:
            if x_day not in create_day_count:
                create_day_count[x_day] = 0
            if x_day not in delete_day_count:
                delete_day_count[x_day] = 0

        count_virtual = {"title": "all virtual machine for month",
                         "x_label_list": x_days,
                         "value_list": [("create", create_day_count.values()),
                                        ("delete", delete_day_count.values())]}

        return count_virtual

    def user_distribution(self, table_list):

        value_list = []

        for table in table_list[2:]:
            username = table[0]
            total_success = table[1]
            total_fail = table[2]

            value_list.append((username, [total_success]))

        user_distribution = {
            "title": "user distribution for virtual machine",
            "value_list": value_list
        }

        return user_distribution

    def state_distribution(self, events):
        _success = 0
        _fail = 0
        for event in events:
            event_type = event['event_type']
            if event_type == 'compute.instance.create.end':
                _success = _success + 1
            elif event_type in FAIL_EVENT_TYPE:
                _fail = _fail + 1

        value_list = [
            ("Success", [_success]),
            ("Fail", [_fail])
        ]

        state_distribution = {"title": "virtual machine build states",
                              "value_list": value_list}

        return state_distribution

    def flavor_distribution(self, events):
        flavor_count = {}
        for event in events:
            event_type = event['event_type']
            if event_type == "compute.instance.create.end":
                flavor_id = event['meta']['flavor_id']
                flavor = self.flavor_info.get(flavor_id, {})
                cpu = flavor.get('vcpus', 0)
                mem = flavor.get('ram', 0)
                disk = flavor.get('disk', 0)
                flavor_key = "%dC%dG%dG" % (cpu, mem / 1024, disk)
                if flavor_key in flavor_count:
                    flavor_count[flavor_key] += 1
                else:
                    flavor_count[flavor_key] = 1

        value_list = []
        for key, value in flavor_count.items():
            value_list.append((key, [value]))

        flavor_distribution = {"title": "virtutal machine flavor distribution",
                               "value_list": value_list}

        return flavor_distribution

    def resource_statistics(self, fileutil):
        fileutil.draw_title(_("Resource Statistics"), 1)
        fileutil.draw_title(_("Physics Resource"), 2)
        table_list = [
            [_("Total CPU"),
             _("Total Mem"),
             _("Local Storage"),
             _("Public IP"),
             _("RBD Storage")],
            [20, 126, 2447, 17, 74]
        ]
        fileutil.draw_table(table_list, TABLESTYLE)

        fileutil.draw_title(_("Virtual Resource"), 2)
        table_list = [
            [_("Virtual Machine"),
             _("Exchange"),
             _("Router"),
             _("Load Balance"),
             _("Cloud Disk")],
            [13, 8, 6, 2, 35]
        ]
        fileutil.draw_table(table_list, TABLESTYLE)

    def user_resource_statistics(self, fileutil):
        fileutil.draw_title(_("User Resource Statistics"), 2)

        data_dict = {}
        instances = self.cli_nova.list_instances()
        # LOG.info("get instance: " + str(instances))
        # instances = tools.gen_vmdatas(100)

        table_list = [
            [_("User Name"),
             _("Num of VM"),
             _("VCPUs"),
             _("Memory_MB"),
             _("Disk_GB")]
        ]
        if instances == {'servers': []} or instances is None:
            row_list = [' ', ' ', ' ', ' ', ' ']
            table_list.append(row_list)
            fileutil.draw_table(table_list, TABLESTYLE)
        else:
            for ins in instances['servers']:
                user_id = ins['user_id']
                try:
                    user_info = self.cli_ks.get_user(user_id).get("user", {})
                except:
                    LOG.error("Can not get user from keystone.")
                    continue

                user_name = user_info.get("username")
                flavor_id = ins['system_metadata']['instance_type_flavorid']
                flavor = self.flavor_info.get(flavor_id, {})
                if user_name not in data_dict:
                    data_dict[user_name] = {}

                u_dict = data_dict[user_name]

                u_dict['vm_num'] = 1 + u_dict.get("vm_num", 0)
                u_dict['vcpus'] = flavor.get("vcpus", 0) + u_dict.get("vcpus", 0)
                u_dict['ram'] = flavor.get("ram", 0) + u_dict.get("ram", 0)
                u_dict['disk'] = flavor.get("disk", 0) + u_dict.get("disk", 0)

            for user, info in data_dict.iteritems():
                row_list = [
                    user, info['vm_num'], info['vcpus'], info['ram'], info['disk']
                ]
                table_list.append(row_list)

            fileutil.draw_table(table_list, TABLESTYLE)

    def user_vm_statistics(self, fileutil, events):
        fileutil.draw_title(_("User VM Creation Statistics"), 2)

        data_dict = {}

        if not events:
            return

        for event in events:
            user = event['username']
            if user not in data_dict:
                data_dict[user] = {}
            user_dict = data_dict[user]

            vcpus = user_dict.get("create_vcpus", 0)
            ram = user_dict.get("create_ram", 0)
            disk = user_dict.get("create_disk", 0)
            create_suc = user_dict.get("create_suc", 0)
            create_fail = user_dict.get("create_fail", 0)
            event_type = event['event_type']
            if event_type == 'compute.instance.create.end':
                flavor_id = event['meta']['flavor_id']
                flavor = self.flavor_info.get(flavor_id, {})
                user_dict['create_suc'] = 1 + create_suc
                user_dict['create_vcpus'] = flavor.get("vcpus", 0) + vcpus
                user_dict['create_ram'] = flavor.get("ram", 0) + ram
                user_dict['create_disk'] = flavor.get("disk", 0) + disk
            elif event_type in FAIL_EVENT_TYPE:
                user_dict['create_fail'] = 1 + create_fail
            elif event_type == "compute.instance.delete.end":
                user_dict['del_suc'] = 1 + user_dict.get('del_suc', 0)
            else:
                continue

        table_list = [
            [_("User Name"),
             _("Success Creation"),
             _("Failed Creation"),
             _("Deletion"),
             _("Added Resources"), "", ""],
            ["", "", "", "", _("VCPUs"), _("Memory_MB"), _("Disk_GB")]
        ]
        for user, info in data_dict.iteritems():
            if not info.get('create_suc') or info.get('create_fail') \
                                            or info.get('del_suc'):

                continue

            row_list = [
                user,
                info.get('create_suc', 0),
                info.get('create_fail', 0),
                info.get('del_suc', 0),
                info.get('create_vcpus', 0),
                info.get('create_ram', 0),
                info.get('create_disk', 0)
            ]
            table_list.append(row_list)

        fileutil.draw_table(table_list, TABLESTYLF)
        if len(table_list) == 2:
            self.contentlist = []

    def user_statistics(self, fileutil, events):
        fileutil.draw_title(_("User Statistics"), 1)

        self.user_resource_statistics(fileutil)
        self.user_vm_statistics(fileutil, events)

    def create_report_file(self):
        now = str(datetime.datetime.now().date())
        file_name = CONF.report_file.rptfile_path + \
            self.task_name + '_' + now + '.' + self.filetype
        fileutil = self.filedriver(file_name)
        fileutil.add_catalog_title(_('Contents'))
        period = TimeUtil.get_period(self.task_period)
        start, end = period['time_s'], period['time_e']
        # start, end = '2016-05-5', '2016-05-6'

        q_params = dict(
            start=start,
            end=end
        )
        events = self.cli_zeus.get_events(**q_params)
        # LOG.info("get events:" + str(events))

        fileutil.draw_title(_(self.task_name))
        # if "resource_statistics" in self.contentlist:
        #     self.resource_statistics(fileutil)

        # events = tools.gen_vmcreate_events(60)
        # events.extend(tools.gen_vmdelete_events(20))
        # events.extend(tools.gen_vmcreate_fail_events(30))
        if "user_statistics" in self.contentlist:
            self.user_statistics(fileutil, events)

        if "vm_statistics" in self.contentlist:
            if events:
                fileutil.draw_title(_("VM Statistics"), 1)
                state_distribution = self.state_distribution(events)
                fileutil.draw_title(_("Status Distribution Of VM Creation"),
                                    2)
                picpath = PicDriver.pie_chart(data=state_distribution)
                fileutil.draw_pic(picpath)

                flavor_distribution = self.flavor_distribution(events)
                fileutil.draw_title(_("Flavors Distribution Of VM Creation"),
                                    2)
                picpath = PicDriver.pie_chart(data=flavor_distribution)
                fileutil.draw_pic(picpath)

                if self.task_period == 'month':
                    time_distribution = self.time_distribution(events)
                    fileutil.draw_title(_("Time Distribution Of VM Creation"),
                                        2)
                    picpath = PicDriver.bar_chart(data=time_distribution)
                    fileutil.draw_pic(picpath)

        fileutil.flush()
        return file_name
