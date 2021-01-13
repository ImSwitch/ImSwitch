from .MultiManager import MultiManager


class RS232sManager(MultiManager):
    def __init__(self, rs232deviceInfos, **kwargs):
        super().__init__(rs232deviceInfos, 'rs232', **kwargs)
