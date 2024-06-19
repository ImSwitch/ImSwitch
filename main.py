import imswitch
import os
import argparse
# Set environment variables for high DPI scaling
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_SCALE_FACTOR"] = ".9"  # Adjust this value as needed
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
# Set application attributes
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
if __name__ == '__main__':

    from imswitch.__main__ import main
    main()
    