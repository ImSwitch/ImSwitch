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
