from imswitch.imcommon.model import initLogger

from pyqtgraph.Qt import QtGui, QtCore
from qtpy import QtCore, QtWidgets

from imswitch.imcontrol.view import guitools
from .basewidgets import Widget


class BFTimelapseWidget(Widget):
    """ Widget for controlling the BF timelapse implementation. """

    def __init__(self, *args, **kwargs):
        self.__logger = initLogger(self, instanceName='BFTimelapseWidget')
        super().__init__(*args, **kwargs)

        # add all forAcquisition detectors in a dropdown list, for being the detector (widefield) to save from
        self.detectors = list()
        self.detectorsPar = QtWidgets.QComboBox()
        self.detectorsPar_label = QtWidgets.QLabel('Detector')
        self.detectorsPar_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom)

        self.initiateButton = guitools.BetterPushButton('Start')
        self.initiateButton.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)

        self.interval_label = QtWidgets.QLabel('Interval (s)')
        self.interval_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom)
        self.interval_edit = QtWidgets.QLineEdit(str(5))

        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)

        # initialize widget controls
        currentRow = 0

        self.grid.addWidget(self.initiateButton, currentRow, 0, 2, 1)
        self.grid.addWidget(self.interval_label, currentRow, 1)
        self.grid.addWidget(self.interval_edit, currentRow, 2)

        #currentRow += 1

        #self.grid.addWidget(self.detectorsPar_label, currentRow, 1)
        #self.grid.addWidget(self.detectorsPar, currentRow, 2)


    def setDetectorList(self, detectorNames):
        """ Set combobox with available detectors to use. """
        for detectorName, _ in detectorNames.items():
            self.detectors.append(detectorName)
        self.detectorsPar.addItems(self.detectors)
        self.detectorsPar.setCurrentIndex(0)

