import numpy as np
from imswitch.imcontrol.model.interfaces.standa_ximc_lib_wrapper import XimcLibraryWrapper
from locai.microscope.units import Distance
from imswitch.imcommon.model import initLogger

def get_linear_positioner(axis):
    logger = initLogger('get_linear_positioner', tryInheritParent=True)
    lib = XimcLibraryWrapper()
    cfg_stages = lib.cfg_from_devices()
    try:
        positioner = LinearPositioner(lib=lib, cfg=cfg_stages[axis])
        return positioner

    except SystemError or KeyboardInterrupt as e:
        logger.warning(
            f'Failed to initialize Standa linear positioner: {e})'
        )
        lib.close_device(cfg_stages[axis]["device_ind"])

class LinearPositioner():
    def __init__(self, lib: XimcLibraryWrapper,
                 port_name = None, positioner_name = None, device_ind = None,
                 friendly_name = None, microstep_mode = None, verbose = 0, wait_for_stop_flag = 0,
                 user_units = "mm", user_calibration = None, cfg = None):
        self.lib = lib
        self.port_name = cfg["port_name"] if cfg["port_name"] is not None else port_name
        self.device_ind = cfg["device_ind"] if cfg["device_ind"] is not None else device_ind
        if self.device_ind == -1:
            print("Error when loading stage")
            raise ValueError
        self.user_units = user_units
        self.verbose = verbose
        self.positioner_name = cfg["positioner_name"] if cfg["positioner_name"] is not None else positioner_name
        self.friendly_name = cfg["friendly_name"] if cfg["friendly_name"] is not None else friendly_name
        self.microstep_mode = cfg["microstep_mode"] if cfg["microstep_mode"] is not None else microstep_mode
        self.user_calibration = cfg["user_calibration"] if cfg["user_calibration"] is not None else user_calibration
        self.travel_range = self.get_stage_settings().TravelRange
        self.wait_for_stop_flag = wait_for_stop_flag

    @property
    def verbose(self):
        return self._verbose
    @verbose.setter
    def verbose(self, x):
        self.lib.verbose = x
        self._verbose = x
    @property
    def travel_range(self):
        return self._travel_range
    @travel_range.setter
    def travel_range(self, tr):
        self._travel_range = tr
    @property
    def lib_version(self):
        return self.lib.version
    @property
    def status(self):
        return self.lib.status(self.device_ind)
    @property
    def info(self):
        return self.lib.info(self.device_ind)

    def enable(self):
        return self.lib.open_device(self.port_name)

    def print_header(self):
        if self.verbose:
            self.lib.print_header(self.device_ind)

    def home(self):
        self.lib.home(self.device_ind)

    def zero(self):
        self.lib.zero(self.device_ind)

    def check_position(self, position):
        if isinstance(position, int) or isinstance(position, float):
            return Distance(mm=position)
        elif isinstance(position, Distance):
            if position.mm is None:
                if position.usteps is None:
                    position.usteps = self.microstep_mode
            return position
        elif isinstance(position, tuple) or isinstance(position, list) or isinstance(position, np.ndarray):
            if len(position)!=2:
                raise ValueError(f"Type {type(position)} unvalid. len(position) has to be 2 (len(position)={len(position)})")
            else:
                return Distance(x=position[0], ux=position[1])
        else:
            raise ValueError(f"Type {type(position)} unvalid")

    def wait_for_stop(self, interval=100):
        return self.lib.wait_for_stop(self.device_ind, interval)

    def flex_wait_for_stop(self, interval=100):
        if self.user_units == "mm":
            return self.lib.flex_wait_for_stop(self.device_ind, interval, mode = 0)
        else:
            return self.lib.flex_wait_for_stop(self.device_ind, interval, mode = 1)

    def shift_on(self, distance):
        pos = self.check_position(distance)
        self._shift_on(pos)

    def _shift_on(self, pos):
        if pos.mm is not None:
            self.lib.shift(self.device_ind, distance=pos.mm, udistance=0, mode=0)
        elif self.microstep_mode:
            self.lib.shift(self.device_ind, distance=pos.x, udistance=pos.ux, mode=1)
        else:
            self.lib.shift(self.device_ind, distance=pos.mm, udistance=0, mode=1)

    def move_to(self, position):
        pos = self.check_position(position)
        self._move_to(pos)

    def _move_to(self, pos):
        if pos.mm is not None:
            self.lib.move(self.device_ind, pos.mm, 0, mode=0)
        elif self.microstep_mode:
            self.lib.move(self.device_ind, pos.x, pos.ux)
        else:
            self.lib.move(self.device_ind, pos.x, 0)

    def left(self):
        # TODO: move_towards_motor()
        self.lib.left(self.device_ind)
        if self.wait_for_stop():
            self.lib.wait_for_stop(self.device_ind, interval=50)

    def right(self):
        # TODO: move_towards_front()
        self.lib.right(self.device_ind)
        if self.wait_for_stop():
            self.lib.wait_for_stop(self.device_ind, interval=50)

    def get_position(self):
        if self.user_units == "mm":
            return Distance(mm=self.lib.get_position(self.device_ind, mode=0))
        else:
            return Distance(self.lib.get_position(self.device_ind, mode=1),
                        usteps=self.microstep_mode)

    def get_speed(self):
        if self.user_units == "mm":
            return self.lib.get_speed(self.device_ind, mode = 0)
        else:
            return self.lib.get_speed(self.device_ind, mode = 1)

    def get_max_speed(self):
        # TODO: create class Speed
        if self.user_units == "mm":
            return self.lib.get_max_speed(self.device_ind, mode = 0)
        else:
            return self.lib.get_max_speed(self.device_ind, mode = 1)

    def set_speed(self, speed):
        if self.user_units == "mm":
            self.lib.set_speed(self.device_ind, speed, mode = 0)
        else:
            self.lib.set_speed(self.device_ind, speed, mode = 1)

    @property
    def user_calibration(self):
        return self.lib.get_user_calibration(self.device_ind)
    @user_calibration.setter
    def user_calibration(self, A):
        self._user_calibration = self.lib.set_user_calibration(self.device_ind, A=A)

    @property
    def microstep_mode(self):
        return self.lib.get_microstep_mode(self.device_ind)
    @microstep_mode.setter
    def microstep_mode(self, microstep):
        self._microstep_mode = self.lib.set_microstep_mode(self.device_ind, microstep)

    def get_motor_settings(self):
        return self.lib.get_motor_settings(self.device_ind)

    def get_stage_info(self):
        return self.lib.get_stage_information(self.device_ind)

    def get_stage_settings(self):
        return self.lib.get_stage_settings(self.device_ind)

    def get_engine_settings(self):
        return self.lib.get_engine_settings(self.device_ind)

    def get_stage_name(self):
        return self.lib.get_stage_name(self.device_ind)

    def get_device_information(self):
        return self.lib.get_device_information(self.device_ind)

    def get_move_settings(self):
        if self.user_units == "mm":
            return self.lib.get_move_settings(self.device_ind, mode = 0)
        else:
            return self.lib.get_move_settings(self.device_ind, mode = 1)

    def set_borders(self, borders):
        pass

    def get_borders(self):
        pass

# def test_positioner(device: LinearPositioner):
#     print(f"Dev.Ind={device.device_ind}")
#     # Prints and getters
#     device.verbose = 1  # Print everything.
#
#     lib_ver = device.lib_version
#     info = device.info
#     status = device.status
#     stage_name = device.get_stage_name()
#     move_settings = device.get_move_settings()
#
#     pos = device.get_position()
#     speed = device.get_speed()
#     max_speed = device.get_max_speed()
#     A = device.user_calibration
#     ustep = device.microstep_mode
#     travel_range = device.travel_range
#     # Structs: TODO: convert to dict
#     motor_settings = device.get_motor_settings()
#     stage_info = device.get_stage_info()
#     stage_settings = device.get_stage_settings()
#     eng_settings = device.get_engine_settings()
#
#     # Movement
#     trajectory = [0.1, 0.25, 0.6, .8]
#     shifts = [travel_range/5, -travel_range/8, travel_range/4, -travel_range/5]
#     speed = [0.1, 0.25, 0.75, 0.5]
#     device.set_speed(max_speed/4)
#     device.home()
#     stop = device.flex_wait_for_stop()
#     for p, s in zip(trajectory, speed):
#         a = p*(travel_range)
#         b = s*max_speed
#         device.set_speed(speed=b)
#         device.move_to(position=a)
#         device.wait_for_stop()
#     device.set_speed(speed=max_speed/6)
#     device.home()
#     device.wait_for_stop()
#     for p, s in zip(shifts, speed):
#         b = s*max_speed
#         device.set_speed(speed=b)
#         device.shift_on(p)
#         device.wait_for_stop()
#     device.set_speed(max_speed/4)
#     device.home()
#     device.wait_for_stop()
#
# #
# # if __name__ == "__main__":
# #     from units import Distance, Point, Position
# #
# #     lib = LibraryWrapper()
# #     cfg_stages = lib.cfg_from_devices()
# #
# #     #x_axis = LinearPositioner(lib=lib, cfg=cfg_stages["X-Axis"])
# #     #test_positioner(x_axis)
# #     #y_axis = LinearPositioner(lib=lib, cfg=cfg_stages["Y-Axis"])
# #     #test_positioner(y_axis)
# #     z_axis = LinearPositioner(lib=lib, cfg=cfg_stages["Z-Axis"])
# #     test_positioner(z_axis)
