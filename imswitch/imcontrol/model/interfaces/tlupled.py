from imswitch.imcontrol.model.interfaces.tlupled_library_wrapper import TLUPLibraryWrapper
from imswitch.imcommon.model import initLogger

class TLUPLed:
    def __init__(self, lib: TLUPLibraryWrapper, dev_index=0, default_current=0.02):
        super().__init__()
        self.__logger = initLogger(self)
        self.lib = lib
        self.is_connected = False
        self.dev_index = dev_index

        if self.dev_index != 0:
            raise Exception("No camera TLUP connected.")
        else:
            self._init_led(self.dev_index, default_current)



    def _init_led(self, dev_index = 0,  default_current = 0.02):
        self.is_connected = True
        self.__logger.debug("Connecting device")
        self.dev_session = self.lib.available_devices[dev_index]["dev_session"]
        self.name = self.lib.available_devices[dev_index]["name"]
        self.info = self.lib.available_devices[dev_index]["info"]

        # self.led_info = self.lib.get_led_info(self.dev_session)

        self.default_current = default_current if not None else self.lib.get_current_setpoint_at_startup(self.dev_session)
        self.lib.set_current_setpoint_at_startup(self.dev_session, self.default_current)

        self.current_setpoint = self.default_current
        return
    
    def close(self):
        self.__logger.debug("Closing device")

        return self.lib.close_device(self.dev_session)

    def switch_on(self):
        self.__logger.debug("LED on")
        return self.lib.switch_on(devSession=self.dev_session)

    def switch_off(self):
        self.__logger.debug("LED off")
        return self.lib.switch_off(devSession=self.dev_session)

    @property
    def default_current(self):
        return self._default_current
    @default_current.setter
    def default_current(self, current):
        self._default_current = current
        self.lib.set_current_setpoint_at_startup(self.dev_session, current)

    @property
    def current_setpoint(self):
        return self._current_setpoint
    @current_setpoint.setter
    def current_setpoint(self, current):
        self._current_setpoint = current
        self.__logger.debug(f"Setting current setpoint to {current} mA")
        self.lib.set_current_setpoint(self.dev_session, current)

def getLED():
    logger = initLogger('getLED', tryInheritParent=True)
    lib = TLUPLibraryWrapper(verbose=True)
    try:
        upled = TLUPLed(lib=lib)
        return upled

    except SystemError or KeyboardInterrupt as e:
        logger.warning(
            f'Failed to initialize TLUP: {e})'
        )
        lib.close_devices()

#
# if __name__ == "__main__":
#     lib = TLUPLibraryWrapper(verbose=True)
#     try:
#         upled = TLUPLed(lib=lib)
#         upled.switch_on()
#         time.sleep(1)
#         setpoint = upled.current_setpoint
#         for i in list(range(1, 5)):
#             upled.current_setpoint = setpoint + i * 0.1
#             time.sleep(1)
#         upled.switch_off()
#
#     except SystemError or KeyboardInterrupt:
#         lib.close_devices()