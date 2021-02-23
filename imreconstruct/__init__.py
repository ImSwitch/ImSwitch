import os as _os

import constants as _constants


def getMainViewAndController(moduleCommChannel):
    from imreconstruct.controller import ImRecMainController
    from imreconstruct.view import ImRecMainView

    view = ImRecMainView()
    try:
        controller = ImRecMainController(view, moduleCommChannel)
    except Exception as e:
        view.close()
        raise e

    return view, controller


_os.environ['PATH'] = (_os.environ['PATH'] + ';' +
                       _os.path.join(_constants.rootFolderPath, 'libs'))
