from .MultiManager import MultiManager


class LasersManager(MultiManager):
    def __init__(self, laserInfos, **kwargs):
        super().__init__(laserInfos, 'lasers', **kwargs)
