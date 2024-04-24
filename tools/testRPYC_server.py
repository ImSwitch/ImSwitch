import rpyc
import numpy as np
from rpyc.utils.server import OneShotServer


class HelloService(rpyc.Service):
    def get(self):
        return np.random.rand(3, 3)

    def remote_np(self):
        return np

if __name__ == "__main__":
    rpyc.lib.setup_logger()
    server = OneShotServer(HelloService, port=8122, protocol_config={'allow_public_attrs': True, 'allow_pickle': True})
    server.start()