import pytest
import napari
import numpy as np
from imswitch.imcontrol.controller.controllers.OptController import (
    OptController,
    FBPliveRecon,
)
from ImSwitchOpt.imswitch.imcontrol.view.widgets.OptWidget import OptWidget
from imswitch.imcontrol.controller.CommunicationChannel import CommunicationChannel
from imswitch.imcontrol.controller.MasterController import MasterController
from imswitch.imcommon.controller import (
    MainController,
    ModuleCommunicationChannel,
)
from . import detectorInfosNonSquare, setupInfoOPTBasic


# functional test
# TODO: expand this test
@pytest.mark.parametrize(
    'opt_settings, expected',
    [({'OptStepsEdit': 2}, {'optSteps': np.array([0, 1600])}),
     ],
)
def test_opt_scan_controller(opt_settings, expected):
    self = MainController()
    # Create the scan controller
    self._setupInfo = setupInfoOPTBasic
    self._moduleCommChannel = ModuleCommunicationChannel()
    self._comm = CommunicationChannel(self, setupInfoOPTBasic)
    self._master = MasterController(self._setupInfo, self._comm,
                                    self._moduleCommChannel)
    viewer = napari.Viewer(show=False)
    widget = OptWidget(options=None, napariViewer=viewer)

    optController = OptController(
                        self._setupInfo,
                        self._comm,
                        self._master,
                        widget=widget,
                        factory=None,
                        moduleCommChannel=self._moduleCommChannel,
                        )
    assert optController.forOptDetectorsList == ['DMK']
    assert optController.rotatorsList == ["ArduinoStepper"]
    assert optController.stepsPerTurn == 3200

    # set OPT settings
    for k, v in opt_settings.items():
        widget.scanPar[k].setValue(v)

    optController.prepareOPTScan()

    assert optController.optSteps == opt_settings['OptStepsEdit']
    assert optController.optWorker.optSteps.all() == expected['optSteps'].all()


# unit live recon test
# TODO: expand this test
@pytest.mark.parametrize(
    'init_vals, expected',
    [(([0, 1, 2, 3], 32), (np.array([0, 1, 2, 3]), 32)),  # can receive a list
     ((np.array([2., 3., 2,]), 16), (np.array([2., 3., 2,]), 16))
     ],
)
def test_FBP_live_recon(init_vals, expected):
    fbpLiveRecon = FBPliveRecon(init_vals[0], init_vals[1])
    # Check the FBP live reconstruction is created
    assert fbpLiveRecon is not None
    # check line
    assert fbpLiveRecon.line.all() == expected[0].all()
    # Check the number of steps
    assert fbpLiveRecon.n_steps == expected[1]
    assert fbpLiveRecon.recon.shape == (
                                        len(expected[0]),
                                        len(expected[0]),
                                        )
