#
# Copyright 2013 Julien Danjou
# Copyright 2014 Red Hat, Inc
#
# Authors: Julien Danjou <julien@danjou.info>
#          Eoghan Glynn <eglynn@redhat.com>
#          Nejc Saje <nsaje@redhat.com>
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

import random

from oslo_config import cfg
from oslo_log import log
from stevedore import extension
from report.openstack.common import service as os_service

LOG = log.getLogger(__name__)

OPTS = [
    cfg.IntOpt('shuffle_time_before_polling_task',
               default=0,
               help='To reduce large requests at same time to Nova or other '
                    'components from different compute agents, shuffle '
                    'start time of polling task.'),
]

cfg.CONF.register_opts(OPTS)


class AgentManager(os_service.Service):

    def __init__(self):
        # features of using coordination and pollster-list are exclusive, and
        # cannot be used at one moment to avoid both samples duplication and
        # samples being lost

        super(AgentManager, self).__init__()

        namespace = "report.tasks"
        # we'll have default ['compute', 'central'] here if no namespaces will
        # be passed
        self.extensions = self._extensions(namespace).extensions
        for extension in self.extensions:
            LOG.info("load extension:, %s", str(extension))

    @staticmethod
    def _extensions(namespace):

        """
        def _catch_extension_load_error(mgr, ep, exc):
            # Extension raising ExtensionLoadError can be ignored,
            # and ignore anything we can't import as a safety measure.
            if isinstance(exc, plugin_base.ExtensionLoadError):
                LOG.error(_("Skip loading extension for %s") % ep.name)
                return
            if isinstance(exc, ImportError):
                LOG.error(
                    _("Failed to import extension for %(name)s: %(error)s"),
                    {'name': ep.name, 'error': exc},
                )
                return
            raise exc
        """

        return extension.ExtensionManager(
            namespace=namespace,
            invoke_on_load=True,
            # on_load_failure_callback=_catch_extension_load_error,
        )

    def start(self):
        # allow time for coordination if necessary
        delay_start = None

        # set shuffle time before polling task if necessary
        delay_polling_time = random.randint(
            0, cfg.CONF.shuffle_time_before_polling_task)

        for extension in self.extensions:
            task = extension.obj
            delay_time = task.interval
            self.tg.add_timer(task.interval,
                              self.interval_task,
                              initial_delay=delay_time,
                              task=task)

    def stop(self):
        super(AgentManager, self).stop()

    @staticmethod
    def interval_task(task):
        task.report()
