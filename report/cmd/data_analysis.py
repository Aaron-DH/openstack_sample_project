import sys

from report import config
from report import service
from oslo_config import cfg
from oslo_log import log as logging

CONF = cfg.CONF
CONF.import_opt('data_topic', 'report.data_analysis.rpcapi')


def main():
    config.parse_args(sys.argv)
    logging.setup(cfg.CONF, 'report')
    """
    logging.setup(CONF, 'nova')
    utils.monkey_patch()
    objects.register_all()

    gmr.TextGuruMeditation.setup_autorun(version)
    """
    server = service.Service.create(binary='report-data',
                                    topic=CONF.data_topic)
    service.serve(server)
    service.wait()
