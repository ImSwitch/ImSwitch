def getMainViewAndController(moduleCommChannel, *_args,
                             overrideSetupInfo=None, overrideOptions=None, **_kwargs):
    from .controller import ImConMainController
    from imswitch.imcontrol.model import configfiletools
    from .view import ViewSetupInfo, ImConMainView

    options, setupInfo = configfiletools.loadSetupInfo(ViewSetupInfo)
    if overrideSetupInfo is not None:
        setupInfo = overrideSetupInfo
    if overrideOptions is not None:
        options = overrideOptions

    view = ImConMainView(options, setupInfo)
    try:
        controller = ImConMainController(options, setupInfo, view, moduleCommChannel)
    except Exception as e:
        view.close()
        raise e

    return view, controller


# Copyright (C) 2020, 2021 TestaLab
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
