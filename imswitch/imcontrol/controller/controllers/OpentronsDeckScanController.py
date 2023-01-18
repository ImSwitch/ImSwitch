import os
import time

from opentrons.types import Point
from opentrons.protocol_api.labware import Labware, Well
from opentrons.simulate import get_protocol_api
from opentrons.util.entrypoint_util import labware_from_paths
from opentrons_shared_data.deck import load

from typing import Dict, List
from functools import partial
from qtpy import QtCore, QtWidgets
import json

from imswitch.imcommon.model import APIExport
from ..basecontrollers import ImConWidgetController, LiveUpdatedController
from imswitch.imcontrol.view import guitools as guitools
from imswitch.imcommon.model import initLogger, APIExport, ostools
from imswitch.imcontrol.controller.controllers.PositionerController import PositionerController

class OpentronsDeckScanController(LiveUpdatedController):
    """ Linked to OpentronsDeckScanWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self, instanceName="OpentronsScanController")
