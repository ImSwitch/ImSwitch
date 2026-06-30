import importlib.util
import sys
import types
from pathlib import Path


class DummySetupModeController:
    def __init__(self, name, state, calls):
        self.name = name
        self.state = state
        self.calls = calls

    def getSetupModeState(self):
        return dict(self.state)

    def applySetupModeState(self, state):
        self.calls.append(self.name)
        self.state = dict(state)
        return []


class UnsupportedController:
    pass


def make_controller(tmp_path, monkeypatch, controllers):
    setup_mode_module, setup_mode_mixin = load_setup_mode_module(monkeypatch)

    for controller in controllers.values():
        if isinstance(controller, DummySetupModeController):
            controller.__class__ = type(
                "ModeAwareDummySetupModeController",
                (setup_mode_mixin, DummySetupModeController),
                {}
            )

    dirtools = setup_mode_module.dirtools
    monkeypatch.setattr(dirtools.UserFileDirs, "Root", str(tmp_path))
    return setup_mode_module.SetupModeController(controllers)


def load_setup_mode_module(monkeypatch):
    controller_dir = Path(__file__).resolve().parents[2] / "controller"
    package_name = "imswitch.imcontrol.controller"

    package_module = types.ModuleType(package_name)
    package_module.__path__ = [str(controller_dir)]
    monkeypatch.setitem(sys.modules, package_name, package_module)

    class SetupModeMixin:
        pass

    basecontrollers_module = types.ModuleType(f"{package_name}.basecontrollers")
    basecontrollers_module.SetupModeMixin = SetupModeMixin
    monkeypatch.setitem(sys.modules, f"{package_name}.basecontrollers", basecontrollers_module)

    spec = importlib.util.spec_from_file_location(
        f"{package_name}.SetupModeController",
        controller_dir / "SetupModeController.py"
    )
    setup_mode_module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, setup_mode_module)
    spec.loader.exec_module(setup_mode_module)

    return setup_mode_module, SetupModeMixin


def test_setup_mode_roundtrip(tmp_path, monkeypatch):
    calls = []
    laser = DummySetupModeController("Laser", {"power": 10}, calls)
    setup_modes = make_controller(
        tmp_path,
        monkeypatch,
        {
            "Laser": laser,
            "Unsupported": UnsupportedController(),
        }
    )

    result = setup_modes.saveSetupMode(
        "test mode",
        componentNames=["Laser", "Unsupported"],
        description="laser only",
        shortcut="F3"
    )

    assert result["warnings"] == ['Setup mode component "Unsupported" is not available.']
    assert result["mode"]["includedComponents"] == ["Laser"]
    assert result["mode"]["description"] == "laser only"
    assert result["mode"]["shortcut"] == "F3"
    assert setup_modes.listSetupModes() == ["test mode"]

    laser.state = {"power": 0}
    warnings = setup_modes.loadSetupMode("test mode")

    assert warnings == []
    assert laser.state == {"power": 10}
    assert calls == ["Laser"]


def test_setup_mode_metadata_rename_duplicate(tmp_path, monkeypatch):
    calls = []
    setup_modes = make_controller(
        tmp_path,
        monkeypatch,
        {
            "Laser": DummySetupModeController("Laser", {"power": 10}, calls),
        }
    )

    setup_modes.saveSetupMode(
        "original",
        componentNames=["Laser"],
        description="starting point",
        shortcut="F3"
    )

    updated = setup_modes.updateSetupModeMetadata(
        "original", description="updated", shortcut=""
    )
    assert updated["description"] == "updated"
    assert updated["shortcut"] is None

    renamed = setup_modes.renameSetupMode("original", "renamed")
    assert renamed["name"] == "renamed"
    assert setup_modes.listSetupModes() == ["renamed"]

    duplicate = setup_modes.duplicateSetupMode("renamed", "copy", shortcut="F4")
    assert duplicate["name"] == "copy"
    assert duplicate["description"] == "updated"
    assert duplicate["shortcut"] == "F4"
    assert setup_modes.listSetupModes() == ["copy", "renamed"]


def test_setup_mode_apply_order(tmp_path, monkeypatch):
    calls = []
    setup_modes = make_controller(
        tmp_path,
        monkeypatch,
        {
            "Laser": DummySetupModeController("Laser", {"enabled": True}, calls),
            "Scan": DummySetupModeController("Scan", {"size": 1}, calls),
            "Settings": DummySetupModeController("Settings", {"roi": [0, 0, 10, 10]}, calls),
        }
    )

    setup_modes.saveSetupMode("ordered", componentNames=["Laser", "Scan", "Settings"])
    setup_modes.loadSetupMode("ordered")

    assert calls == ["Settings", "Scan", "Laser"]
