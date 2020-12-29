import importlib


class PositionersManager:
    def __init__(self, positionerInfos, **kwargs):
        self._positionerManagers = {}
        for positionerName, positionerInfo in positionerInfos.items():
            # Create positioner manager
            package = importlib.import_module(
                'model.managers.positioners.' + positionerInfo.managerName
            )
            manager = getattr(package, positionerInfo.managerName)
            self._positionerManagers[positionerName] = manager(
                positionerInfo, positionerName, **kwargs
            )

    def execOn(self, positionerName, func):
        """ Executes a function on a specific positioner and returns the result. """
        if positionerName not in self._positionerManagers:
            raise NoSuchPositionerError(f'Positioner "{positionerName}" does not exist or is not managed'
                                      f' by this PositionersManager.')

        return func(self._positionerManagers[positionerName])

    def execOnAll(self, func):
        """ Executes a function on all positioners and returns the results. """
        return {positionerName: func(positionerManager)
                for positionerName, positionerManager in self._positionerManagers.items()}
