from qtpy import QtCore, QtWidgets

from imswitch.imcommon.view.guitools import colorutils
from imswitch.imcontrol.view import guitools
from .basewidgets import Widget


class ShutterWidget(Widget):
    """ Shutter widget for setting shutter state. """

    sigStateChanged = QtCore.Signal(str, bool)  # (shutterame, Shutterstate)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shutterModules = {}

        self.setMinimumHeight(50)

        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)

        # Shutters grid
        self.shuttersGrid = QtWidgets.QGridLayout()
        self.shuttersGrid.setContentsMargins(4, 4, 4, 4)

        self.shuttersGridContainer = QtWidgets.QWidget()
        self.shuttersGridContainer.setLayout(self.shuttersGrid)

        self.layout.addWidget(self.shuttersGridContainer)

    def addShutter(self, shutterName):
        """ Adds a shutter module widget."""

        control = ShutterModule()
        control.sigStateChanged.connect(
            lambda state: self.sigStateChanged.emit(shutterName, state)
        )

        nameLabel = QtWidgets.QLabel(shutterName)
        nameLabel.setStyleSheet(
            f'font-size: 16px; font-weight: bold; padding: 0 6px 0 12px;'
        )

        self.shuttersGrid.addWidget(control, len(self.shutterModules), 1)
        self.shutterModules[shutterName] = control

    def isShutterActive(self, shutterName):
        """ Returns whether the specified shutter is on. """
        return self.shutterModules[shutterName].isActive()

    def setEditable(self, editable):
        """ Sets whether the widget can be interacted with. """
        self.setEnabled(editable)

    def setShutterActive(self, shutterName, active):
        """ Sets whether the specified shutter is open. """
        if shutterName in self.shutterModules:
            # Mettre à jour l'état du bouton pour refléter le changement de l'état du shutter
            self.shutterModules[shutterName].setActive(active)
        
    def setShutterActivatable(self, shutterName, activatable):
        """ Sets whether the specified shuer can be opened/closed by the user."""
        if shutterName in self.shutterModules:
            self.shutterModules[shutterName].setActivatable(activatable)

    def setShutterEditable(self, shutterName, editable):
        """ Sets whether the specified laser's values can be edited by the
        user. """
        self.shutterModules[shutterName].setEditable(editable)


class ShutterModule(QtWidgets.QWidget):
    """ Module from ShutterWidget to handle a single shutter. """

    sigStateChanged = QtCore.Signal(bool)  # (state)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # On/Off Button              
        self.shutterButton = QtWidgets.QPushButton('ON')
        self.shutterButton.setSizePolicy(QtWidgets.QSizePolicy.Minimum,
                                        QtWidgets.QSizePolicy.Expanding)
        self.shutterButton.setCheckable(True)

        # Add elements to QHBoxLayout
        self.layout = QtWidgets.QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.layout.addWidget(self.shutterButton)

        # Connect signals
        self.shutterButton.toggled.connect(self.onToggle)

    def onToggle(self, state):
        """ Handles button toggle event. """
        self.sigStateChanged.emit(state)
        self.updateButtonStyle(state)

    def updateButtonStyle(self, state):
        """ Changes the button color to red only when activated. """
        if state:
            # Applique une couleur rouge lorsque le bouton est activé
            self.shutterButton.setStyleSheet("background-color: red; color: white; font-weight: bold; border-radius: 10px;")
            self.shutterButton.setText('ON')
        else:
            # Réinitialise le style pour utiliser le style natif d'IMswitch
            self.shutterButton.setStyleSheet("")
            self.shutterButton.setText('OFF')

    def isActive(self):
        """ Returns whether the widget is powered on. """
        return self.shutterButton.isChecked()

    def setActive(self, active):
        """ Sets whether the widget is powered on. """
        self.shutterButton.setChecked(active)
        self.updateButtonStyle(active)

    def setActivatable(self, activatable):
        """ Sets whether the widget can be (de)activated by the user. """
        self.shutterButton.setEnabled(activatable)
        self.updateButtonStyle(self.isActive())
        
    def setEditable(self, editable):
        """ Sets whether the shutter's values can be edited by the user. """
        self.shutterButton.setEnabled(editable)
        self.updateButtonStyle(self.isActive())