import sys
import os

from oslo_config import cfg
from oslo_log import log as logging
from wsgiref import simple_server

from report.api import app
from report import config


CONF = cfg.CONF

LOG = logging.getLogger(__name__)


def main():

    host = '0.0.0.0'
    port = 8899
    config.parse_args(sys.argv)
    logging.setup(cfg.CONF, "report")
    logging.set_defaults(default_log_levels=logging.DEBUG)
    application = app.setup_app()
    srv = simple_server.make_server(host, port, application)
    LOG.debug("Report API is serving on http://%s:%d (PID=%d)" %
             (host, port, os.getpid()))
    srv.serve_forever()



if __name__ == '__main__':
    main()
