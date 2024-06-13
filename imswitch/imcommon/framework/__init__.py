import imswitch
if imswitch.IS_HEADLESS:
    from .noqt import *
else:
    from .qt import *
