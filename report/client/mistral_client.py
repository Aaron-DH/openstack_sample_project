import json

from oslo_config import cfg
from oslo_log import log

from report.client.httpclient import HttpClient

CONF = cfg.CONF
LOG = log.getLogger(__name__)


class MistralClient(HttpClient):
    @staticmethod
    def from_url(url=None, **kwargs):
        if url is None:
            url = CONF.zeus.endpoint

        return HttpClient._getclient(MistralClient, url, **kwargs)
    def action_list(self):
        url = '/v2/actions'
        response = self.request(
            url=url,
            method='GET',
            headers={
            'Content-type': 'application/json',
            }
        )
        return (response.status_code, response.content)

    def create_cron_trigger(self, cron_trigger):
        url = '/v2/cron_triggers'
        response = self.request(
            url=url,
            method='POST',
            data=cron_trigger,
            headers={
            'Content-type': 'application/json',
            }
        )
        return (response.status_code, response.content)

    def delete_cron_trigger(self, trigger_name):
        url = '/v2/cron_triggers/%s' % trigger_name
        response = self.request(
            url=url,
            method='DELETE',
            headers={
            'Content-type': 'application/json',
            }
        )
        return (response.status_code, response.content)

    def create_workflow(self, workflow):
        url = '/v2/workflows'
        response = self.request(
            url=url,
            method='POST',
            data=workflow,
            headers={
            'Content-type': 'application/json',
            }
        )
        return (response.status_code, response.content)
    def delete_workflow(self):
        pass

if __name__ == "__main__":
    cli = MistralClient(host='192.168.138.71', port=8989)
    # print cli.action_list()
    data = dict(
        name="test_9",
        workflow_name="echo_flow",
        workflow_input='{"echo_str":"test"}',
        first_execution_time='2015-11-17 15:24',
        pattern='59 03 09 12 *',
        remaining_executions=2

    )
    print cli.create_cron_trigger(data)
    # print cli.delete_cron_trigger('test')