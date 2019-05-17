from oslo_config import cfg
from oslo_utils import importutils

from report.openstack.common import service
from report import wsgi
from report import rpc
from report import utils
from report import context
from report.i18n import _, _LE,  _LW
from oslo_log import log as logging
import oslo_messaging as messaging
import os
import sys

service_opts = [
    cfg.IntOpt('report_interval',
               default=10,
               help='Seconds between nodes reporting state to datastore'),
    cfg.BoolOpt('periodic_enable',
                default=True,
                help='Enable periodic tasks'),
    cfg.IntOpt('periodic_fuzzy_delay',
               default=60,
               help='Range of seconds to randomly delay when starting the'
                    ' periodic task scheduler to reduce stampeding.'
                    ' (Disable by setting to 0)'),
    cfg.ListOpt('enabled_ssl_apis',
                default=[],
                help='A list of APIs with enabled SSL'),
    cfg.StrOpt('reportapi_listen',
               default="0.0.0.0",
               help='The IP address on which the OpenStack API will listen.'),
    cfg.IntOpt('reportapi_listen_port',
               default=8888,
               help='The port on which the OpenStack API will listen.'),
    cfg.IntOpt('reportapi_workers',
               help='Number of workers for OpenStack API service. The default '
                    'will be the number of CPUs available.'),
    cfg.StrOpt('cert_manager',
               default='nova.cert.manager.CertManager',
               help='Full class name for the Manager for cert'),
    cfg.IntOpt('service_down_time',
               default=60,
               help='Maximum time since last check-in for up service'),
    cfg.StrOpt('data_manager',
               default='report.data_analysis.manager.DataManager',
               help='Full class name for the Manager for report'),
    cfg.StrOpt('agent_manager',
               default='report.agent.manager.AgentManager',
               help='Full class name for the AgentManager for report'),
    ]

CONF = cfg.CONF
CONF.register_opts(service_opts)
CONF.import_opt('host', 'report.netconf')

LOG = logging.getLogger(__name__)


class Service(service.Service):
    """Service object for binaries running on hosts.

    A service takes a manager and enables rpc by listening to queues based
    on topic. It also periodically runs tasks on the manager and reports
    it state to the database services table.
    """

    def __init__(self, host, binary, topic, manager, report_interval=None,
                 periodic_interval=None, periodic_fuzzy_delay=None,
                 service_name=None, *args, **kwargs):
        super(Service, self).__init__()

        self.host = host
        self.binary = binary
        self.topic = topic
        self.manager_class_name = manager
        manager_class = importutils.import_class(self.manager_class_name)
        self.manager = manager_class(*args, **kwargs)
        self.report_interval = report_interval
        self.periodic_interval = periodic_interval
        self.periodic_fuzzy_delay = periodic_fuzzy_delay
        self.basic_config_check()
        self.saved_args, self.saved_kwargs = args, kwargs
        self.timers = []

        # setup_profiler(binary, host)

    def start(self):
        """
        version_string = version.version_string()
        LOG.info(_LI('Starting %(topic)s node (version %(version_string)s)'),
                 {'topic': self.topic, 'version_string': version_string})
        self.model_disconnected = False
        self.manager.init_host()
        ctxt = context.get_admin_context()
        try:
            service_ref = db.service_get_by_args(ctxt,
                                                 self.host,
                                                 self.binary)
            self.service_id = service_ref['id']
        except exception.NotFound:
            self._create_service_ref(ctxt)

        LOG.debug("Creating RPC server for service %s", self.topic)
        """
        target = messaging.Target(topic=self.topic, server=self.host)
        endpoints = [self.manager]
        # endpoints.extend(mana.additional_endpoints)
        # serializer = objects_base.CinderObjectSerializer()
        self.rpcserver = rpc.get_server(target, endpoints)
        self.rpcserver.start()
        """
        self.manager.init_host_with_rpc()

        if self.report_interval:
            pulse = loopingcall.FixedIntervalLoopingCall(
                self.report_state)
            pulse.start(interval=self.report_interval,
                        initial_delay=self.report_interval)
            self.timers.append(pulse)

        if self.periodic_interval:
            if self.periodic_fuzzy_delay:
                initial_delay = random.randint(0, self.periodic_fuzzy_delay)
            else:
                initial_delay = None

            periodic = loopingcall.FixedIntervalLoopingCall(
                self.periodic_tasks)
            periodic.start(interval=self.periodic_interval,
                           initial_delay=initial_delay)
            self.timers.append(periodic)
        """

    def basic_config_check(self):
        """Perform basic config checks before starting service."""
        # Make sure report interval is less than service down time
        if self.report_interval:
            if CONF.service_down_time <= self.report_interval:
                new_down_time = int(self.report_interval * 2.5)
                LOG.warning(
                    _LW("Report interval must be less than service down "
                        "time. Current config service_down_time: "
                        "%(service_down_time)s, report_interval for this: "
                        "service is: %(report_interval)s. Setting global "
                        "service_down_time to: %(new_down_time)s"),
                    {'service_down_time': CONF.service_down_time,
                     'report_interval': self.report_interval,
                     'new_down_time': new_down_time})
                CONF.set_override('service_down_time', new_down_time)

    def _create_service_ref(self, context):
        """
        zone = CONF.storage_availability_zone
        service_ref = db.service_create(context,
                                        {'host': self.host,
                                         'binary': self.binary,
                                         'topic': self.topic,
                                         'report_count': 0,
                                         'availability_zone': zone})
        self.service_id = service_ref['id']
        """
        pass

    def __getattr__(self, key):
        manager = self.__dict__.get('manager', None)
        return getattr(manager, key)

    @classmethod
    def create(cls, host=None, binary=None, topic=None, manager=None,
               report_interval=None, periodic_interval=None,
               periodic_fuzzy_delay=None, service_name=None):
        """Instantiates class and passes back application object.

        :param host: defaults to CONF.host
        :param binary: defaults to basename of executable
        :param topic: defaults to bin_name - 'cinder-' part
        :param manager: defaults to CONF.<topic>_manager
        :param report_interval: defaults to CONF.report_interval
        :param periodic_interval: defaults to CONF.periodic_interval
        :param periodic_fuzzy_delay: defaults to CONF.periodic_fuzzy_delay

        """
        if not host:
            host = CONF.host
        if not binary:
            binary = os.path.basename(sys.argv[0])
        if not topic:
            topic = binary.rpartition('report-')[2]
        if not manager:
            manager_cls = ('%s_manager' %
                           binary.rpartition('report-')[2])
            manager = CONF.get(manager_cls, None)
        """
        if report_interval is None:
            report_interval = CONF.report_interval
        if periodic_interval is None:
            periodic_interval = CONF.periodic_interval
        if periodic_fuzzy_delay is None:
            periodic_fuzzy_delay = CONF.periodic_fuzzy_delay
        """
        service_obj = cls(host, binary, topic, manager,
                          report_interval=report_interval,
                          periodic_interval=periodic_interval,
                          periodic_fuzzy_delay=periodic_fuzzy_delay,
                          service_name=service_name)

        return service_obj

    def kill(self):
        """Destroy the service object in the datastore."""
        self.stop()
        """
        try:
            self.service_ref.destroy()
        except exception.NotFound:
            LOG.warning(_LW('Service killed that has no database entry'))
        """
    def stop(self):
        try:
            self.rpcserver.stop()
            self.rpcserver.wait()
        except Exception:
            pass
        """
        try:
            self.manager.cleanup_host()
        except Exception:
            LOG.exception(_LE('Service error occurred during cleanup_host'))
            pass
        """
        super(Service, self).stop()

    def periodic_tasks(self, raise_on_error=False):
        """Tasks to be run at a periodic interval."""
        ctxt = context.get_admin_context()
        return self.manager.periodic_tasks(ctxt, raise_on_error=raise_on_error)

    def basic_config_check(self):
        """Perform basic config checks before starting processing."""
        # Make sure the tempdir exists and is writable
        try:
            with utils.tempdir():
                pass
        except Exception as e:
            LOG.error(_LE('Temporary directory is invalid: %s'), e)
            sys.exit(1)


class WSGIService(object):
    """Provides ability to launch API from a 'paste' configuration."""

    def __init__(self, name, loader=None, use_ssl=False, max_url_len=None):
        """Initialize, but do not start the WSGI server.

        :param name: The name of the WSGI server given to the loader.
        :param loader: Loads the WSGI application using the given name.
        :returns: None

        """
        self.name = name
        self.manager = self._get_manager()
        self.loader = loader or wsgi.Loader()
        self.app = self.loader.load_app(name)
        self.host = getattr(CONF, '%s_listen' % name, "0.0.0.0")
        self.port = getattr(CONF, '%s_listen_port' % name, 0)
        self.workers = (getattr(CONF, '%s_workers' % name, 1))
        self.use_ssl = use_ssl
        self.server = wsgi.Server(name,
                                  self.app,
                                  host=self.host,
                                  port=self.port,
                                  use_ssl=self.use_ssl,
                                  max_url_len=max_url_len)
        # Pull back actual port used
        self.port = self.server.port
        self.backdoor_port = None

    def reset(self):
        """Reset server greenpool size to default.

        :returns: None

        """
        self.server.reset()

    def _get_manager(self):
        """Initialize a Manager object appropriate for this service.

        Use the service name to look up a Manager subclass from the
        configuration and initialize an instance. If no class name
        is configured, just return None.

        :returns: a Manager instance, or None.

        """
        fl = '%s_manager' % self.name
        if fl not in CONF:
            return None

        manager_class_name = CONF.get(fl, None)
        if not manager_class_name:
            return None

        manager_class = importutils.import_class(manager_class_name)
        return manager_class()

    def start(self):
        """Start serving this service using loaded configuration.

        Also, retrieve updated port number in case '0' was passed in, which
        indicates a random port should be used.

        :returns: None

        """
        if self.manager:
            self.manager.init_host()
            self.manager.pre_start_hook()
            if self.backdoor_port is not None:
                self.manager.backdoor_port = self.backdoor_port
        self.server.start()
        if self.manager:
            self.manager.post_start_hook()

    def stop(self):
        """Stop serving this API.

        :returns: None

        """
        self.server.stop()

    def wait(self):
        """Wait for the service to stop serving this API.

        :returns: None

        """
        self.server.wait()


def process_launcher():
    return service.ProcessLauncher()


# NOTE(vish): the global launcher is to maintain the existing
#             functionality of calling service.serve +
#             service.wait
_launcher = None


def serve(server, workers=None):
    global _launcher
    if _launcher:
        raise RuntimeError(('serve() can only be called once'))

    _launcher = service.launch(server, workers=workers)


def wait():
    _launcher.wait()


_DEFAULT_LOG_LEVELS = ['amqp=WARN', 'amqplib=WARN', 'boto=WARN',
                       'qpid=WARN', 'sqlalchemy=WARN',
                       'oslo_messaging=INFO', 'iso8601=WARN',
                       'requests.packages.urllib3.connectionpool=WARN',
                       'urllib3.connectionpool=WARN', 'websocket=WARN',
                       'keystonemiddleware=WARN', 'routes.middleware=WARN',
                       'stevedore=WARN', 'glanceclient=WARN']

_DEFAULT_LOGGING_CONTEXT_FORMAT = ('%(asctime)s.%(msecs)03d %(process)d '
                                   '%(levelname)s %(name)s [%(request_id)s '
                                   '%(user_identity)s] %(instance)s'
                                   '%(message)s')


def prepare_service(argv=None, config_files=None):
    logging.set_defaults(_DEFAULT_LOGGING_CONTEXT_FORMAT, _DEFAULT_LOG_LEVELS)
    logging.register_options(cfg.CONF)
    if argv is None:
        argv = sys.argv
    cfg.CONF(argv[1:], project='report', default_config_files=config_files)
    rpc.set_defaults(control_exchange='report')
    rpc.init(cfg.CONF)
    logging.setup(cfg.CONF, 'report')
