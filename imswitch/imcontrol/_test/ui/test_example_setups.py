import pytest
from qtpy import QtTest

from imswitch.imcommon.model.dirtools import DataFileDirs
from imswitch.imcontrol.view import ViewSetupInfo
from . import getApp, prepareUI
from .. import optionsBasic


mainView = None


setups = {}
exampleSetupsDir = DataFileDirs.Configs / 'imcontrol_setups'
for fileName in exampleSetupsDir.iterdir():
    if not fileName.suffix == '.json':
        continue

    filePath = exampleSetupsDir / fileName
    with open(filePath) as file:
        setups[fileName] = ViewSetupInfo.from_json(file.read())


@pytest.fixture(scope='module', params=list(setups.keys()))
def qapp(request):
    global mainView
    app = getApp()
    setupName = request.param
    mainView = prepareUI(optionsBasic, setups[setupName])
    yield app


def test_setup_starts_no_error(qtbot):
    QtTest.QTest.qWait(1000)


def test_setup_close_no_error(qtbot):
    mainView.close()


# Copyright (C) 2020-2021 ImSwitch developers
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
