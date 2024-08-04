import importlib
import traceback
import logging
import argparse
import os

import imswitch
# python main.py --headless or
# python -m imswitch --headless 1 --config-file example_virtual_microscope.json --config-folder /Users/bene/Downloads
# py
def main(is_headless:bool=None, default_config:str=None, http_port:int=None, ssl:bool=None, config_folder:str=None,
         data_folder: str=None):
    '''
    is_hedless
    
    '''
    try:
        try: # Google Colab does not support argparse
            parser = argparse.ArgumentParser(description='Process some integers.')

            # specify if run in headless mode
            parser.add_argument('--headless', dest='headless', type=bool, default=0,
                                help='run in headless mode')

            # specify config file name - None for default
            parser.add_argument('--config-file', dest='config_file', type=str, default=None,
                                help='specify run with config file')

            # specify http port
            parser.add_argument('--http-port', dest='http_port', type=int, default=8001,
                                help='specify http port')

            # specify ssl
            parser.add_argument('--ssl', dest='ssl', type=bool, default=True,
                                help='specify ssl')
            
            # specify the config folder (e.g. if running from a different location / container)
            parser.add_argument('--config-folder', dest='config_folder', type=str, default=None,
                                help='specify config folder')
            
            parser.add_argument('--ext-data-folder', dest='data_folder', type=str, default=None, 
                                help='point to a folder to store the data. This overrides the ImSwitchConfig, useful for docker volumes')

            args = parser.parse_args()
            
            imswitch.IS_HEADLESS = args.headless            # if True, no QT will be loaded   
            imswitch.__httpport__ = args.http_port          # e.g. 8001
            imswitch.__ssl__ = args.ssl                     # if True, ssl will be used (e.g. https)
            
            if type(args.config_file)==str and args.config_file.find("json")>=0:  # e.g. example_virtual_microscope.json
                imswitch.DEFAULT_SETUP_FILE = args.config_file  
            if os.path.isdir(args.config_folder):
                imswitch.DEFAULT_CONFIG_PATH = args.config_folder # e.g. /Users/USER/ in case an alternative path is used
            if os.path.isdir(args.data_folder):
                imswitch.DEFAULT_DATA_PATH = args.data_folder # e.g. /Users/USER/ in case an alternative path is used
            
        except Exception as e:
            print(e)
            pass
        # override settings if provided as argument
        if is_headless is not None:
            print("We use the user-provided headless flag: " + str(is_headless))
            imswitch.IS_HEADLESS = is_headless
        if default_config is not None:
            print("We use the user-provided configuration file: " + default_config)
            imswitch.DEFAULT_SETUP_FILE = default_config
        if http_port is not None:
            print("We use the user-provided http port: " + str(http_port))
            imswitch.__httpport__ = http_port
        if ssl is not None:
            print("We use the user-provided ssl: " + str(ssl))
            imswitch.__ssl__ = ssl
        if config_folder is not None:
            print("We use the user-provided configuration path: " + config_folder)
            imswitch.DEFAULT_CONFIG_PATH = config_folder
        if data_folder is not None:
            print("We use the user-provided data path: " + data_folder)
            imswitch.DEFAULT_DATA_PATH = data_folder

        # FIXME: !!!! This is because the headless flag is loaded after commandline input
        from imswitch.imcommon import prepareApp, launchApp
        from imswitch.imcommon.controller import ModuleCommunicationChannel, MultiModuleWindowController
        from imswitch.imcommon.model import modulesconfigtools, pythontools, initLogger

        logger = initLogger('main')
        logger.info(f'Starting ImSwitch {imswitch.__version__}')
        logger.info(f'Headless mode: {imswitch.IS_HEADLESS}')
        logger.info(f'Config file: {imswitch.DEFAULT_SETUP_FILE}')
        logger.info(f'Config folder: {imswitch.DEFAULT_CONFIG_PATH}')
        logger.info(f'Data folder: {imswitch.DEFAULT_DATA_PATH}')
        
        if imswitch.IS_HEADLESS:
            os.environ["DISPLAY"] = ":0"
            os.environ["QT_QPA_PLATFORM"] = "offscreen"
        else:
            app = prepareApp()
        enabledModuleIds = modulesconfigtools.getEnabledModuleIds()

        if 'imscripting' in enabledModuleIds:
            if imswitch.IS_HEADLESS:
                enabledModuleIds.remove('imscripting')
            else:
                # Ensure that imscripting is added last
                enabledModuleIds.append(enabledModuleIds.pop(enabledModuleIds.index('imscripting')))

        if 'imnotebook' in enabledModuleIds and not imswitch.IS_HEADLESS:
            # Ensure that imnotebook is added last
            try:
                from PyQt5 import QtWebEngine
                enabledModuleIds.append(enabledModuleIds.pop(enabledModuleIds.index('imnotebook')))
            except ImportError:
                logger.error('QtWebEngineWidgets not found, disabling imnotebook')
                enabledModuleIds.remove('imnotebook')

        modulePkgs = [importlib.import_module(pythontools.joinModulePath('imswitch', moduleId))
                    for moduleId in enabledModuleIds]

        moduleCommChannel = ModuleCommunicationChannel()

        if not imswitch.IS_HEADLESS:
            from imswitch.imcommon.view import MultiModuleWindow, ModuleLoadErrorView
            multiModuleWindow = MultiModuleWindow('ImSwitch')
            multiModuleWindowController = MultiModuleWindowController.create(
                multiModuleWindow, moduleCommChannel
            )
            multiModuleWindow.show(showLoadingScreen=True)
            app.processEvents()  # Draw window before continuing
        else:
            multiModuleWindow = None
            multiModuleWindowController = None
        

        # Register modules
        for modulePkg in modulePkgs:
            moduleCommChannel.register(modulePkg)

        # Load modules
        moduleMainControllers = dict()

        for i, modulePkg in enumerate(modulePkgs):
            moduleId = modulePkg.__name__
            moduleId = moduleId[moduleId.rindex('.') + 1:]  # E.g. "imswitch.imcontrol" -> "imcontrol"

            # The displayed module name will be the module's __title__, or alternatively its ID if
            # __title__ is not set
            moduleName = modulePkg.__title__ if hasattr(modulePkg, '__title__') else moduleId

            try:
                view, controller = modulePkg.getMainViewAndController(
                    moduleCommChannel=moduleCommChannel,
                    multiModuleWindowController=multiModuleWindowController,
                    moduleMainControllers=moduleMainControllers
                )
                logger.info(f'initialize module {moduleId}')
            except Exception as e:
                logger.error(f'Failed to initialize module {moduleId}')
                logger.error(e)
                logger.error(traceback.format_exc())
                moduleCommChannel.unregister(modulePkg)
                if not imswitch.IS_HEADLESS:
                    from imswitch.imcommon.view import ModuleLoadErrorView
                    multiModuleWindow.addModule(moduleId, moduleName, ModuleLoadErrorView(e))
            else:
                # Add module to window
                if not imswitch.IS_HEADLESS: multiModuleWindow.addModule(moduleId, moduleName, view)
                moduleMainControllers[moduleId] = controller

                # Update loading progress
                if not imswitch.IS_HEADLESS:
                    multiModuleWindow.updateLoadingProgress(i / len(modulePkgs))
                    app.processEvents()  # Draw window before continuing
        logger.info(f'init done')
        if not imswitch.IS_HEADLESS:
            launchApp(app, multiModuleWindow, moduleMainControllers.values())
    except Exception as e:
        logging.error(traceback.format_exc())


if __name__ == '__main__':
    main()

# Copyright (C) 2020-2023 ImSwitch developers
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
