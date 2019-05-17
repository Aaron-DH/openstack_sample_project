from oslo_log import log as logging
import pecan
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from report.api.controller import resource
from report.api.controller.v1 import root as v1_root

LOG = logging.getLogger(__name__)

API_STATUS = wtypes.Enum(str, 'SUPPORTED', 'CURRENT', 'DEPRECATED')


class APIVersion(resource.Base):
    """API Version."""

    id = wtypes.text
    "The version identifier."

    status = API_STATUS
    "The status of the API (SUPPORTED, CURRENT or DEPRECATED)."

    link = resource.Link
    "The link to the versioned API."

    @classmethod
    def sample(cls):
        return cls(
            id='v1.0',
            status='CURRENT',
            link=resource.Link(
                target_name='v1',
                href='http://example.com:9777/v1'
            )
        )


class RootController(object):
    v1 = v1_root.Controller()

    @wsme_pecan.wsexpose([APIVersion])
    def index(self):
        LOG.debug("Fetching API versions.")

        host_url_v1 = '%s/%s' % (pecan.request.host_url, 'v1')
        api_v1 = APIVersion(
            id='v2.0',
            status='CURRENT',
            link=resource.Link(href=host_url_v1, target='v1')
        )

        return [api_v1]
