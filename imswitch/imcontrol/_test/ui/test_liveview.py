import pytest
from PyQt5 import QtCore, QtTest
from . import prepareUI


app, mainView = prepareUI()


@pytest.fixture(scope='session')
def qapp():
    yield app


def test_liveview_no_error(qtbot):
    qtbot.mouseClick(mainView.widgets['View'].liveviewButton, QtCore.Qt.LeftButton)
    assert mainView.widgets['View'].liveviewButton.isChecked()

    QtTest.QTest.qWait(3000)
    qtbot.mouseClick(mainView.widgets['View'].liveviewButton, QtCore.Qt.LeftButton)
    assert not mainView.widgets['View'].liveviewButton.isChecked()


def test_grid_no_error(qtbot):
    qtbot.mouseClick(mainView.widgets['View'].gridButton, QtCore.Qt.LeftButton)
    assert mainView.widgets['View'].gridButton.isChecked()

    QtTest.QTest.qWait(100)
    qtbot.mouseClick(mainView.widgets['View'].gridButton, QtCore.Qt.LeftButton)
    assert not mainView.widgets['View'].gridButton.isChecked()


def test_crosshair_no_error(qtbot):
    qtbot.mouseClick(mainView.widgets['View'].crosshairButton, QtCore.Qt.LeftButton)
    assert mainView.widgets['View'].crosshairButton.isChecked()

    QtTest.QTest.qWait(100)
    qtbot.mouseMove(mainView.widgets['Image'], pos=QtCore.QPoint(120, 120))
    QtTest.QTest.qWait(100)
    qtbot.mouseMove(mainView.widgets['Image'], pos=QtCore.QPoint(150, 160))
    QtTest.QTest.qWait(100)
    qtbot.mouseMove(mainView.widgets['Image'], pos=QtCore.QPoint(400, 400))
    qtbot.mouseClick(mainView.widgets['Image'], QtCore.Qt.LeftButton, pos=QtCore.QPoint(400, 400))
    QtTest.QTest.qWait(100)
    qtbot.mouseMove(mainView.widgets['Image'], pos=QtCore.QPoint(400, 300))
    qtbot.mouseClick(mainView.widgets['Image'], QtCore.Qt.LeftButton, pos=QtCore.QPoint(400, 300))
    QtTest.QTest.qWait(100)
    qtbot.mouseMove(mainView.widgets['Image'], pos=QtCore.QPoint(400, 200))

    QtTest.QTest.qWait(100)
    qtbot.mouseClick(mainView.widgets['View'].crosshairButton, QtCore.Qt.LeftButton)
    assert not mainView.widgets['View'].crosshairButton.isChecked()


def test_close_no_error(qtbot):
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
