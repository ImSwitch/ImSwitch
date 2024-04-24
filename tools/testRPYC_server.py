import rpyc
from rpyc.utils.server import ThreadedServer

class ArithmeticService(rpyc.Service):
    """ A simple arithmetic service """
    def exposed_add(self, x, y):
        """ Returns the sum of x and y """
        return x + y

    def exposed_subtract(self, x, y):
        """ Returns the difference of x and y """
        return x - y

def start_server():
    # Create a threaded server on localhost port 18812
    t = ThreadedServer(ArithmeticService, port=18812, auto_register=False)
    t.start()

if __name__ == "__main__":
    start_server()
