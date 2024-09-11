if __name__ == '__main__':
    from imswitch.__main__ import main
    '''
    To start imswitch in headless with a remote config file, you can add additional arguments:
    main(is_headless=True, default_config="/Users/bene/ImSwitchConfig/imcontrol_setups/example_virtual_microscope.json", http_port=8001, ssl=True, data_folder="/Users/bene/Downloads")
    - is_headless: True or False
    - default_config: path to the config file
    - http_port: port number
    - ssl: True or False
    - data_folder: path to the data folder
    '''
    main(is_headless=True, data_folder="/Users/bene/Downloads") # this has to be maintained for DOCKER!
