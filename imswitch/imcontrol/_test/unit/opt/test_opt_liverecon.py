import pytest
from imswitch.imcontrol.controller.controllers.ScanControllerOpt import (
    ScanControllerOpt,
    FBPliveRecon,
)
from . import detectorInfosNonSquare


# Test the FBP live reconstruction
def test_FBP_live_recon(qtbot):
    # Create the scan controller
    scanController = ScanControllerOpt(detectorInfosNonSquare)
    # Create the FBP live reconstruction
    fbpLiveRecon = FBPliveRecon(scanController)
    # Check the FBP live reconstruction is created
    assert fbpLiveRecon is not None
