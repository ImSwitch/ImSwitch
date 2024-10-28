from typing import TYPE_CHECKING
from psygnal import SignalInstance, emit_queued
from functools import lru_cache
import asyncio
import threading
import imswitch.imcommon.framework.base as abstract

if TYPE_CHECKING:
    from typing import Tuple, Callable, Any, Union

class Mutex(abstract.Mutex):
    """ Wrapper around the `threading.Lock` class. 
    """
    def __init__(self) -> None:
        self.__lock = threading.Lock()
    
    def lock(self) -> None:
        self.__lock.acquire()
    
    def unlock(self) -> None:
        self.__lock.release()

class Signal(SignalInstance, abstract.Signal):
    """ `psygnal` implementation of the `base.Signal` abstract class.
    """

    def __init__(self, *argtypes: 'Any', info: str = "ImSwitch signal") -> None:
        SignalInstance.__init__(self, signature=argtypes)
        self._info = info

    def connect(self, func: 'Union[Callable, abstract.Signal]') -> None:
        if isinstance(func, abstract.Signal):
            if any([t1 != t2 for t1, t2 in zip(self.types, func.types)]):
                raise TypeError(f"Source and destination must have the same signature. Source signature: {self.types}, destination signature: {func.types}")
            func = func.emit
        super().connect(func)
    
    def disconnect(self, func: 'Union[Callable, abstract.Signal, None]' = None) -> None:
        if func is None:
            super().disconnect()
        super().disconnect(func)
    
    def emit(self, *args) -> None:
        super().emit(*args)
    
    @property
    @lru_cache
    def types(self) -> 'Tuple[type, ...]':
        return tuple([param.annotation for param in self._signature.parameters.values()])
    
    @property
    def info(self) -> str:
        return self._info

class SignalInterface(abstract.SignalInterface):
    """ Base implementation of `abstract.SignalInterface`.
    """
    def __init__(self) -> None:
        ...

class Worker(abstract.Worker):
    def __init__(self) -> None:
        self._thread = None

    def moveToThread(self, thread : abstract.Thread) -> None:
        self._thread = thread
        thread._worker = self

class Thread(abstract.Thread):
    
    _started = Signal()
    _finished = Signal()
    
    def __init__(self):
        self._thread = None
        self._loop = None
        self._running = threading.Event()
        self._worker : Worker = None

    def start(self):
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._run, daemon=True)
            if self._worker is not None:
                # reassign worker to the new thread in case
                # it was moved to another thread before
                self._worker._thread = self
            self._running.set()
            self._thread.start()

    def _run(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._started.emit()
        try:
            while self._running.is_set():
                self._loop.run_forever()
        finally:
            self._loop.run_until_complete(self._loop.shutdown_asyncgens())
            self._loop.close()
            self._loop = None
            self._finished.emit()

    def quit(self):
        self._running.clear()
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

    def wait(self):
        if self._thread and self._thread.is_alive():
            self._thread.join()
    
    @property
    def started(self) -> Signal:
        return self._started

    @property
    def finished(self) -> Signal:
        return self._finished

class Timer(abstract.Timer):
    
    _timeout = Signal()
    
    def __init__(self, singleShot=False):
        self._task = None
        self._singleShot = singleShot
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def start(self, millisecs):
        self._interval = millisecs / 1000.0
        if self._task:
            self._task.cancel()
        self._task = asyncio.run_coroutine_threadsafe(self._run(), self._loop)

    def stop(self):
        if self._task:
            self._task.cancel()
            self._task = None

    async def _run(self):
        await asyncio.sleep(self._interval)
        self.timeout.emit()
        if not self._singleShot:
            self._task = self._loop.create_task(self._run())
    
    @property
    def timeout(self) -> Signal:
        return self._timeout

def threadCount() -> int:
    """ Returns the current number of active threads of this framework.
    
    Returns:
        ``int``: number of active threads
    """
    return threading.active_count()

class FrameworkUtils(abstract.FrameworkUtils):
    @staticmethod
    def processPendingEventsCurrThread():
        emit_queued()