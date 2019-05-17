from oslo_config import cfg
from report import service
from report.agent import manager
from oslo_log import log as logging
from oslo_config import cfg

import sys


CONF = cfg.CONF
CONF.import_opt('report_agent_topic', 'report.agent.rpcapi')


def main():
    service.prepare_service()
    server = service.Service.create(binary='report-agent',
                                    topic=CONF.report_agent_topic)
    service.serve(server)
    service.wait()
