from oslo_log import log
from oslo_config import cfg
from report import storage
from pecan import hooks

LOG = log.getLogger(__name__)


class RPCHook(hooks.PecanHook):
    def __init__(self, rcp_client):
        self._rpc_client = rcp_client

    def before(self, state):
        state.request.rpc_client = self._rpc_client


class DBHook(hooks.PecanHook):

    def __init__(self):
        self.storage_connection = storage.get_connection_from_config(cfg.CONF)

        if not self.storage_connection:
            raise Exception("Api failed to start. "
                            "Failed to connect to database.")

    def before(self, state):
        state.request.storage_conn = self.storage_connection
