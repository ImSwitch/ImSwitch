from abc import ABCMeta
from pyqtgraph.Qt import QtCore
import imswitch.imcommon.framework.base as base


class QObjectMeta(type(QtCore.QObject), ABCMeta):
    pass


class Mutex(QtCore.QMutex, base.Mutex, metaclass=QObjectMeta):
    pass


class Signal(base.Signal):
    def __new__(cls, *argtypes) -> base.Signal:
        return QtCore.Signal(*argtypes)


class SignalInterface(QtCore.QObject, base.SignalInterface, metaclass=QObjectMeta):
    pass


class Thread(QtCore.QThread, base.Thread, metaclass=QObjectMeta):
    pass


class Timer(QtCore.QTimer, base.Timer, metaclass=QObjectMeta):
    pass


class Worker(QtCore.QObject, base.Worker, metaclass=QObjectMeta):
    pass


class FrameworkUtils(base.FrameworkUtils):
    @staticmethod
    def processPendingEventsCurrThread():
        QtCore.QAbstractEventDispatcher.instance(
            QtCore.QThread.currentThread()
        ).processEvents(QtCore.QEventLoop.AllEvents)
