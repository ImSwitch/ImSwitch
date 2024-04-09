import imswitch
import os

if imswitch.IS_HEADLESS:
    os.environ["DISPLAY"] = ":0"
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

from imswitch.__main__ import main
main()