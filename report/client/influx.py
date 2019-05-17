
from influxdb.client import InfluxDBClusterClient

from oslo_config import cfg
from oslo_log import log


LOG = log.getLogger(__name__)
CONF = cfg.CONF

influxdb_opts = {
    cfg.StrOpt('influxdb_url',
               secret=True,
               help='influxdb url'),
}

CONF.register_opts(influxdb_opts, 'influxdb')


class Client(object):
    def __init__(self, dsn_url=None):
        """Construct a new InfluxDBClient object."""

        if dsn_url is None:
            dsn_url = CONF.influxdb.influxdb_url

        self.influx = InfluxDBClusterClient.from_DSN(dsn_url)

    def get_data_byurl(self, url):
        result = None
        try:
            resultset = self.influx.query(url)
            result = resultset.raw.get('series', None)
        except Exception, e:
            pass

        if result is None:
            LOG.warn("Failed to get data from influxdb, url: %s", url)

        return result
