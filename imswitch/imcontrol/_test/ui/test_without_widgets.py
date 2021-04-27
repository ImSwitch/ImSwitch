import pytest
from PyQt5 import QtTest

from .. import optionsBasic, setupInfoWithoutWidgets
from . import getApp, prepareUI


mainView = None


@pytest.fixture(scope='module')
def qapp():
    global mainView
    app = getApp()
    mainView = prepareUI(optionsBasic, setupInfoWithoutWidgets)
    yield app


def test_without_widgets_starts_no_error(qtbot):
    QtTest.QTest.qWait(1000)


def test_without_widgets_close_no_error(qtbot):
    mainView.close()


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
