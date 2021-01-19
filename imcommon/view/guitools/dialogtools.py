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
