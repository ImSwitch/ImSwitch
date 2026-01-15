from imswitch.imcommon.framework import SignalInterface
from .MultiManager import MultiManager

class SLMsManager(MultiManager,SignalInterface):
    """ Multi manager for SLMs """

    def __init__(self, slmsInfos,*args,**kwargs):
        super().__init__(slmsInfos, 'slms')
        SignalInterface.__init__(self)