__imswitch_module__ = True
__title__ = 'Hardware Control'


def getMainViewAndController(moduleCommChannel, *_args,
                             overrideSetupInfo=None, overrideOptions=None, **_kwargs):
    from imswitch.imcommon.model import initLogger
    from .controller import ImConMainController
    from .model import configfiletools
    from .view import ViewSetupInfo, ImConMainView

    logger = initLogger('imcontrol init')

    def pickSetup(options):
        import dataclasses
        import sys
        from qtpy import QtWidgets
        from imswitch.imcontrol.view import PickSetupDialog

        # Let user pick the setup to use
        pickSetupDialog = PickSetupDialog()
        pickSetupDialog.setSetups(configfiletools.getSetupList())
        result = pickSetupDialog.exec_()
        setupFileName = pickSetupDialog.getSelectedSetup()
        if result != QtWidgets.QDialog.Accepted or not setupFileName:
            logger.critical('User did not pick a setup to use')
            sys.exit()
        return dataclasses.replace(options, setupFileName=setupFileName)

    if overrideOptions is None:
        options, optionsDidNotExist = configfiletools.loadOptions()
        if optionsDidNotExist:
            options = pickSetup(options)  # Setup to use not set, let user pick

        configfiletools.saveOptions(options)
    else:
        options = overrideOptions

    if overrideSetupInfo is None:
        try:
            setupInfo = configfiletools.loadSetupInfo(options, ViewSetupInfo)
        except FileNotFoundError:
            # Have user pick setup anyway
            options = pickSetup(options)
            configfiletools.saveOptions(options)
            setupInfo = configfiletools.loadSetupInfo(options, ViewSetupInfo)
    else:
        setupInfo = overrideSetupInfo

    logger.info(f'Setup used: {options.setupFileName}')
    
    view = ImConMainView(options, setupInfo)
    try:
        controller = ImConMainController(options, setupInfo, view, moduleCommChannel)
    except Exception as e:
        # TODO: To broad exception
        view.close()
        raise e

    return view, controller


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
