# -*- coding: utf-8 -*-
"""
Python Httpclient for Sending http requests
"""

import json
import requests
import requests.exceptions

from oslo_log import log
from oslo_config import cfg
from oslo_utils import netutils


admin_opts = [
    cfg.StrOpt('username',
               help='username'),
    cfg.StrOpt('password',
               help='password'),
    cfg.StrOpt('tenantName',
               help='tenantName'),
    cfg.StrOpt('tenantID',
               help='tenantID')
]

keystone_opts = [
    cfg.StrOpt('endpoint',
               help='keystone endpoint')
]

nova_opts = [
    cfg.StrOpt('endpoint',
               help='nova endpoint')
]

zeus_opts = [
    cfg.StrOpt('endpoint',
               help='zeus endpoint')
]

mistral_opts = [
    cfg.StrOpt('endpoint',
               default='http://192.168.138.71:8989',
               help='mistral endpoint')
]

CONF = cfg.CONF
CONF.register_opts(admin_opts, 'admininfo')
CONF.register_opts(keystone_opts, 'keystone')
CONF.register_opts(nova_opts, 'nova')
CONF.register_opts(zeus_opts, 'zeus')
CONF.register_opts(mistral_opts, 'mistral')

LOG = log.getLogger(__name__)


class HttpClient(object):
    """
    :param host: hostname to connect to httpserver, defaults to 'localhost'
    :type host: str
    :param port: port to connect to httpserver, default to 80
    :type port: int
    :param ssl: use https instead of http , defaults to False
    :type ssl: bool
    :param verify_ssl: verify SSL certificates for HTTPS requests, defaults to
        False
    :type verify_ssl: bool
    :param timeout: number of seconds Requests will wait for your client to
        establish a connection, defaults to None
    :type timeout: int
    """
    def __init__(self,
                 host='localhost',
                 port=80,
                 ssl=False,
                 verify_ssl=False,
                 timeout=10,
                 ):
        self._host = host
        self._port = port
        self._timeout = timeout

        self._verify_ssl = verify_ssl

        self._session = requests.Session()

        self._scheme = "http"

        if ssl is True:
            self._scheme = "https"

        self._baseurl = "{0}://{1}:{2}".format(
            self._scheme,
            self._host,
            self._port)

        self._headers = {
            'Content-type': 'application/json'
        }

    @staticmethod
    def _getclient(clientclass, url, **kwargs):
        result = netutils.urlsplit(url)

        init_args = {}
        hostinfo = result.netloc

        if ':' in hostinfo:
            host, port = hostinfo.split(':')
        else:
            host = hostinfo
            port = 80

        scheme = result.scheme

        init_args = dict(
            host=host,
            port=port
        )

        init_args.update(kwargs)

        return clientclass(**init_args)

    @staticmethod
    def from_URL(url=None, **kwargs):
        return HttpClient._getclient(HttpClient, url, **kwargs)

    def request(self, url, method='GET', params=None, data=None, headers=None):
        """Make a HTTP request to the API.

        :param url: the path of the HTTP request, e.g. write, query, etc.
        :type url: str
        :param method: the HTTP method for the request, defaults to GET
        :type method: str
        :param params: additional parameters for the request, defaults to None
        :type params: dict
        :param data: the data of the request, defaults to None
        :type data: str
        :returns: the response from the request
        """
        # url = "{0}/{1}/{2}".format(self._baseurl, self.api_version, url)
        url = "{0}{1}".format(self._baseurl, url)

        header = self._headers
        if headers is not None:
            header.update(headers)

        if params is None:
            params = {}

        if isinstance(data, (dict, list)):
            data = json.dumps(data)

        # Try to send the request a maximum of three times. (see #103)
        # TODO (aviau): Make this configurable.
        for i in range(0, 3):
            try:
                response = self._session.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    headers=header,
                    verify=self._verify_ssl,
                    timeout=self._timeout
                )
                break
            except requests.exceptions.ConnectionError as e:
                if i < 2:
                    continue
                else:
                    raise e

        return response
