from imswitch import IS_HEADLESS
if IS_HEADLESS:
    #from .noqt import *
    from .noqtj import *
else:
    from .qt import *
