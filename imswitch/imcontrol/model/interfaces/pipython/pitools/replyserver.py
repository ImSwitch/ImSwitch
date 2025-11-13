#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Mock object for a PI controller that receives commands and sends answers over a socket."""

from collections import deque
from logging import debug, error
from threading import Thread
from time import sleep

try:
    from socketserver import BaseRequestHandler, ThreadingTCPServer
except ImportError:
    from SocketServer import BaseRequestHandler, ThreadingTCPServer

# Invalid class name "basestring"  pylint: disable=C0103
# Redefining built-in 'basestring' pylint: disable=W0622
try:
    basestring
except NameError:
    basestring = str

__signature__ = 0xb4d12199ebfd6d1dac6bd07681732a4a


def startup(host, port):
    """Create a ReplyHandler object that listens on the according port.
    @param host : IP address to connect to as string.
    @param port : Port to connect to as integer.
    @return : ThreadingTCPServer object.
    """
    server = ThreadingTCPServer((host, port), ReplyHandler)
    thread = Thread(target=server.serve_forever)
    thread.daemon = True  # exit server thread when main thread terminates
    thread.start()
    return server


def checkstring(cmd, answer):
    """Verify types, if empty, if EOL character is present. Raise assertion error.
    @param cmd : Will be verified to be none empty string with valid EOL character.
    @param answer : Will be verified to be string.
    """
    assert isinstance(cmd, basestring), 'type of cmd is not string'
    assert isinstance(answer, basestring), 'type of answer is not string'
    assert str(cmd), 'empty cmd string'
    assert ord(str(cmd[-1:])) < 32, 'invalid EOL character in cmd string'


class ReplyHandler(BaseRequestHandler):
    """Verify received data send the according answer."""

    queue = deque()  # received cmd is compared to first item and the according answer is sent
    static = []  # received cmd is compared to any item and the according answer is sent
    delay = 0  # milliseconds between sent lines
    rotate = False  # if True, received item is not removed but put at the end of the queue
    errorbuf = ''  # first error message if queue is empty or the received line does not match

    def handle(self):
        """Receive data and send answers. Verify starts on characters with ASCII code < 32."""
        debug('ReplyHandler: starting')
        rcvbuf = ''
        while True:
            rcvbuf += self.request.recv(1).decode(encoding='cp1252', errors='ignore')
            if not rcvbuf:  # EOF received
                break
            if ord(rcvbuf[-1:]) < 32:
                rcvbuf = self.__verify_answer(rcvbuf)
        debug('ReplyHandler: shutting down')

    def __verify_answer(self, rcv):
        """Verify 'rcv' by "queue", then by "static", then set error flag.
        @param rcv : String to verify.
        @return : Empty string.
        """
        debug('ReplyHandler.receive: %r', rcv)
        if self.__send_from_queue(rcv):
            return ''
        if self.__send_from_static(rcv):
            return ''
        if not self.queue:
            self.__seterror('svr queue is empty but received %r' % rcv)
        else:
            self.__seterror('svr expected %r but received %r' % (self.queue[0]['cmd'], rcv))
        if rcv.find('?') > -1:
            self.request.sendall('%s\n' % self.server.RequestHandlerClass.errorbuf)  # to prevent GCS timeout error
        return ''

    def __send_from_queue(self, rcv):
        """Check if rcv is first queue element and send answer.
        If 'rotate' is False the item is removed from queue, else it is put at the end of the queue.
        @param rcv : Command string that has been received.
        @return : True if an answer from queue has been sent.
        """
        try:
            if rcv == self.queue[0]['cmd']:
                answer = self.queue[0]['answer']
                if self.rotate:
                    self.queue.rotate(-1)
                else:
                    self.queue.popleft()
                self.__send(answer, 'queue')
                return True
        except IndexError:
            return False
        return False

    def __send_from_static(self, rcv):
        """Send answer from 'static'.
        @param rcv : Command string that has been received.
        @return : True if an answer from 'static' has been sent.
        """
        for item in self.static:
            if rcv == item['cmd']:
                self.__send(item['answer'], 'static')
                return True
        return False

    def __send(self, tosend, source):
        """Send lines in 'tosend' with 'delay'.
        @param tosend : This string is sent line by line.
        @param source : Only for logging, can be "queue" or "static".
        """
        for line in tosend.splitlines(True):
            if self.delay:
                debug('ReplyHandler.send: delay answer for %d ms', self.delay)
                sleep(self.delay / 1000.0)
            debug('ReplyHandler.send(%s): %r', source, line)
            self.request.sendall(line.encode('cp1252'))

    def __seterror(self, message):
        """Log ERROR 'message' and store 'message' in 'errorbuf' if it is empty.
        @param message : Error message as string.
        """
        error(message)
        if not self.server.RequestHandlerClass.errorbuf:
            self.server.RequestHandlerClass.errorbuf = message


# Class inherits from object, can be safely removed from bases in python3 pylint: disable=R0205
class ReplyServer(object):
    """Wait for a command and send the according answer, can be used as context manager."""

    def __init__(self, host='localhost', port=50000):
        """Wait for a command and send the according answer. Command/answer pairs are appended to
        a FIFO queue. Call ReplyServer.isok after communication.
        @param host : IP address to connect to as string.
        @param port : Port to connect to as integer.
        """
        debug('create an instance of ReplyServer(host=%r, port=%s)', host, port)
        self.__server = startup(host, port)
        self.__handler = self.__server.RequestHandlerClass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Shut down server and close connection."""
        self.clear()
        debug('ReplyServer.close')
        self.rotate = False
        self.delay = 0
        self.__server.shutdown()
        self.__server.server_close()

    def queue(self, cmd, answer=''):
        """Append new cmd and answer pair to "queue". Remember to add "\n" to cmd and answer.
        @param cmd : Command that is received as string.
        @param answer : According answer that is sent back as string.
        """
        checkstring(cmd, answer)
        self.__handler.queue.append({'cmd': cmd, 'answer': answer})
        debug('ReplyServer.queue: %r -> %r (%d)', cmd, answer, len(self.__handler.queue))

    def append(self, cmd, answer=''):
        """Append new cmd and answer pair to "static". Remember to add "\n" to cmd and answer.
        @param cmd : Command that is received as string.
        @param answer : According answer that is sent back as string.
        """
        checkstring(cmd, answer)
        self.__handler.static.append({'cmd': cmd, 'answer': answer})
        debug('ReplyServer.append: %r -> %r (%d)', cmd, answer, len(self.__handler.static))

    def clear(self):
        """Clear "queue" and "static" if they are not empty."""
        debug('ReplyServer.clear')
        if self.__handler.queue:
            self.__handler.queue.clear()
        if self.__handler.static:
            self.__handler.static = []

    @property
    def delay(self):
        """Before each line to send back to the host this delay in millisconde is applied."""
        return self.__handler.delay

    @delay.setter
    def delay(self, delay):
        """Before each line to send back to the host this delay in millisconde is applied."""
        delay = int(delay)
        if self.__handler.delay != int(delay):
            self.__handler.delay = delay
            debug('ReplyServer.delay: set to %d ms', delay)

    @property
    def rotate(self):
        """Get rotate mode, can be True or False. If False the first item in the queue will be
        popped on request. If True the queue rotates, i.e. no item in the queue will be deleted
        and you must self.clear() the queue manually afterwards.
        """
        return self.__handler.rotate

    @rotate.setter
    def rotate(self, mode):
        """Set rotate mode as bool."""
        mode = bool(mode)
        if self.__handler.rotate != mode:
            self.__handler.rotate = mode
            debug('ReplyServer.rotate: set to %s', mode)

    @property
    def check(self):
        """Clear "static" and return True if the server received all commands as expected."""
        if self.__handler.errorbuf:
            assert 0, self.__handler.errorbuf
        if self.__handler.queue:
            msg = 'svr message queue is not empty:\n'
            for item in self.__handler.queue:
                msg += '%r -> %r\n' % (item['cmd'], item['answer'])
            assert 0, msg.strip()
        self.__handler.static = []
        debug('ReplyServer.check: ok')
        return True
