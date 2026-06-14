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
