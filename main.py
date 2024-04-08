import os

os.environ["DISPLAY"] = ":0"
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from imswitch.__main__ import main
'''
sudo usermod -a -G dialout bene
export DISPLAY=:0
export QT_QPA_PLATFORM=offscreen
'''

main()