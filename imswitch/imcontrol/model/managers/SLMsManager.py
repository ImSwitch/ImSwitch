from imswitch.imcommon.framework import SignalInterface
from .MultiManager import MultiManager
from imswitch.imcommon.model import initLogger
from imswitch.imcommon.framework import Signal

class SLMsManager(MultiManager,SignalInterface):
    """ Multi manager for SLMs """

    def __init__(self, slmsInfos,*args,**kwargs):
        super().__init__(slmsInfos, 'slms')
        SignalInterface.__init__(self)