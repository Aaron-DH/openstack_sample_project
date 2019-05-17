from wsgiref import simple_server
import os

from oslo_config import cfg
from oslo_log import log as logging
from paste import deploy
import pecan

from report.api import hooks
from report.agent import rpcapi


LOG = logging.getLogger(__name__)
CONF = cfg.CONF
pecan_opts = [
    cfg.StrOpt('root',
               default='report.api.controller.root.RootController',
               help='Pecan root controller'),
    cfg.ListOpt('modules',
                default=["report.api"],
                help='A list of modules where pecan will search for '
                     'applications.'),
    cfg.BoolOpt('debug',
                default=True,
                help='Enables the ability to display tracebacks in the '
                     'browser and interactively debug during '
                     'development.'),
    cfg.BoolOpt('auth_enable',
                default=True,
                help='Enables user authentication in pecan.')
]

api_opts = [
    cfg.StrOpt('host',
               default='0.0.0.0',
               help='api host'),
    cfg.IntOpt('port',
               default=8899,
               help='api port')
]

CONF.register_opts(pecan_opts, group='pecan')
CONF.register_opts(api_opts, group='api')


def get_pecan_config():
    # Set up the pecan configuration.
    opts = CONF.pecan

    cfg_dict = {
        "app": {
            "root": opts.root,
            "modules": opts.modules,
            "debug": True,
            "auth_enable": opts.auth_enable
        }
    }

    return pecan.configuration.conf_from_dict(cfg_dict)


def setup_app(config=None, extra_hooks=None):
    if not config:
        config = get_pecan_config()

    app_conf = dict(config.app)

    rpcclient = rpcapi.AgentAPI()

    app_hooks = [hooks.DBHook(),
                 hooks.RPCHook(rpcclient)]

    app = pecan.make_app(
        app_conf.pop('root'),
        hooks=app_hooks,
        logging=getattr(config, 'logging', {}),
        **app_conf
    )

    return app


def load_app():
    # Build the WSGI app
    cfg_file = None
    cfg_path = cfg.CONF.api_paste_config
    if not os.path.isabs(cfg_path):
        cfg_file = CONF.find_file(cfg_path)
    elif os.path.exists(cfg_path):
        cfg_file = cfg_path

    if not cfg_file:
        raise cfg.ConfigFilesNotFoundError([cfg.CONF.api_paste_config])
    LOG.info("Full WSGI config used: %s" % cfg_file)
    return deploy.loadapp("config:" + cfg_file, name="reportapi")


def build_server():
    # Create the WSGI server and start it
    app = load_app()

    host = CONF.api.host
    port = CONF.api.port
    LOG.info('Starting server in PID %s', os.getpid())
    LOG.info("Configuration:")
    cfg.CONF.log_opt_values(LOG, logging.INFO)

    if host == '0.0.0.0':
        LOG.info('serving on 0.0.0.0:%(sport)s, view at http://127.0.0.1:%'
                 '(vport)s', {'sport': port, 'vport': port})
    else:
        LOG.info("serving on http://%(host)s:%(port)s",
                 {'host': host, 'port': port})

    server_cls = simple_server.WSGIServer
    handler_cls = simple_server.WSGIRequestHandler

    srv = simple_server.make_server(
        host,
        port,
        app)

    srv.serve_forever()


def app_factory(global_config, **local_conf):
    return setup_app()
