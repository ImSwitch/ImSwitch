__imswitch_module__ = True
__title__ = "Arkitekt Control"
from arkitekt import App
from .manifest import identifier, version, logo
from arkitekt.builders import publicscheduleqt
from qtpy import QtCore, QtWidgets

from imswitch.immikro.controller import MikroMainController


def getMainViewAndController(
    moduleCommChannel,
    *_args,
    overrideSetupInfo=None,
    overrideOptions=None,
    moduleMainControllers=None,
    **_kwargs
):
    from imswitch.imcommon.model import initLogger
    from .view import MikroMainView

    logger = initLogger("imcontrol init")

    settings = QtCore.QSettings("napari", f"{identifier}:{version}")


    global_app = publicscheduleqt(
        identifier, version, logo=logo, settings=settings
    )



    the_view = MikroMainView(app=global_app)

    try:
        controller = MikroMainController(
            the_view, global_app, moduleCommChannel, moduleMainControllers
        )
    except Exception as e:
        the_view.close()
        raise e

    return the_view, controller


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
