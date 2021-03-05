import os
import sys

from pyqtgraph.Qt import QtWidgets

from .view.guitools import getBaseStyleSheet


def prepareApp():
    """ This function must be called before any views are created. """
    os.environ['PYQTGRAPH_QT_LIB'] = 'PyQt5'  # force Qt to use PyQt5
    app = QtWidgets.QApplication([])
    app.setStyleSheet(getBaseStyleSheet())
    return app


def launchApp(app, mainView, mainControllers):
    """ Launches the app. The program will exit when the app is exited. """

    # Show app
    mainView.show()
    exitCode = app.exec_()

    # Clean up
    for controller in mainControllers:
        controller.closeEvent()
    sys.exit(exitCode)
