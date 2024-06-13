import imswitch
import os
import argparse


# python main.py --headless or python3 -m imswitch --headless
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--headless', dest='headless', action='store_true',
                        help='run in headless mode')

    args = parser.parse_args()
    imswitch.IS_HEADLESS = True# args.headless
    
    if imswitch.IS_HEADLESS:
        os.environ["DISPLAY"] = ":0"
        os.environ["QT_QPA_PLATFORM"] = "offscreen"

    from imswitch.__main__ import main
    main()
    # keep the event loop running
    