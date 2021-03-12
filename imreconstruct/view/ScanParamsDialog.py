from pyqtgraph.Qt import QtCore, QtWidgets

from .guitools import BetterPushButton


class ScanParamsDialog(QtWidgets.QDialog):
    """Seperate window for editing scanning parameters"""

    # Signals
    sigApplyParams = QtCore.Signal()

    # Methods
    def __init__(self, parent, r_l_text, u_d_text, b_f_text,
                 timepoints_text, p_text, n_text, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.r_l_text = r_l_text
        self.u_d_text = u_d_text
        self.b_f_text = b_f_text
        self.p_text = p_text
        self.timepoints_text = timepoints_text
        self.n_text = n_text

        imDimLabel = QtWidgets.QLabel('Image dimension')
        dimDirLabel = QtWidgets.QLabel('Direction')
        imStepsLabel = QtWidgets.QLabel('Steps')
        imStepSizeLabel = QtWidgets.QLabel('Step size (nm)')

        dim0Label = QtWidgets.QLabel('Dimension 0')
        self.dim0DimEdit = QtWidgets.QComboBox()
        self.dim0DimEdit.addItems([self.r_l_text, self.u_d_text, self.b_f_text])
        self.dim0DimEdit.currentIndexChanged.connect(self.dim0Changed)
        self.dim0DirEdit = QtWidgets.QComboBox()
        self.dim0DirEdit.addItems([self.p_text, self.n_text])
        self.dim0SizeEdit = QtWidgets.QLineEdit()
        self.dim0SizeEdit.returnPressed.connect(lambda: self.checkForInt(self.dim0SizeEdit))
        self.dim0StepSizeEdit = QtWidgets.QLineEdit()

        dim1Label = QtWidgets.QLabel('Dimension 1')
        self.dim1DimEdit = QtWidgets.QComboBox()
        self.dim1DimEdit.currentIndexChanged.connect(self.dim1Changed)
        self.dim1DirEdit = QtWidgets.QComboBox()
        self.dim1DirEdit.addItems([self.p_text, self.n_text])
        self.dim1SizeEdit = QtWidgets.QLineEdit()
        self.dim1SizeEdit.returnPressed.connect(lambda: self.checkForInt(self.dim1SizeEdit))
        self.dim1StepSizeEdit = QtWidgets.QLineEdit()

        dim2Label = QtWidgets.QLabel('Dimension 2')
        self.dim2DimEdit = QtWidgets.QComboBox()
        self.dim2DirEdit = QtWidgets.QComboBox()
        self.dim2DirEdit.addItems([self.p_text, self.n_text])
        self.dim2SizeEdit = QtWidgets.QLineEdit()
        self.dim2SizeEdit.returnPressed.connect(lambda: self.checkForInt(self.dim2SizeEdit))
        self.dim2StepSizeEdit = QtWidgets.QLineEdit()

        dim3Label = QtWidgets.QLabel('Dimension 3')
        self.dim3DimLabel = QtWidgets.QLabel(self.timepoints_text)
        self.dim3SizeEdit = QtWidgets.QLineEdit()
        self.dim3SizeEdit.returnPressed.connect(lambda: self.checkForInt(self.dim3SizeEdit))
        self.dim3StepSizeEdit = QtWidgets.QLineEdit()

        self.unidirCheck = QtWidgets.QCheckBox('Unidirectional scan')

        okBtn = BetterPushButton('OK')
        okBtn.clicked.connect(self.okClicked)

        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        layout.addWidget(imDimLabel, 0, 1)
        layout.addWidget(dimDirLabel, 0, 2)
        layout.addWidget(imStepsLabel, 0, 3)
        layout.addWidget(imStepSizeLabel, 0, 4)
        layout.addWidget(dim0Label, 1, 0)
        layout.addWidget(self.dim0DimEdit, 1, 1)
        layout.addWidget(self.dim0DirEdit, 1, 2)
        layout.addWidget(self.dim0SizeEdit, 1, 3)
        layout.addWidget(self.dim0StepSizeEdit, 1, 4)
        layout.addWidget(dim1Label, 2, 0)
        layout.addWidget(self.dim1DimEdit, 2, 1)
        layout.addWidget(self.dim1DirEdit, 2, 2)
        layout.addWidget(self.dim1SizeEdit, 2, 3)
        layout.addWidget(self.dim1StepSizeEdit, 2, 4)
        layout.addWidget(dim2Label, 3, 0)
        layout.addWidget(self.dim2DimEdit, 3, 1)
        layout.addWidget(self.dim2DirEdit, 3, 2)
        layout.addWidget(self.dim2SizeEdit, 3, 3)
        layout.addWidget(self.dim2StepSizeEdit, 3, 4)
        layout.addWidget(dim3Label, 4, 0)
        layout.addWidget(self.dim3DimLabel, 4, 1)
        layout.addWidget(self.dim3SizeEdit, 4, 3)
        layout.addWidget(self.dim3StepSizeEdit, 4, 4)
        layout.addWidget(self.unidirCheck, 5, 1)
        layout.addWidget(okBtn, 5, 2)

    def updateValues(self, parDict):
        try:
            self.dim0DimEdit.setCurrentIndex(self.dim0DimEdit.findText(parDict['dimensions'][0]))
            self.dim1DimEdit.setCurrentIndex(self.dim1DimEdit.findText(parDict['dimensions'][1]))
            self.dim2DimEdit.setCurrentIndex(self.dim2DimEdit.findText(parDict['dimensions'][2]))
            self.dim0Changed()

            self.dim0DirEdit.setCurrentIndex(self.dim0DirEdit.findText(parDict['directions'][0]))
            self.dim1DirEdit.setCurrentIndex(self.dim1DirEdit.findText(parDict['directions'][1]))
            self.dim2DirEdit.setCurrentIndex(self.dim2DirEdit.findText(parDict['directions'][2]))

            self.dim0SizeEdit.setText(parDict['steps'][0])
            self.dim1SizeEdit.setText(parDict['steps'][1])
            self.dim2SizeEdit.setText(parDict['steps'][2])
            self.dim3SizeEdit.setText(parDict['steps'][3])

            self.dim0StepSizeEdit.setText(parDict['step_sizes'][0])
            self.dim1StepSizeEdit.setText(parDict['step_sizes'][1])
            self.dim2StepSizeEdit.setText(parDict['step_sizes'][2])
            self.dim3StepSizeEdit.setText(parDict['step_sizes'][3])

            self.unidirCheck.setChecked(parDict['unidirectional'])
        except:
            print('Error setting initial values')
            self.dim0Changed()

    def checkForInt(self, parameter):
        try:
            int(parameter.text())
        except ValueError:
            parameter.setText('1')
            print('Cannot interpret given value as integer')

    def dim0Changed(self):
        currText = self.dim0DimEdit.currentText()
        self.dim1DimEdit.clear()
        if currText == self.r_l_text:
            self.dim1DimEdit.addItems([self.u_d_text, self.b_f_text])
        elif currText == self.u_d_text:
            self.dim1DimEdit.addItems([self.r_l_text, self.b_f_text])
        else:
            self.dim1DimEdit.addItems([self.r_l_text, self.u_d_text])

        self.dim1Changed()

    def dim1Changed(self):
        currdim0Text = self.dim0DimEdit.currentText()
        currdim1Text = self.dim1DimEdit.currentText()
        self.dim2DimEdit.clear()
        if currdim0Text == self.r_l_text:
            if currdim1Text == self.u_d_text:
                self.dim2DimEdit.addItem(self.b_f_text)
            else:
                self.dim2DimEdit.addItem(self.u_d_text)
        elif currdim0Text == self.u_d_text:
            if currdim1Text == self.r_l_text:
                self.dim2DimEdit.addItem(self.b_f_text)
            else:
                self.dim2DimEdit.addItem(self.r_l_text)
        else:
            if currdim1Text == self.r_l_text:
                self.dim2DimEdit.addItem(self.u_d_text)
            else:
                self.dim2DimEdit.addItem(self.r_l_text)

    def getDimensions(self):
        return [self.dim0DimEdit.currentText(),
                self.dim1DimEdit.currentText(),
                self.dim2DimEdit.currentText(),
                self.dim3DimLabel.text()]

    def getDirections(self):
        return [self.dim0DirEdit.currentText(),
                self.dim1DirEdit.currentText(),
                self.dim2DirEdit.currentText(),
                self.p_text]

    def getSteps(self):
        return [self.dim0SizeEdit.text(),
                self.dim1SizeEdit.text(),
                self.dim2SizeEdit.text(),
                self.dim3SizeEdit.text()]

    def getStepSizes(self):
        return [self.dim0StepSizeEdit.text(),
                self.dim1StepSizeEdit.text(),
                self.dim2StepSizeEdit.text(),
                self.dim3StepSizeEdit.text()]

    def getUnidirectional(self):
        return self.unidirCheck.isChecked()

    def okClicked(self):
        self.sigApplyParams.emit()
        self.close()


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
