from .ImConMainView import ImConMainView, ImConMainViewNoQt
from .guitools import ViewSetupInfo
from imswitch import IS_HEADLESS
# FIXME: hacky way to do that I guess..
if not IS_HEADLESS:
    from .PickSetupDialog import PickSetupDialog
    from .PickUC2BoardConfigDialog import PickUC2BoardConfigDialog
    from .SLMDisplay import SLMDisplay
    from .SIMDisplay import SIMDisplay
    
