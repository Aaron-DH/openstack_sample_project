import json

from oslo_log import log
from oslo_config import cfg

from report.client.httpclient import HttpClient
from report import utils

LOG = log.getLogger(__name__)
CONF = cfg.CONF


class NovaClient(HttpClient):
    @staticmethod
    def from_url(url=None, **kwargs):
        if url is None:
            url = CONF.nova.endpoint

        return HttpClient._getclient(NovaClient, url, **kwargs)

    def get_flavor(self, tenant_id, flavor_id):
        data = None
        url = '/v2/%s/flavors/%s' % (tenant_id, flavor_id)

        headers = {}
        headers.update({'X-Auth-Token': utils.token()})

        try:
            response = self.request(
                url=url,
                headers=headers
            )

            if response.status_code == 200:
                data = json.loads(response.content)
            else:
                LOG.error('get data failed! code:%d; msg:%s',
                          response.status_code, response.content)
        except Exception, e:
            LOG.error("Catch exception: %s", str(e))

        return data

    def get_flavors(self):
        data = None
        url = '/v2/%s/flavors/detail' % CONF.admininfo.tenantID

        headers = {}
        headers.update({'X-Auth-Token': utils.token()})

        try:
            response = self.request(
                url=url,
                headers=headers
            )

            if response.status_code == 200:
                data = json.loads(response.content)
            else:
                LOG.error('get data failed! code:%d; msg:%s',
                          response.status_code, response.content)
        except Exception, e:
            LOG.error("Catch exception: %s", str(e))

        return data

    def get_quota(self, tenant_id):
        data = None
        url = '/v2/%s/os-quota-sets/%s' % (tenant_id, tenant_id)
        headers = {}
        headers.update({'X-Auth-Token': utils.token()})

        try:
            response = self.request(
                url=url,
                headers=headers
            )

            if response.status_code == 200:
                data = json.loads(response.content)
            else:
                LOG.error('get data failed! code:%d; msg:%s',
                          response.status_code, response.content)
        except Exception, e:
            LOG.error("Catch exception: %s", str(e))

        return data

    def list_instances(self, tenant_id=None, all_tenants=True):
        data = None
        if tenant_id is None:
            tenant_id = CONF.admininfo.tenantID

        url = '/v2/%s/servers/detail' % tenant_id
        if all_tenants:
            url = url + '?all_tenants=1'

        headers = {}
        headers.update({'X-Auth-Token': utils.token()})

        try:
            response = self.request(
                url=url,
                headers=headers
            )

            if response.status_code == 200:
                data = json.loads(response.content)
            else:
                LOG.error('get data failed! code:%d; msg:%s',
                          response.status_code, response.content)
        except Exception, e:
            LOG.error("Catch exception: %s", str(e))
        return data
