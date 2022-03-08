import atexit
from abc import ABC, abstractmethod
from multiprocessing.shared_memory import SharedMemory
from typing import Deque, Generic, TypeVar

import numpy as np
import Pyro5
import Pyro5.api
import useq

Pyro5.config.SERIALIZER = "msgpack"
T = TypeVar("T")


class Serializer(ABC, Generic[T]):
    # define these in subclasses

    @abstractmethod
    def to_dict(self, obj: T) -> dict:
        ...

    @abstractmethod
    def from_dict(self, classname: str, dct: dict) -> T:
        ...

    # -----------------

    @classmethod
    def type_(cls):
        return cls.__orig_bases__[0].__args__[0]

    def _to_dict(self, obj: T) -> dict:
        return {**self.to_dict(obj), "__class__": self.type_key()}

    def _from_dict(self, classname: str, d: dict) -> T:
        d.pop("__class__", None)
        return self.from_dict(classname, d)

    @classmethod
    def register(cls):
        ser = cls()
        Pyro5.api.register_class_to_dict(cls.type_(), ser._to_dict)
        Pyro5.api.register_dict_to_class(cls.type_key(), ser._from_dict)

    @classmethod
    def type_key(cls):
        return f"{cls.type_().__module__}.{cls.type_().__name__}"


class SerMDASequence(Serializer[useq.MDASequence]):
    def to_dict(self, obj: useq.MDASequence):
        return obj.dict()

    def from_dict(self, classname: str, d: dict):
        return useq.MDASequence.parse_obj(d)


class SerMDAEvent(Serializer[useq.MDAEvent]):
    def to_dict(self, obj: useq.MDAEvent):
        return obj.dict()

    def from_dict(self, classname: str, d: dict):
        return useq.MDAEvent.parse_obj(d)



class SerNDArray(Serializer[np.ndarray]):
    SHM_SENT: Deque[SharedMemory] = Deque(maxlen=15)

    def to_dict(self, obj: np.ndarray):
        shm = SharedMemory(create=True, size=obj.nbytes)
        SerNDArray.SHM_SENT.append(shm)
        b: np.ndarray = np.ndarray(obj.shape, dtype=obj.dtype, buffer=shm.buf)
        b[:] = obj[:]
        return {
            "shm": shm.name,
            "shape": obj.shape,
            "dtype": str(obj.dtype),
        }

    def from_dict(self, classname: str, d: dict):
        """convert dict from `ndarray_to_dict` back to np.ndarray"""
        shm = SharedMemory(name=d["shm"], create=False)
        array = np.ndarray(d["shape"], dtype=d["dtype"], buffer=shm.buf).copy()
        shm.close()
        shm.unlink()
        return array


@atexit.register  # pragma: no cover
def _cleanup():
    for shm in SerNDArray.SHM_SENT:
        shm.close()
        try:
            shm.unlink()
        except FileNotFoundError:
            pass


def remove_shm_from_resource_tracker():
    """Monkey-patch multiprocessing.resource_tracker so SharedMemory won't be tracked
    More details at: https://bugs.python.org/issue38119
    """
    from multiprocessing import resource_tracker

    def fix_register(name, rtype):  # pragma: no cover
        if rtype == "shared_memory":
            return
        return resource_tracker._resource_tracker.register(name, rtype)

    resource_tracker.register = fix_register

    def fix_unregister(name, rtype):  # pragma: no cover
        if rtype == "shared_memory":
            return
        return resource_tracker._resource_tracker.unregister(name, rtype)

    resource_tracker.unregister = fix_unregister

    if "shared_memory" in resource_tracker._CLEANUP_FUNCS:
        del resource_tracker._CLEANUP_FUNCS["shared_memory"]


def register_serializers():
    remove_shm_from_resource_tracker()
    for i in globals().values():
        if isinstance(i, type) and issubclass(i, Serializer) and i != Serializer:
            i.register()


# BSD 3-Clause License
#
# Copyright (c) 2021, Talley Lambert
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.