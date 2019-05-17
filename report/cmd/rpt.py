# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Starter script for Nova Compute."""

import sys

from oslo_config import cfg

from report import config
from report import service
from oslo.config import cfg
from oslo_log import log as logging

CONF = cfg.CONF
CONF.import_opt('rpt_topic', 'report.rpt.rpcapi')


def main():
    config.parse_args(sys.argv)
    logging.setup(cfg.CONF, 'report')
    """
    logging.setup(CONF, 'nova')
    utils.monkey_patch()
    objects.register_all()

    gmr.TextGuruMeditation.setup_autorun(version)
    """
    server = service.Service.create(binary='rpt',
                                    topic='rpt')
    service.serve(server)
    service.wait()
