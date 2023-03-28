from .MultiManager import MultiManager


class StateSelectorsManager(MultiManager):
    """StateSelectorManager interface for dealing with StateSelectorsManagers. It is
    a MultiManager for stateselectors. """

    def __init__(self, stateselectorInfos, **lowLevelManagers):
        super().__init__(stateselectorInfos, 'stateselectors', **lowLevelManagers)
