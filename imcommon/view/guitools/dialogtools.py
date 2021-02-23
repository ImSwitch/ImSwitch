from pyqtgraph.Qt import QtWidgets


def askYesNoQuestion(widget, title, question):
    """ Asks the user a yes/no question and returns whether "yes" was clicked. """
    result = QtWidgets.QMessageBox.question(widget, title, question,
                                            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
    return result == QtWidgets.QMessageBox.Yes


def askForTextInput(widget, title, label):
    """ Asks the user to enter a text string. Returns the string if "yes" is
    clicked, None otherwise. """
    result, okClicked = QtWidgets.QInputDialog.getText(widget, title, label)
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
