from imswitch.imcommon.controller import MainController
from imswitch.imcommon.model import generateAPI, pythontools
from imswitch.imblockly.model import getActionsScope
from .CommunicationChannel import CommunicationChannel
from .ImScrMainViewController import ImScrMainViewController
from .basecontrollers import ImScrWidgetControllerFactory
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class ImScrMainController(MainController):
    """ Main controller of imblockly. """

    def __init__(self, mainView, moduleCommChannel, multiModuleWindowController,
                 moduleMainControllers):
        self.__mainView = mainView
        self.__moduleCommChannel = moduleCommChannel
        self.__scriptScope = self._createScriptScope(moduleCommChannel, multiModuleWindowController,
                                                     moduleMainControllers)

        # Connect view signals
        self.__mainView.sigClosing.connect(self.closeEvent)

        # Init communication channel and master controller
        self.__commChannel = CommunicationChannel()

        # List of Controllers for the GUI Widgets
        self.__factory = ImScrWidgetControllerFactory(
            self.__scriptScope, self.__commChannel, self.__moduleCommChannel
        )

        self.mainViewController = self.__factory.createController(
            ImScrMainViewController, self.__mainView
        )
        
        # start serving the blockly files    
        self.server = MyServer()
        self.server.start()


    def _createScriptScope(self, moduleCommChannel, multiModuleWindowController,
                           moduleMainControllers):
        """ Generates a scope of objects that are intended to be accessible by scripts. """

        scope = {}
        scope.update({
            'moduleCommChannel': moduleCommChannel,
            'mainWindow': generateAPI([multiModuleWindowController]),
            'controllers': pythontools.dictToROClass(moduleMainControllers),
            'api': pythontools.dictToROClass(
                {key: controller.api
                 for key, controller in moduleMainControllers.items()
                 if hasattr(controller, 'api')}
            )
        })
        scope.update(getActionsScope(scope.copy()))

        return scope

    def closeEvent(self):
        self.server.stop()
        self.__factory.closeAllCreatedControllers()



class MyServer:
    def __init__(self, port=1889):
        self.port = port
        self.httpd = None
        self.server_thread = None

    class StaticServer(BaseHTTPRequestHandler):
        def do_GET(self):
            root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "view", "static", "index.html")
            if self.path == '/':
                filename = root + '/index.html'
            else:
                filename = root + self.path
            self.send_response(200)
            if filename[-4:] == '.css':
                self.send_header('Content-type', 'text/css')
            elif filename[-5:] == '.json':
                self.send_header('Content-type', 'application/javascript')
            elif filename[-3:] == '.js':
                self.send_header('Content-type', 'application/javascript')
            elif filename[-4:] == '.ico':
                self.send_header('Content-type', 'image/x-icon')
            else:
                self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open(filename, 'rb') as fh:
                html = fh.read()
                self.wfile.write(html)

    def start(self):
        try:
            self.httpd = HTTPServer(('', self.port), self.StaticServer)
            self.server_thread = threading.Thread(target=self.httpd.serve_forever)
            self.server_thread.start()
            print(f'httpd started on port {self.port}')
        except Exception as e:
            print(f'httpd failed to start on port {self.port}')
            print(e)

    def stop(self):
        print('Stopping httpd in Blockly')
        if self.httpd:
            self.httpd.shutdown()
            self.server_thread.join()
            print(f'httpd stopped on port {self.port}')



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
