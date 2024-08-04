if __name__ == '__main__':
    from imswitch.__main__ import main
    #main(is_headless=True, default_config="example_virtualmicroscope.json")
    #main(is_headless=True, default_config="/Users/bene/ImSwitchConfig/imcontrol_setups/example_virtual_microscope.json", http_port=8001, ssl=True)
    #main(is_headless=True, default_config="/Users/bene/ImSwitchConfig/imcontrol_setups/example_uc2_hik_flowstop.json", http_port=8001, ssl=True)
    #main(is_headless=False, http_port=8001)
    #main(is_headless=True, config_folder="/Users/bene/Downloads")
    main(data_folder="/Volumes/SD/test") # this has to be maintained for DOCKER!
    
