from imswitch import IS_HEADLESS
if IS_HEADLESS:
    #from .noqt import *
    from .noqt import *
else:
    from .qt import *
