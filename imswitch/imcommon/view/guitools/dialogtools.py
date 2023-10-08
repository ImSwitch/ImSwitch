from json import dump
from typing import Union
from .BetterTableWidget import BetterTableWidget
from .BetterPushButton import BetterPushButton
from qtpy import QtCore, QtWidgets
from qtpy.QtWidgets import (
    QDialog,
    QGridLayout,
)
from imswitch.imcommon.model import dirtools
from os.path import join

def askYesNoQuestion(widget, title, question):
    """ Asks the user a yes/no question and returns whether "yes" was clicked. """
    result = QtWidgets.QMessageBox.question(widget, title, question,
                                            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
    return result == QtWidgets.QMessageBox.Yes


def askForTextInput(widget, title, label):
    """ Asks the user to enter a text string. Returns the string if "yes" is
    clicked, None otherwise. """
    result, okClicked = QtWidgets.QInputDialog.getText(
        widget, title, label, flags=QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowTitleHint
    )
    return result if okClicked else None


def askForFilePath(widget, caption=None, defaultFolder=None, nameFilter=None, isSaving=False):
    """ Asks the user to pick a file path. Returns the file path if "OK" is
    clicked, None otherwise. """
    func = (QtWidgets.QFileDialog().getOpenFileName if not isSaving
            else QtWidgets.QFileDialog().getSaveFileName)

    result = func(widget, caption=caption, directory=defaultFolder, filter=nameFilter)[0]
    return result if result else None


def askForFolderPath(widget, caption=None, defaultFolder=None):
    """ Asks the user to pick a folder path. Returns the folder path if "OK" is
    clicked, None otherwise. """
    result = QtWidgets.QFileDialog.getExistingDirectory(widget, caption=caption,
                                                        directory=defaultFolder)
    return result if result else None

class PositionsTableDialog(QDialog):
    
    sigTableDataDumped = QtCore.Signal(dict)
    
    def __init__(self, title: str, coordinates: list, default: Union[str, int, float],  unit: str = "µm", labelName: str = "Point"):
        super(QDialog, self).__init__()
        
        self.coordinates = coordinates
        
        # Create the dialog
        self.resize(600, 400)  # Set the size of the dialog.
        gridLayout = QGridLayout(self)  # Create a grid layout.
        
        # Create the table widget
        self.pointsTableWidget = BetterTableWidget(names=coordinates, default=default, unit=unit, labelName=labelName)
        
        numColumns = len(coordinates) + 1
        
        # Create the add row button
        self.addPosButton = BetterPushButton(self)
        self.addPosButton.setText("Add position")  # Set label of the button.
        self.addPosButton.clicked.connect(self.pointsTableWidget.addNewRow)  # Connect the button to a function.
        
        # Create the remove row button
        self.removePosButton = BetterPushButton(self)
        self.removePosButton.setText("Remove position")  # Set label of the button.
        self.removePosButton.clicked.connect(self.pointsTableWidget.removeSelectedRow)  # Connect the button to a function.
        
        # The remove row button is active only when a row is selected
        self.removePosButton.setEnabled(False)
        self.pointsTableWidget.selectionModel().selectionChanged.connect(
            self.setRemoveButtonStatus
        )
        
        # Create the save table button
        self.saveTableButton = BetterPushButton(self)
        self.saveTableButton.setText("Save table")  # Set label of the button.
        self.saveTableButton.clicked.connect(self.saveTable)
        
        # Create OK and Cancel buttons
        self.okButton = BetterPushButton(self)
        self.okButton.setText("OK")
        self.okButton.clicked.connect(self.accept)
        self.cancelbutton = BetterPushButton(self)
        self.cancelbutton.setText("Cancel")
        self.cancelbutton.clicked.connect(self.reject)
        
        
        gridLayout.addWidget(self.pointsTableWidget, 0, 0, 6, numColumns)
        gridLayout.addWidget(self.addPosButton, 0, numColumns)
        gridLayout.addWidget(self.removePosButton, 1, numColumns)
        gridLayout.addWidget(self.saveTableButton, 2, numColumns)
        gridLayout.addWidget(self.okButton, 4, numColumns)
        gridLayout.addWidget(self.cancelbutton, 5, numColumns)
        self.setLayout(gridLayout)
        self.setWindowTitle(title)
    
    def __del__(self):
        receiversCount = self.receivers(self.sigTableDataDumped)
        if receiversCount > 0:
            self.sigTableDataDumped.disconnect()
    
    def accept(self) -> None:
        data = {}
        keys = self.coordinates
        if self.pointsTableWidget.labelName is not None:
            keys.append("Label")
        for row in range(self.pointsTableWidget.rowCount()):
            rowData = self._parseRowElements(row)
            data[row] = {key: value for key, value in zip(keys, rowData)}
        self.sigTableDataDumped.emit(data)
        super().accept()
    
    def setRemoveButtonStatus(self, _):
        selectedItems = len(self.pointsTableWidget.selectedItems())
        self.removePosButton.setEnabled(selectedItems != 0)

    def saveTable(self):
        """ Saves the table as a CSV or JSON file. A file explorer window will open,
        and the user will be asked to pick a file path.
        """
        fileFilter = "JSON (*.json);;CSV (*.csv)"
        filePath: str = askForFilePath(self, 
                                       caption="Save table", 
                                       defaultFolder=join(dirtools.UserFileDirs.Root, "table_data"), 
                                       isSaving=True, 
                                       nameFilter=fileFilter)
        if filePath is not None:
            if filePath.endswith(".csv"):
                self._saveTableAsCSV(filePath)
            elif filePath.endswith(".json"):
                self._saveTableAsJSON(filePath)
    
    def _saveTableAsCSV(self, filePath: str):
        with open(filePath, "w") as f:
            # Write the data
            header = self.coordinates
            if self.pointsTableWidget.labelName is not None:
                header.append("Label")
            f.write(",".join(header) + "\n")
            for row in range(self.pointsTableWidget.rowCount()):
                rowData = self._parseRowElements(row)
                rowData = [str(item) for item in rowData]
                f.write(",".join(rowData) + "\n")
    
    def _saveTableAsJSON(self, filePath: str):
        data = {}
        keys = self.coordinates
        if self.pointsTableWidget.labelName is not None:
            keys.append("Label")
        for row in range(self.pointsTableWidget.rowCount()):
            rowData = self._parseRowElements(row)
            data[row] = {key: value for key, value in zip(keys, rowData)}
        
        with open(filePath, "w") as f:
            dump(data, f, indent=4)

    def _parseRowElements(self, row: int):
        """ Parses the elements of a row and returns them as a list.
        """
        table = self.pointsTableWidget
        rowData = []
        if type(table.default) in [int, float]:
            if table.labelName is not None:
                rowData = [table.cellWidget(row, col).value() for col in range(table.columnCount()-1)]
                rowData.append(table.item(row, table.columnCount()-1).text())
            else:
                rowData = [table.itemAt(row, col).text() for col in range(table.columnCount())]
        return rowData


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
