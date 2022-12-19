__imswitch_module__ = True
__title__ = 'Blockly'

from imswitch.imcommon.model import modulesconfigtools, pythontools, initLogger

from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import threading
import asyncio

# SRC: https://code-maven.com/static-server-in-python
class StaticServer(BaseHTTPRequestHandler):
 
    def do_GET(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
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
            #html = bytes(html, 'utf8')
            self.wfile.write(html)
 
def start_server(httpd):
    #print('Starting httpd')
    httpd.serve_forever()
     
def run(server_class=HTTPServer, handler_class=StaticServer, port=1889):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    t = threading.Thread(target=start_server, args=(httpd,))
    t.start()
    #print('httpd started on port {}'.format(port))

run()
 

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
