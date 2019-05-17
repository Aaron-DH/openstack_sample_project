import pecan
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from report.api.controller import resource
from report.api.controller.v1 import rpttasks
from report.api.controller.v1 import rptfiles



class RootResource(resource.Base):
    """Root resource for API version 1.

    It references all other resources belonging to the API.
    """

    uri = wtypes.text

    # TODO(everyone): what else do we need here?
    # TODO(everyone): we need to collect all the links from API v2.0
    #                 and provide them.


class Controller(object):
    """API root controller for version 2."""

    rpttasks = rpttasks.RptTasksController()
    rptfiles = rptfiles.RptFilesController()

    @wsme_pecan.wsexpose(RootResource)
    def index(self):
        return RootResource(uri='%s/%s' % (pecan.request.host_url, 'v1'))