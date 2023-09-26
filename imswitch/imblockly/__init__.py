import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

def getMainViewAndController(moduleCommChannel, multiModuleWindowController, moduleMainControllers,
                             *_args, **_kwargs):
    from .controller import ImScrMainController
    from .view import ImScrMainView

    view = ImScrMainView()
    try:
        controller = ImScrMainController(
            view,
            moduleCommChannel=moduleCommChannel,
            multiModuleWindowController=multiModuleWindowController,
            moduleMainControllers=moduleMainControllers
        )
    except Exception as e:
        view.close()
        raise e

    return view, controller

