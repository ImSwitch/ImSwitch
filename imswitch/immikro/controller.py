from imswitch.imcommon.controller import MainController
from mikro.api.schema import (
    from_xarray,
)
from arkitekt import App
from rekuest.qt.builders import qtinloopactifier, qtwithfutureactifier
import xarray as xr

from imswitch.imcommon.model.logging import initLogger
from imswitch.imcontrol.controller.controllers.ImageController import ImageController
from imswitch.imcontrol.controller.controllers.LaserController import LaserController
from rekuest.widgets import SliderWidget
from mikro.api.schema import (
    RepresentationFragment,
    OmeroRepresentationInput,
    PhysicalSizeInput,
    ChannelInput,
)
import numpy as np
from koil.qt import QtFuture


class MikroMainController(MainController):
    def __init__(
        self, mainView, app: App, moduleCommChannel, moduleMainControllers
    ):
        self.__logger = initLogger(self)
        self.__logger.debug("Initializing")

        self.__mainView = mainView
        self.__moduleCommChannel = moduleCommChannel
        self.__moduleMainControllers = moduleMainControllers

        self.__app = app

        self.__mainView.magic_bar.app_up.connect(self.on_app_up)
        self.__mainView.magic_bar.app_down.connect(self.on_app_down)


        # An actifier that will be used to register the functions
        # actifiers are used to defined the asynchronous wrapping of the function
        # i.e should the function be run in the main thread or in a separate thread
        # if not provided arkitekt will offload the function to a separate thread

        # here we are using the qtinloopactifier which will run the function in the main thread of
        # the qt application and return the result of that functioncall, this is often not a good idea
        self.qt_actifier = qtinloopactifier
        # A future actifier can be used to pass the function a future object that can be resolved
        # at a later time, this is useful for functions that need to wait for a signal to be emitted
        # before they can continue
        self.qt_future_activier = qtwithfutureactifier

        # Will be run in the main thread
        self.__app.rekuest.register(builder=self.qt_actifier)(self.call_run_scan)
        self.__app.rekuest.register(builder=self.qt_actifier)(self.toggle_grid)
        self.__app.rekuest.register(
            builder=self.qt_actifier, widgets={"value": SliderWidget(min=0, max=1024)}
        )(self.set_laser_value)


        # Will be run in a separate thread
        self.__app.rekuest.register()(self.snap_image)


        # WIll run in the main thread, but will be passed a future object that can be
        # resolved at a later time
        self.__app.rekuest.register(builder=self.qt_future_activier)(self.on_do_stuff_async)

    @property
    def api(self):
        return self.__api

    @property
    def shortcuts(self):
        return self.__shortcuts


    def on_do_stuff_async(self, qtfuture: QtFuture, hello: str) -> str:
        """Do Stuff Async

        This function will be run in the main thread, but will be passed a future object
        that can be resolved at a later time. This is useful for functions that need to
        wait for a signal to be emitted before they can continue.

        Args:
            qtfuture (QFuture): The future object that can be resolved at a later time.
            hello (str): A string that will be printed to the console.

        Returns:
            str: A string that will be returned to the caller.
        """
        print(hello)

        # YOu can store the future object and resolve it at a later time

        self._to_be_resolved_future = qtfuture


        #here we are resolving the future object with the value 42 immediately
        # This is not very useful, but you can imagine that you would resolve the future
        # object when a signal is emitted or when some other condition is met
        qtfuture.resolve("42")

        
        return None



    def call_run_scan(self):
        """Run Scan

        Runs the currently active scan that is open on imswitch.
        """
        controlMainController = self._MikroMainController__moduleMainControllers[
            "imcontrol"
        ]
        scanController = controlMainController.controllers["Scan"]
        scanController.runScan()

    def snap_image(
        self, xdims: int = 1000, ydims: int = 1000
    ) -> RepresentationFragment:
        """Snap Image

        Snaps a single image from the camera.

        Args:
            xdims (int): The dimensions of the image in the x direction.
            ydims (int): The dimensions of the image in the y direction.

        Returns:
            RepresentationFragment: The generated image.
        """
        controlMainController = self._MikroMainController__moduleMainControllers[
            "imcontrol"
        ]
        laserController: LaserController = controlMainController.controllers["Laser"]
        active_channels = laserController.getLaserNames()

        metadata = OmeroRepresentationInput(
            physicalSize=PhysicalSizeInput(x=2, y=2),
            channels=[ChannelInput(name=channel) for channel in active_channels],
        )

        image = np.random.random((xdims, ydims, len(active_channels)))
        return from_xarray(
            xr.DataArray(image, dims=["x", "y", "c"]),
            name="Randomly generated image",
            omero=metadata,
        )

    def toggle_grid(self, enabled=False):
        """Toggle Grid

        Toggles the grid on and off.

        Args:
            enabled (bool, optional): Should we turn the grid on?. Defaults to False.
        """
        controlMainController = self._MikroMainController__moduleMainControllers[
            "imcontrol"
        ]
        imageController = controlMainController.controllers["Image"]
        imageController.gridToggle(enabled)

    def set_laser_value(self, lasername: str, value: int):
        """Set Laser Value

        Sets the value of the laser.

        Args:
            lasername (str): The lasername value
            value (int): the value to set the laser to
        """
        controlMainController = self._MikroMainController__moduleMainControllers[
            "imcontrol"
        ]
        laserController: LaserController = controlMainController.controllers["Laser"]
        laserController.setLaserValue(lasername, value)

    def on_app_up(self):

        print("App up")

    def on_app_down(self):
        print("App down")

    def closeEvent(self):
        self.__logger.debug("Shutting down")


# Copyright (C) 2020-2021 ImSwitch developers
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
