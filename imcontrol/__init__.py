def getMainViewAndController(moduleCommChannel):
    from imcontrol.controller import configfileutils, ImConMainController
    from imcontrol.view import ViewSetupInfo, ImConMainView

    setupInfo = configfileutils.loadSetupInfo(ViewSetupInfo)

    view = ImConMainView(setupInfo)
    try:
        controller = ImConMainController(setupInfo, view, moduleCommChannel)
    except Exception as e:
        view.close()
        raise e

    return view, controller
