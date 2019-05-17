"""
Common Auth Middleware.

"""

from oslo_config import cfg
from oslo_log import log as logging
import webob.dec
import webob.exc
from report import wsgi
from oslo_middleware import request_id
from oslo_serialization import jsonutils
from report import context
from report.i18n import _
import keystonemiddleware.auth_token
# import oslo_middleware.request_id
import novaclient

auth_opts = [
    cfg.BoolOpt('api_rate_limit',
                default=False,
                help='Whether to use per-user rate limiting for the api. '
                     'This option is only used by v2 api. Rate limiting '
                     'is removed from v3 api.'),
    cfg.StrOpt('auth_strategy',
               default='keystone',
               help='''
The strategy to use for auth: keystone, noauth (deprecated), or
noauth2. Both noauth and noauth2 are designed for testing only, as
they do no actual credential checking. noauth provides administrative
credentials regardless of the passed in user, noauth2 only does if
'admin' is specified as the username.
'''),
    cfg.BoolOpt('use_forwarded_for',
                default=False,
                help='Treat X-Forwarded-For as the canonical remote address. '
                     'Only enable this if you have a sanitizing proxy.'),
]

CONF = cfg.CONF
CONF.register_opts(auth_opts)

LOG = logging.getLogger(__name__)


class TestFilter(wsgi.Middleware):
    @webob.dec.wsgify(RequestClass=wsgi.Request)
    def __call__(self, req):
        LOG.debug("Call TestFilter")
        return self.application


class ReportKeystoneContext(wsgi.Middleware):
    """Make a request context from keystone headers."""

    @webob.dec.wsgify(RequestClass=wsgi.Request)
    def __call__(self, req):
        user_id = req.headers.get('X_USER')
        user_id = req.headers.get('X_USER_ID', user_id)
        if user_id is None:
            LOG.debug("Neither X_USER_ID nor X_USER found in request")
            # return webob.exc.HTTPUnauthorized()

        roles = self._get_roles(req)
        """
        if 'X_TENANT_ID' in req.headers:
            # This is the new header since Keystone went to ID/Name
            project_id = req.headers['X_TENANT_ID']
        else:
            # This is for legacy compatibility
            project_id = req.headers['X_TENANT']
        """
        project_id = None

        project_name = req.headers.get('X_TENANT_NAME')
        user_name = req.headers.get('X_USER_NAME')

        req_id = req.environ.get(request_id.ENV_REQUEST_ID)

        # Get the auth token
        auth_token = req.headers.get('X_AUTH_TOKEN',
                                     req.headers.get('X_STORAGE_TOKEN'))

        # Build a context, including the auth_token...
        remote_address = req.remote_addr
        if CONF.use_forwarded_for:
            remote_address = req.headers.get('X-Forwarded-For', remote_address)

        service_catalog = None
        if req.headers.get('X_SERVICE_CATALOG') is not None:
            try:
                catalog_header = req.headers.get('X_SERVICE_CATALOG')
                service_catalog = jsonutils.loads(catalog_header)
            except ValueError:
                raise webob.exc.HTTPInternalServerError(_('Invalid service catalog json.'))

        # NOTE(jamielennox): This is a full auth plugin set by auth_token
        # middleware in newer versions.
        user_auth_plugin = req.environ.get('keystone.token_auth')

        ctx = context.RequestContext(user_id,
                                     project_id,
                                     user_name=user_name,
                                     project_name=project_name,
                                     roles=roles,
                                     auth_token=auth_token,
                                     remote_address=remote_address,
                                     service_catalog=service_catalog,
                                     request_id=req_id,
                                     user_auth_plugin=user_auth_plugin)

        req.environ['report.context'] = ctx
        return self.application

    def _get_roles(self, req):
        """Get the list of roles."""
        roles = req.headers.get('X_ROLES', '')
        return [r.strip() for r in roles.split(',')]
