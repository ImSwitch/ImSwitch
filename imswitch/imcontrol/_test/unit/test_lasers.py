import imswitch.imcontrol.model.managers.lasers.Cobolt0601NewLaserManager as cobolt0601_new
from imswitch.imcontrol.model import LaserInfo
from imswitch.imcontrol.model.managers.lasers.PyCoboltMock import MockCobolt06


def _cobolt0601_new_laser_info():
    return LaserInfo(
        analogChannel=None,
        digitalLine=0,
        managerName='Cobolt0601NewLaserManager',
        managerProperties={
            'digitalPorts': ['COM-MOCK']
        },
        valueRangeMin=0,
        valueRangeMax=100,
        wavelength=488
    )


def test_cobolt0601_new_laser_manager_falls_back_to_mock(monkeypatch):
    class FailingCobolt06:
        def __init__(self, *args, **kwargs):
            raise RuntimeError('No Cobolt hardware available')

    monkeypatch.setattr(cobolt0601_new, 'Cobolt06', FailingCobolt06)
    monkeypatch.setattr(cobolt0601_new, 'list_lasers', lambda: [])

    manager = cobolt0601_new.Cobolt0601NewLaserManager(
        _cobolt0601_new_laser_info(),
        '488'
    )

    assert manager._isMock is True
    assert isinstance(manager._laser, MockCobolt06)
    assert manager.consumeOnEnableWarning() is None
    assert manager.name == '488'
    assert manager.valueUnits == 'mW'

    assert manager._laser.is_on() is True
    assert manager._laser.paused is True

    manager.setEnabled(True)
    assert manager._laser.paused is False
    assert manager._laser.get_mode() == 'ConstantPower'

    manager.setValue(42)
    assert manager._laser.power == 42

    manager.setScanModeActive(True)
    assert manager.getModulationPower() == 42
    assert manager._laser.get_mode() == 'PowerModulation'

    manager.setValue(0)
    assert manager._laser.get_mode() == 'CurrentModulation'
    assert manager._laser.get_modulation_current() == 0.1

    manager.setModulationEnabled(False)
    assert manager._laser.get_modulation_state()[0] == '0'
    assert manager.getAllDeviceNames() == ['COM-MOCK']

    manager.finalize()
    assert manager._laser.is_on() is False


def test_cobolt0601_new_laser_manager_warns_once_when_waiting_for_key(monkeypatch):
    class WaitingForKeyCobolt06(MockCobolt06):
        def turn_on(self):
            self._is_on = True
            self._state = 'AutostartWaitingForKeyOn'
            return 'OK'

    monkeypatch.setattr(cobolt0601_new, 'Cobolt06', WaitingForKeyCobolt06)

    manager = cobolt0601_new.Cobolt0601NewLaserManager(
        _cobolt0601_new_laser_info(),
        '488'
    )

    assert manager._isMock is False
    assert manager._laser.is_on() is True
    assert manager._laser.paused is True

    warning = manager.consumeOnEnableWarning()
    assert '488' in warning
    assert 'waiting for the key' in warning
    assert manager.consumeOnEnableWarning() is None
    manager.finalize()


def test_cobolt0601_new_laser_manager_warns_when_on_but_waiting_for_key(monkeypatch):
    class OnButWaitingForKeyCobolt06(MockCobolt06):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._is_on = True
            self._state = 'AutostartWaitingForKeyOn'

    monkeypatch.setattr(cobolt0601_new, 'Cobolt06', OnButWaitingForKeyCobolt06)

    manager = cobolt0601_new.Cobolt0601NewLaserManager(
        _cobolt0601_new_laser_info(),
        '488'
    )

    warning = manager.consumeOnEnableWarning()
    assert 'waiting for the key' in warning
    assert manager.consumeOnEnableWarning() is None
    manager.finalize()


def test_cobolt0601_new_laser_manager_does_not_warn_when_laser_is_on(monkeypatch):
    class LaserOnCobolt06(MockCobolt06):
        pass

    monkeypatch.setattr(cobolt0601_new, 'Cobolt06', LaserOnCobolt06)

    manager = cobolt0601_new.Cobolt0601NewLaserManager(
        _cobolt0601_new_laser_info(),
        '488'
    )

    assert manager._isMock is False
    assert manager._laser.is_on() is True
    assert manager._laser.paused is True

    assert manager.consumeOnEnableWarning() is None
    manager.finalize()
