import json

from oslo_log import log
from oslo_config import cfg

from report.client.httpclient import HttpClient
from report import utils

LOG = log.getLogger(__name__)
CONF = cfg.CONF


class ZeusClient(HttpClient):
    @staticmethod
    def from_url(url=None, **kwargs):
        if url is None:
            url = CONF.zeus.endpoint

        return HttpClient._getclient(ZeusClient, url, **kwargs)

    def get_data(self, url, method='GET', **q_kwargs):
        data = None
        url += '?'

        start = q_kwargs.pop('start', None)
        if start:
            url += 'q.field=timestamp&q.op=ge&q.value=%s&' % start

        end = q_kwargs.pop('end', None)
        if end:
            url += 'q.field=timestamp&q.op=le&q.value=%s&' % end

        for key, value in q_kwargs.items():
            if value:
                url += 'q.field=%s&q.value=%s&' % (key, value)

        # delete the last '&' or ''

        url = url[0:-1]

        headers = {}
        headers.update({'X-Auth-Token': utils.token()})

        try:
            response = self.request(
                url=url,
                headers=headers,
                method=method,
            )

            if response.status_code == 200:
                data = json.loads(response.content)
            else:
                LOG.error('get data failed! code:%d; msg:%s',
                          response.status_code, response.content)
        except Exception, e:
            LOG.error("Catch exception: %s", str(e))

        return data

    def get_events(self, **q_kwargs):
        url = '/v1/events'

        return self.get_data(url, **q_kwargs)

    def get_nodes(self, **q_kwargs):
        url = '/v1/nodes'

        return self.get_data(url, **q_kwargs)

    def get_vms(self, **q_kwargs):
        url = '/v1/vms'

        return self.get_data(url, **q_kwargs)

    def get_node(self, node_id):
        url = '/v1/nodes/' + node_id

        return self.get_data(url)

    def get_vm(self, vm_id):
        url = '/v1/vms/' + vm_id

        return self.get_data(url)

    def alarm_events(self, **q_kwargs):
        url = '/v1/alarmEvents'
        method = 'GET_ALL'

        return self.get_data(url, method=method, **q_kwargs)

    def get_resource(self, url, **q_kwargs):

        return self.get_data(url, **q_kwargs)
