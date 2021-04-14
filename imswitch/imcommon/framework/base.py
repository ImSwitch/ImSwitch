from abc import ABC, abstractmethod
from typing import Callable


class Mutex(ABC):
    @abstractmethod
    def __init__(self) -> None:
        pass

    @abstractmethod
    def lock(self) -> None:
        pass

    @abstractmethod
    def unlock(self) -> None:
        pass


class Signal(ABC):
    @abstractmethod
    def __init__(self, *argTypes) -> None:
        pass

    @abstractmethod
    def connect(self, func: Callable) -> None:
        pass

    @abstractmethod
    def disconnect(self, func: Callable) -> None:
        pass

    @abstractmethod
    def emit(self, *args) -> None:
        pass


class SignalInterface(ABC):
    @abstractmethod
    def __init__(self) -> None:
        pass


class Thread(SignalInterface, ABC):
    @abstractmethod
    def __init__(self) -> None:
        super().__init__()

    @property
    @abstractmethod
    def started(self) -> Signal:
        pass

    @property
    @abstractmethod
    def finished(self) -> Signal:
        pass

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def quit(self) -> None:
        pass

    @abstractmethod
    def wait(self) -> None:
        pass


class Timer(SignalInterface, ABC):
    @abstractmethod
    def __init__(self, singleShot: bool = False) -> None:
        pass

    @property
    @abstractmethod
    def timeout(self) -> Signal:
        pass

    @abstractmethod
    def start(self, periodMilliseconds: int) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass


class Worker(SignalInterface, ABC):
    @abstractmethod
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def moveToThread(self, thread: Thread) -> None:
        pass


class FrameworkUtils(ABC):
    @staticmethod
    @abstractmethod
    def processPendingEventsCurrThread() -> None:
        pass
