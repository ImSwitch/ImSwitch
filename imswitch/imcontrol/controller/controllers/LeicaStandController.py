from qtpy import QtCore, QtGui, QtWidgets
from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.controller.basecontrollers import ImConWidgetController


class LeicaStandController(ImConWidgetController):
    """Click-driven controller for LeicaStandWidget."""

    FLUO_SHUTTER_DELAY_MS = 800

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self, tryInheritParent=True)

        self._manager = None
        self._last_selected_fluo_cube_name = None
        self._current_mode = "FLUO"

        stand_manager = getattr(self._master, "standManager", None)

        if stand_manager is None:
            self._widget.setConnected(False)
            return

        if getattr(stand_manager, "mocker", False):
            self._widget.setConnected(False)
            return

        self._manager = getattr(stand_manager, "_subManager", None)

        if self._manager is None:
            self._widget.setConnected(False)
            return

        self._cube_slot_to_name = self._manager.getAvailableCubes()
        self._cube_name_to_slot = {
            name: slot for slot, name in self._cube_slot_to_name.items()
        }

        self._connect_widget_signals()
        self._init_widget()
        self._init_shortcuts()

    def _init_shortcuts(self):
        self._toggleModeShortcut = QtWidgets.QShortcut(
            QtGui.QKeySequence("F2"),
            self._widget
        )
        self._toggleModeShortcut.activated.connect(self.toggleMode)

    def toggleMode(self):
        if self._manager is None or not self._manager.isConnected():
            self._widget.setConnected(False)
            return

        if self._current_mode == "FLUO":
            self.setCSMode()
        else:
            self.setFluoMode()

    def _connect_widget_signals(self):
        self._widget.sigModeChanged.connect(self.setMode)
        self._widget.sigCubeChanged.connect(self.setCubeByName)
        self._widget.sigPortSideChanged.connect(self.setPortSideByName)

    def _init_widget(self):
        fluo_cubes = [
            name
            for slot, name in sorted(self._cube_slot_to_name.items())
            if name != "EMP_BF"
        ]

        self._widget.setCubeChoices(fluo_cubes)

        if fluo_cubes:
            self._last_selected_fluo_cube_name = fluo_cubes[0]
            self._widget.setCurrentCube(self._last_selected_fluo_cube_name)

        self._widget.setCurrentPortSide("Left")
        self._widget.setMode(self._current_mode)
        self._widget.setConnected(self._manager.isConnected())

    def _safe_call(self, func, *args):
        try:
            result = func(*args)
            self._widget.setConnected(self._manager.isConnected())
            return result
        except Exception:
            self._widget.setConnected(self._manager.isConnected())
            return None

    def setMode(self, mode):
        if mode == "FLUO":
            self.setFluoMode()
        elif mode == "CS":
            self.setCSMode()

    def _get_selected_fluo_cube_name(self):
        if self._last_selected_fluo_cube_name in self._cube_name_to_slot:
            return self._last_selected_fluo_cube_name

        for slot, name in sorted(self._cube_slot_to_name.items()):
            if name != "EMP_BF":
                return name

        return None

    def setFluoMode(self):
        if not self._manager.isConnected():
            self._widget.setConnected(False)
            return

        self._safe_call(self._manager.setCS)

        cube_name = self._get_selected_fluo_cube_name()
        if cube_name:
            slot = self._cube_name_to_slot.get(cube_name)
            if slot:
                self._safe_call(self._manager.setCube, slot)

        self._safe_call(self._manager.setILFieldDiaphragm, 12)
        self._safe_call(self._manager.setCameraPort)

        QtCore.QTimer.singleShot(
            self.FLUO_SHUTTER_DELAY_MS, self._finishSetFluoMode
        )

        self._current_mode = "FLUO"
        self._widget.setMode(self._current_mode)

    def _finishSetFluoMode(self):
        if not self._manager.isConnected():
            self._widget.setConnected(False)
            return

        self._safe_call(self._manager.setILshutter, 1)

    def setCSMode(self):
        if not self._manager.isConnected():
            self._widget.setConnected(False)
            return

        self._safe_call(self._manager.setCS)

        if "EMP_BF" in self._cube_name_to_slot:
            self._safe_call(
                self._manager.setCube, self._cube_name_to_slot["EMP_BF"]
            )

        self._safe_call(self._manager.setCameraPort)
        self._safe_call(self._manager.setMagnScan)

        self._widget.setCurrentPortSide("Left")

        self._current_mode = "CS"
        self._widget.setMode(self._current_mode)

    def setCubeByName(self, cube_name):
        if cube_name not in self._cube_name_to_slot:
            return

        self._last_selected_fluo_cube_name = cube_name

        if self._current_mode == "FLUO" and self._manager.isConnected():
            slot = self._cube_name_to_slot[cube_name]
            self._safe_call(self._manager.setCube, slot)

    def setPortSideByName(self, value):
        if not self._manager.isConnected():
            self._widget.setConnected(False)
            return

        if value == "Left":
            self._safe_call(self._manager.setMagnScan)
        elif value == "Right":
            self._safe_call(self._manager.setMagn1)