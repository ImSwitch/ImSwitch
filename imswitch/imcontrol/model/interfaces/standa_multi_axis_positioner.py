from imswitch.imcontrol.model.interfaces.standa_linear_positioner import LinearPositioner
from imswitch.imcontrol.model.interfaces.standa_ximc_lib_wrapper import XimcLibraryWrapper
import numpy as np
from imswitch.imcommon.model import initLogger

from opentrons.types import Point

X_SPEED = 12.5
Y_SPEED = 12.5
Z_SPEED = 8

def get_multiaxis_positioner(axes):
    logger = initLogger('get_multiaxis_positioner', tryInheritParent=True)
    lib = XimcLibraryWrapper()
    cfg_stages = lib.cfg_from_devices()
    try:
        x_axis = LinearPositioner(lib=lib, cfg=cfg_stages["X"]) if "X" in axes else None
        y_axis = LinearPositioner(lib=lib, cfg=cfg_stages["Y"]) if "Y" in axes else None
        z_axis = LinearPositioner(lib=lib, cfg=cfg_stages["Z"]) if "Z" in axes else None
        stage = MultiAxisPositioner(x_axis=x_axis, y_axis=y_axis, z_axis=z_axis)
        return stage
    except SystemError or KeyboardInterrupt as e:
        logger.warning(
            f'Failed to initialize Standa multiaxis positioner: {e})'
        )
        [lib.close_device(cfg_stages[axis]["device_ind"]) for axis in ["X","Y","Z"]]

class MultiAxisPositioner():

    def __init__(self, x_axis: LinearPositioner, y_axis: LinearPositioner, z_axis: LinearPositioner,
                 default_speeds = [X_SPEED, Y_SPEED, Z_SPEED], verbose = 0):
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.z_axis = z_axis
        self.verbose = verbose
        self.default_speeds = default_speeds
        self.mapper = {"X":0, "Y":1, "Z":2}

    @property
    def verbose(self):
        return self._verbose
    @verbose.setter
    def verbose(self, v):
        for dev in self.devices:
            dev.verbose = v
        self._verbose = v
    @property
    def devices(self):
        return [self.x_axis, self.y_axis, self.z_axis]

    def home(self):
        if hasattr(self,"z_axis"):
            self.z_axis.home()
            self.z_axis.flex_wait_for_stop()
        self.x_axis.home()
        self.y_axis.home()
        for i,dev in enumerate(self.devices):
            dev.flex_wait_for_stop()
            if self.verbose: print(f"Axis {i+1}")

    def zero(self):
        for dev in self.devices:
            dev.zero()
        for i, dev in enumerate(self.devices):
            dev.flex_wait_for_stop()
            if self.verbose: print(f"Axis {i + 1}")

    def get_position(self):
        if len(self.devices) == 3:
            d = []
            for i,dev in enumerate(self.devices):
                d.append(dev.get_position().to_float())
        else:
            print(f"{len(self.devices)} devices detected. Unable to get 3D position")
            raise ValueError
        return Point(d[0], d[1], d[2])

    def check_position(self, p):
        if isinstance(p, Point):
            return p
        elif isinstance(p, tuple):
            return Point(*p)
        else:
            raise TypeError("The position must be a Point or tuple.")

    def move_to(self, position):
        position = self.check_position(position)
        for dev, p in zip(self.devices, position):
            dev.move_to(p)
        # self.wait_for_stop(self.devices)

    def wait_for_stop(self, devices: [LinearPositioner] = None):
        if devices is None:
            devices = self.devices
        for dev in devices:
            dev.flex_wait_for_stop()

    def shift_on(self, shift):
        shift = self.check_position(shift)
        for dev, p in zip(self.devices, shift):
            dev.shift_on(p)
        # self.wait_for_stop(self.devices)


    def get_speed(self):
        return [dev.get_speed() for dev in self.devices]

    def get_max_speed(self):
        return [dev.get_max_speed() for dev in self.devices]

    @property
    def default_speeds(self):
        return self._default_speeds
    @default_speeds.setter
    def default_speeds(self, speeds):
        self.set_speed(speed=speeds)
        self._default_speeds = speeds

    def set_default_speeds(self):
        self.set_speed(self.default_speeds)

    def set_speed(self, speed):
        if isinstance(speed, int) or isinstance(speed, float):
            for dev in self.devices:
                dev.set_speed(speed)
        elif isinstance(speed, list) or isinstance(speed, tuple) or isinstance(speed, np.ndarray):
            for dev, sp in zip(self.devices, speed):
                dev.set_speed(sp)
        elif isinstance(speed, dict):
            for axis, sp in speed.items():
                self.devices[self.mapper[axis]].set_speed(sp)
        else:
            raise ValueError(f"Type {type(speed)} unvalid")

def initialize_stage():
    from locai.microscope.stage.ximc_lib_wrapper import XimcLibraryWrapper
    lib = XimcLibraryWrapper()
    cfg_stages = lib.cfg_from_devices()

    x_axis = LinearPositioner(lib=lib, cfg=cfg_stages["X"])
    y_axis = LinearPositioner(lib=lib, cfg=cfg_stages["Y"])
    z_axis = LinearPositioner(lib=lib, cfg=cfg_stages["Z"])
    stage = MultiAxisPositioner(x_axis=x_axis, y_axis=y_axis, z_axis=z_axis)
    stage.x_axis.set_speed(X_SPEED)
    stage.y_axis.set_speed(Y_SPEED)
    stage.z_axis.set_speed(Z_SPEED)
    return stage

def multi_axis_positioner_test(device: MultiAxisPositioner):
    import numpy as np

    device.verbose = 1

    travel_range = [d.travel_range for d in device.devices]

    shifts = [[t/5, -t/8, t/4, -t/5] for t in travel_range]
    trajectory = np.array(shifts).transpose()

    speed = [0.1, 0.25, 0.75, 0.5]
    max_speed = device.get_max_speed()
    speeds = np.array([speed]).transpose()*np.array([max_speed])
    device.home()
    device.get_position()
    for s,sp in zip(trajectory, speeds):
        device.set_speed(sp)
        device.shift_on(s)
    device.set_speed((5,5,2.5))
    device.home()
    device.set_speed((1,5,2.5))
    device.move_to((100,100,25))
    device.set_speed((10,10,5))
    device.home()

# if __name__ == "__main__":
#     from opentrons.types import Point
#     from locai.microscope.stage.ximc_lib_wrapper import LibraryWrapper
#
#     lib = LibraryWrapper()
#     cfg_stages = lib.cfg_from_devices()
#
#     x_axis = LinearPositioner(lib=lib, cfg=cfg_stages["X-Axis"])
#     y_axis = LinearPositioner(lib=lib, cfg=cfg_stages["Y-Axis"])
#     z_axis = LinearPositioner(lib=lib, cfg=cfg_stages["Z-Axis"])
#     stage = MultiAxisPositioner(x_axis=x_axis, y_axis=y_axis, z_axis=z_axis)
#     multi_axis_positioner_test(stage)