from pyqtgraph.Qt import QtGui


def askYesNoQuestion(widget, title, question):
    """ Asks the user a yes/no question and returns whether "yes" was clicked. """
    result = QtGui.QMessageBox.question(widget, title, question,
                                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
    return result == QtGui.QMessageBox.Yes


def askForTextInput(widget, title, label):
    """ Asks the user to enter a text string. Returns the string if "yes" is
    clicked, None otherwise. """
    result, okClicked = QtGui.QInputDialog.getText(widget, title, label)
    return result if okClicked else None

# Copyright (C) 2020, 2021 Staffan Al-Kadhimi, Xavier Casas, Andreas Boden
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