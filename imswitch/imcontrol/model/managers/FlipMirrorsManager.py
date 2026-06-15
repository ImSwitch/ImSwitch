from .MultiManager import MultiManager


class FlipMirrorsManager(MultiManager):
    """MultiManager for motorized flip mirrors."""

    def __init__(self, flipMirrorInfos, **lowLevelManagers):
        super().__init__(flipMirrorInfos or {}, "flipMirrors", **lowLevelManagers)

    def reset_connections(self):
        return self.execOnAll(lambda manager: manager.reset_connection())