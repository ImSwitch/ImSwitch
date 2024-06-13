import imswitch
if not imswitch.IS_HEADLESS:
    # FIXME: hacky way to do that I guess..
    from .ModuleLoadErrorView import ModuleLoadErrorView
    from .MultiModuleWindow import MultiModuleWindow
    from .PickDatasetsDialog import PickDatasetsDialog
