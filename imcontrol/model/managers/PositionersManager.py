from .MultiManager import MultiManager


class PositionersManager(MultiManager):
    def __init__(self, positionerInfos, **kwargs):
        super().__init__(positionerInfos, 'positioners', **kwargs)
