from qtpy import QtCore, QtWidgets


def askYesNoQuestion(widget, title, question):
    """ Asks the user a yes/no question and returns whether "yes" was clicked. """
    result = QtWidgets.QMessageBox.question(widget, title, question,
                                            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
    return result == QtWidgets.QMessageBox.Yes


def askForTextInput(widget, title, label, suggested=None):
    """ Asks the user to enter a text string. Returns the string if "yes" is
    clicked, None otherwise. """
    result, okClicked = QtWidgets.QInputDialog.getText(
        widget, title, label, flags=QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowTitleHint, 
        text=suggested
    )
    return result if okClicked else None


def askForFilePath(widget, caption=None, defaultFolder=None, nameFilter=None, isSaving=False,multiFiles=False):
    """ Asks the user to pick a file path. Returns the file path if "OK" is
    clicked, None otherwise. """
    func = (QtWidgets.QFileDialog().getOpenFileName if not isSaving and not multiFiles
            else QtWidgets.QFileDialog().getOpenFileNames if not isSaving
            else QtWidgets.QFileDialog().getSaveFileName)

    result = func(widget, caption=caption, directory=defaultFolder, filter=nameFilter)[0]
    return result if result else None


def askForFolderPath(widget, caption=None, defaultFolder=None):
    """ Asks the user to pick a folder path. Returns the folder path if "OK" is
    clicked, None otherwise. """
    result = QtWidgets.QFileDialog.getExistingDirectory(widget, caption=caption,
                                                        directory=defaultFolder)
    return result if result else None


def askForTwoTextInputs(title, label1, label2, default1="", default2="", multiline2=True, readonly1=False):
    """
    Asks the user for two text inputs.
    Args:
        title (str): Dialog title.
        label1 (str): Label for first input.
        label2 (str): Label for second input.
        default1 (str): Default text for first input.
        default2 (str): Default text for second input.
        multiline2 (bool): If True, second input is QTextEdit; else QLineEdit.
        readonly1 (bool): If True, first input is read-only (cannot be edited).

    Returns:
        (val1, val2) if OK clicked and val1 is not empty (or readonly)
        (None, None) if Cancel clicked
    Notes:
    - Parent is None to ensure the dialog always appears in front.
    """
    dialog = QtWidgets.QDialog(None)
    dialog.setWindowTitle(title)
    dialog.setWindowFlags(QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowTitleHint)
    dialog.setWindowModality(QtCore.Qt.ApplicationModal)

    layout = QtWidgets.QVBoxLayout(dialog)

    edit1 = QtWidgets.QLineEdit()
    edit1.setText(default1)
    edit1.setReadOnly(readonly1)
    layout.addWidget(QtWidgets.QLabel(label1))
    layout.addWidget(edit1)

    layout.addWidget(QtWidgets.QLabel(label2))
    if multiline2:
        edit2 = QtWidgets.QTextEdit()
        edit2.setPlainText(default2)
        edit2.setFixedHeight(80)
    else:
        edit2 = QtWidgets.QLineEdit()
        edit2.setText(default2)
    layout.addWidget(edit2)

    buttons = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    layout.addWidget(buttons)

    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)

    if readonly1:
        edit2.setFocus()
    else:
        edit1.setFocus()

    if dialog.exec() != QtWidgets.QDialog.Accepted:
        return None, None

    val1 = edit1.text().strip()
    val2 = edit2.toPlainText().strip() if multiline2 else edit2.text().strip()

    if not val1:
        return None, None

    return val1, val2





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
