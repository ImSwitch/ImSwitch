import importlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields as dataclass_fields

from imswitch.imcommon.model import pythontools, initLogger
from ..errors import InvalidChildClassError


class SignalDesigner(ABC):
    """Parent class for any type of SignalDesigner. Any child should define
    self._expected_parameters and its own make_signal method."""

    def __init__(self):
        self._logger = initLogger(self)

        self.lastSignal = None
        self.lastParameterDict = None
        self._expectedParameters = None

    @property
    def expectedParameters(self):
        if self._expectedParameters is None:
            raise ValueError('Value "%s" is not defined')
        else:
            return self._expectedParameters

    def isValidSignalDesigner(self):
        if self._expectedParameters is None:
            raise InvalidChildClassError('Child of SignalDesigner should define \
                                 "self.expected_parameters" in __init__.')
        else:
            return True

    def parameterCompatibility(self, parameterDict):
        """ Method to check the compatibility of parameter 'parameterDict'
        and the expected parameters of the object. """
        expected = set(self._expectedParameters)
        incoming = set([*parameterDict])

        return expected.issubset(incoming)

    @abstractmethod
    def make_signal(self, parameterDict, setupInfo):
        """ Method to be defined by child. Should return a dictionary with
        {'target': signal} pairs. """
        pass


class ScanDesigner(SignalDesigner, ABC):
    @abstractmethod
    def checkSignalComp(self, scanParameters, setupInfo, scanInfo):
        """ Check analog scanning signals so that they are inside the range of
        the acceptable scanner voltages."""
        pass

    def checkSignalLength(self, scanParameters, setupInfo):
        """ Check that the signal would not be too large (to be stored in
        the RAM and to be generated and run inside a reasonable time). """
        return True

    @abstractmethod
    def make_signal(self, parameterDict, setupInfo):
        """ Method to be defined by child. Should return a dictionary with
        {'target': signal} pairs. """
        pass


class TTLCycleDesigner(SignalDesigner, ABC):
    @property
    @abstractmethod
    def timeUnits(self):
        pass

    @abstractmethod
    def make_signal(self, parameterDict, setupInfo, scanInfoDict=None):
        """ Method to be defined by child. Should return a dictionary with
        {'target': signal} pairs. """
        pass


class SignalDesignerFactory:
    """Factory class for creating a SignalDesigner object. Factory checks
    that the new object is compatible with the parameters that will we
    be sent to its make_signal method."""

    def __new__(cls, designerName):
        currentPackage = '.'.join(__name__.split('.')[:-1])
        package = importlib.import_module(pythontools.joinModulePath(currentPackage, designerName))
        signalDesigner = getattr(package, designerName)()

        if signalDesigner.isValidSignalDesigner():
            return signalDesigner


@dataclass
class ScanInfoContract:
    """Complete contract for scan information exchanged between scan designers,
    TTL cycle designers, and detector managers.

    All ScanDesigner subclasses MUST return ``contract.to_dict()`` so that
    every downstream consumer receives a consistent, complete dictionary
    without ad-hoc normalization layers.

    Conventions
    -----------
    - ``img_dims`` contains PHYSICAL scan dimensions only (no linestep).
    - ``n_linesteps`` is always a separate field.
    - ``img_axes_with_linesteps`` is auto-derived in __post_init__ and
      appends ``"linestep"`` when ``n_linesteps > 1``.
    - ``scan_samples`` indices correspond to physical axes, not linestep.
    """

    # --- Required: image geometry (physical axes only) ---
    img_dims: list                  # pixel counts per physical axis, e.g. [Nx, Ny] or [Nx, Ny, Nz]
    img_axes_phys: list             # axis labels, e.g. ["x", "y", "z"]
    pixel_sizes: list               # physical pixel size per axis (µm)

    # --- Required: sample counts ---
    scan_samples: list              # samples per axis level: [per_pixel, per_line, per_frame, ...]
    scan_samples_total: int         # total samples in entire scan signal
    scan_samples_d2_period: int     # samples per fast-axis period (line active + flyback)

    # --- Required: fast-axis helpers ---
    n_pixels_fast: int              # == img_dims[0]
    samples_per_pixel: int          # == scan_samples[0]

    # --- Required: timing ---
    dwell_time: float               # pixel dwell time (seconds)
    scan_time_step: float           # time per sample (seconds), i.e. 1 / sampleRate

    # --- Linestep ---
    n_linesteps: int = 1

    # --- Throw / padding (in scan samples) ---
    scan_throw_startzero: int = 0
    scan_throw_settling: int = 0
    scan_throw_startacc: int = 0
    scan_pads_initpos: list = field(default_factory=list)

    # --- Phase and smoothing ---
    phase_delay: int = 0
    smooth_axes: list = field(default_factory=lambda: [False, False, False])

    # --- Auto-derived (populated in __post_init__) ---
    img_axes_with_linesteps: list = field(default_factory=list)
    axis_names: list = field(default_factory=list)

    # --- Optional / informational ---
    minmaxes: list = field(default_factory=list)
    tot_scan_time_s: float = 0.0

    # --- Beta-designer compatibility (BetaTTLCycleDesigner reads these) ---
    positions: list = field(default_factory=list)
    return_time: float = 0.0

    def __post_init__(self):
        if not self.img_axes_with_linesteps:
            self.img_axes_with_linesteps = list(self.img_axes_phys) + (
                ["linestep"] if self.n_linesteps > 1 else []
            )
        if not self.axis_names:
            self.axis_names = list(self.img_axes_phys)
        # Ensure smooth_axes covers all physical axes
        while len(self.smooth_axes) < len(self.img_dims):
            self.smooth_axes = list(self.smooth_axes) + [False]

    def to_dict(self) -> dict:
        """Convert to a plain dict for backward compatibility with all consumers."""
        result = {}
        for f in dataclass_fields(self):
            result[f.name] = getattr(self, f.name)
        return result


# Copyright (C) 2020-2021 ImSwitch developers
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
