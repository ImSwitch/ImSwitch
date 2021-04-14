import os
import sys

from pyqtgraph.Qt import QtCore, QtWidgets

from .view.guitools import getBaseStyleSheet


def prepareApp():
    """ This function must be called before any views are created. """
    os.environ['PYQTGRAPH_QT_LIB'] = 'PyQt5'  # force Qt to use PyQt5
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)  # Fixes Napari issues
    app = QtWidgets.QApplication([])
    app.setStyleSheet(getBaseStyleSheet())
    return app


def launchApp(app, mainView, moduleMainControllers):
    """ Launches the app. The program will exit when the app is exited. """

    # Show app
    mainView.show()
    exitCode = app.exec_()

    # Clean up
    for controller in moduleMainControllers:
        controller.closeEvent()
    sys.exit(exitCode)


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
