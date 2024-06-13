from .ImConMainView import ImConMainView, ImConMainViewNoQt
from .guitools import ViewSetupInfo
import imswitch
# FIXME: hacky way to do that I guess..
if not imswitch.IS_HEADLESS:
    from .PickSetupDialog import PickSetupDialog
    from .PickUC2BoardConfigDialog import PickUC2BoardConfigDialog
    from .SLMDisplay import SLMDisplay
    from .SIMDisplay import SIMDisplay
    
