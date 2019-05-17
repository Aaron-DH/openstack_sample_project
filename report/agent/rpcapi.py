from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging

from report import rpc

agent_opts = [
    cfg.StrOpt('report_agent_topic',
               default='agent',
               help='The topic agent listen on'),
]

CONF = cfg.CONF
CONF.register_opts(agent_opts)

LOG = logging.getLogger(__name__)
VERSION = '1.0'


class AgentAPI(object):
    '''Client side of the compute rpc API.

    API version history:

        * 1.0 - Initial version.
    '''

    VERSION_ALIASES = {
        'kilo': '1.0',
    }

    def __init__(self):
        super(AgentAPI, self).__init__()
        target = messaging.Target(topic=CONF.report_agent_topic, version='1.0')
        # version_cap = self.VERSION_ALIASES.get(CONF.upgrade_levels.compute,
        #                                       CONF.upgrade_levels.compute)
        # serializer = objects_base.NovaObjectSerializer()
        # self.client = self.get_client(target, version_cap, serializer)
        self.client = self.get_client(target)

    def _compat_ver(self, current, legacy):
        if self.client.can_send_version(current):
            return current
        else:
            return legacy

    # Cells overrides this
    def get_client(self, target, version_cap=None, serializer=None):
        return rpc.get_client(target,
                              version_cap=version_cap,
                              serializer=serializer)

    def add_task(self, ctxt, task):
        cctxt = self.client.prepare(version=VERSION)
        cctxt.cast(ctxt, 'add_task', task=task)

    def update_task(self, ctxt, task):
        cctxt = self.client.prepare(version=VERSION)
        cctxt.cast(ctxt, 'update_task', task=task)

    def del_task(self, ctxt, task_id):
        cctxt = self.client.prepare(version=VERSION)
        cctxt.cast(ctxt, 'del_task', task_id=task_id)

    def get_next_run_time(self, ctxt, task_id):
        cctxt = self.client.prepare(version=VERSION)
        return cctxt.call(ctxt, 'get_next_run_time', task_id=task_id)

    def enable_task(self, ctxt, task):
        cctxt = self.client.prepare(version=VERSION)
        cctxt.cast(ctxt, 'enable_task', task=task)

    def disable_task(self, ctxt, task):
        cctxt = self.client.prepare(version=VERSION)
        cctxt.cast(ctxt, 'disable_task', task=task)
