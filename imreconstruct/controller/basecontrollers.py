from imcommon.controller import WidgetController, WidgetControllerFactory


class ImRecWidgetControllerFactory(WidgetControllerFactory):
    """ Factory class for creating a ImRecWidgetController object. """

    def __init__(self, commChannel, moduleCommChannel):
        super().__init__(commChannel=commChannel, moduleCommChannel=moduleCommChannel)


class ImRecWidgetController(WidgetController):
    """ Superclass for all ImRecWidgetController. """

    def __init__(self, commChannel, *args, **kwargs):
        # Protected attributes, which should only be accessed from controller and its subclasses
        self._commChannel = commChannel

        # Init superclass
        super().__init__(*args, **kwargs)
