import json

from oslo_config import cfg
from oslo_log import log

from report.client.httpclient import HttpClient

CONF = cfg.CONF
LOG = log.getLogger(__name__)


class KeystoneClient(HttpClient):
    @staticmethod
    def from_url(url=None, **kwargs):
        if url is None:
            url = CONF.keystone.endpoint

        return HttpClient._getclient(KeystoneClient, url, **kwargs)

    def get_token(self, username=None, password=None, tenantName=None):
        """
        get auth token from keystone
        """
        token = None

        username = CONF.admininfo.username if username is None else username
        password = CONF.admininfo.password if password is None else password
        tenantName = (CONF.admininfo.tenantName if
                      tenantName is None else tenantName)

        url = '/v2.0/tokens'
        passwordCredentials = dict(username=username,
                                   password=password)
        auth = dict(tenantName=tenantName,
                    passwordCredentials=passwordCredentials)

        data = dict(auth=auth)

        try:
            response = self.request(
                url=url,
                method="POST",
                data=data
            )

            if response.status_code == 200:
                resinfo = json.loads(response.content)
                token = resinfo['access']['token']['id']
            else:
                LOG.error('get token failed! code:%d; msg:%s',
                          response.status_code, response.content)

        except Exception, e:
            LOG.error("Catch exception: %s", str(e))

        return token

    def get_users(self):
        url = '/v2.0/users'

        user_info = None
        headers = {
            'Content-Type': 'application/json',
            'X-Auth-Token': self.from_url().get_token()
            }

        try:
            response = self.request(
                url=url,
                headers=headers,
                method='GET',
            )

            if response.status_code == 200:
                user_info = json.loads(response.content)
            else:
                LOG.error('get user failed! code:%d; msg:%s',
                          response.status_code, response.content)
        except Exception, e:
            LOG.error("Catch exception: %s", str(e))

        return user_info

    def get_user(self, user_id):
        url = '/v2.0/users/' + user_id

        user_info = None
        headers = {
            'Content-Type': 'application/json',
            'X-Auth-Token': self.from_url().get_token()
            }

        try:
            response = self.request(
                url=url,
                headers=headers,
                method='GET',
            )

            if response.status_code == 200:
                user_info = json.loads(response.content)
            else:
                LOG.error('get user failed! code:%d; msg:%s',
                          response.status_code, response.content)
        except Exception, e:
            LOG.error("Catch exception: %s", str(e))

        return user_info
