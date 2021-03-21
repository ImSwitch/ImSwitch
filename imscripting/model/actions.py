import threading

from imcommon.model import APIExport, generateAPI
#from imcommon.framework import Timer


class _Actions:
    @staticmethod
    @APIExport
    def runInQueue(*funcsOrDelays):
        funcsOrDelays = list(funcsOrDelays)
        funcsToBeExecuted = []
        delay = None

        while funcsOrDelays:
            funcOrDelay = funcsOrDelays.pop(0)
            if callable(funcOrDelay):
                funcsToBeExecuted.append(funcOrDelay)
            else:
                delay = funcOrDelay
                break

        for func in funcsToBeExecuted:
            func()

        if delay is not None:
            timer = threading.Timer(delay / 1000, lambda: _Actions.runInQueue(*funcsOrDelays))
            timer.start()
            #timer = Timer(singleShot=True)
            #timer.timeout.connect(lambda: _Actions.runInQueue(*funcsOrDelays))
            #timer.start(delay)


def getActionsScope():
    return generateAPI([_Actions()]).toDict()


# Copyright (C) 2020, 2021 TestaLab
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
