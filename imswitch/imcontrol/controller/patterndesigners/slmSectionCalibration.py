"""Per-section SLM calibration helpers."""

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

Matrix2x2 = Tuple[Tuple[float, float], Tuple[float, float]]

@dataclass
class SLMSectionCalibration:
    """Map physical displacement in um to SLM linear-phase kxy values."""

    kx_per_um: float = 0.0
    ky_per_um: float = 0.0
    matrix_2x2: Optional[Matrix2x2] = None
    version: int = 1
    created_at: str = ""
    source: str = ""
    plane: str = None
    cam_px_size_um: float = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.kx_per_um = float(self.kx_per_um or 0.0)
        self.ky_per_um = float(self.ky_per_um or 0.0)
        self.matrix_2x2 = self._coerce_matrix(self.matrix_2x2)
        self.version = int(self.version or 1)
        self.created_at = str(self.created_at or "")
        self.source = str(self.source or "")
        self.plane = self._coerce_optional_text(self.plane)
        self.cam_px_size_um = self._coerce_optional_float(self.cam_px_size_um)
        self.metadata = dict(self.metadata or {})

    @classmethod
    def from_linear_phase_test(
        cls,
        period_x_px,
        measured_dx_um,
        period_y_px,
        measured_dy_um,
        source="linear_phase_test",
        created_at=None,
    ):
        """Create a diagonal calibration from a tested phase period."""

        period_x_px = cls._require_positive(period_x_px, "period_x_px")
        period_y_px = cls._require_positive(period_y_px, "period_y_px")
        measured_dx_um = cls._require_nonzero(measured_dx_um, "measured_dx_um")
        measured_dy_um = cls._require_nonzero(measured_dy_um, "measured_dy_um")

        return cls(
            kx_per_um=(1.0 / period_x_px) / measured_dx_um,
            ky_per_um=(1.0 / period_y_px) / measured_dy_um,
            created_at=created_at or datetime.now().isoformat(),
            source=source,
            metadata={
                "period_x_px": period_x_px,
                "period_y_px": period_y_px,
                "measured_dx_um": measured_dx_um,
                "measured_dy_um": measured_dy_um,
            },
        )

    def is_valid(self):
        matrix = self._effective_matrix()
        if matrix is None:
            return False

        values = (matrix[0][0], matrix[0][1], matrix[1][0], matrix[1][1])
        if not all(math.isfinite(value) for value in values):
            return False

        return abs(self._determinant(matrix)) > 0.0

    def um_to_kxy(self, x_um, y_um):
        """Convert physical displacement in um to kxy."""

        matrix = self._valid_matrix()
        x_um = float(x_um)
        y_um = float(y_um)
        kx = matrix[0][0] * x_um + matrix[0][1] * y_um
        ky = matrix[1][0] * x_um + matrix[1][1] * y_um
        return kx, ky

    def kxy_to_um(self, kx, ky):
        """Convert kxy back to physical displacement in um."""

        matrix = self._valid_matrix()
        det = self._determinant(matrix)
        inv = (
            (matrix[1][1] / det, -matrix[0][1] / det),
            (-matrix[1][0] / det, matrix[0][0] / det),
        )
        kx = float(kx)
        ky = float(ky)
        x_um = inv[0][0] * kx + inv[0][1] * ky
        y_um = inv[1][0] * kx + inv[1][1] * ky
        return x_um, y_um

    def to_dict(self):
        matrix = self._effective_matrix()
        return {
            "version": self.version,
            "mapping": "matrix_2x2" if self.matrix_2x2 is not None else "diagonal",
            "kx_per_um": self.kx_per_um,
            "ky_per_um": self.ky_per_um,
            "matrix_2x2": [list(row) for row in matrix] if matrix is not None else None,
            "created_at": self.created_at,
            "source": self.source,
            "plane": self.plane,
            "cam_px_size_um": self.cam_px_size_um,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data):
        if isinstance(data, cls):
            return data
        if not data:
            return cls()
        if not hasattr(data, "get"):
            return cls()
        if "calibration" in data:
            data = data.get("calibration") or {}

        matrix = data.get("matrix_2x2", data.get("matrix"))
        if matrix is not None:
            matrix = cls._coerce_matrix(matrix)

        kx_per_um = data.get("kx_per_um")
        ky_per_um = data.get("ky_per_um")
        if matrix is not None:
            if kx_per_um is None:
                kx_per_um = matrix[0][0]
            if ky_per_um is None:
                ky_per_um = matrix[1][1]
        

        return cls(
            kx_per_um=0.0 if kx_per_um is None else kx_per_um,
            ky_per_um=0.0 if ky_per_um is None else ky_per_um,
            matrix_2x2=matrix,
            version=data.get("version", 1),
            created_at=data.get("created_at", data.get("date", "")),
            source=data.get("source", ""),
            metadata=data.get("metadata", {}),
            plane = data.get("plane",None),
            cam_px_size_um = data.get("cam_px_size_um")
        )

    def _effective_matrix(self):
        if self.matrix_2x2 is not None:
            return self.matrix_2x2
        return ((self.kx_per_um, 0.0), (0.0, self.ky_per_um))

    def _valid_matrix(self):
        matrix = self._effective_matrix()
        if matrix is None or not self.is_valid():
            raise ValueError("SLM section calibration is missing or invalid.")
        return matrix

    @staticmethod
    def _determinant(matrix):
        return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]

    @staticmethod
    def _coerce_matrix(matrix):
        if matrix is None:
            return None
        if len(matrix) != 2 or len(matrix[0]) != 2 or len(matrix[1]) != 2:
            raise ValueError("matrix_2x2 must be a 2x2 sequence.")
        return (
            (float(matrix[0][0]), float(matrix[0][1])),
            (float(matrix[1][0]), float(matrix[1][1])),
        )

    @staticmethod
    def _require_positive(value, name):
        value = float(value)
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError(f"{name} must be > 0.")
        return value

    @staticmethod
    def _require_nonzero(value, name):
        value = float(value)
        if not math.isfinite(value) or value == 0.0:
            raise ValueError(f"{name} must be non-zero.")
        return value

    @staticmethod
    def _coerce_optional_text(value):
        if value is None:
            return None
        text = str(value).strip()
        if text == "" or text.lower() == "none":
            return None
        return text

    @staticmethod
    def _coerce_optional_float(value):
        if value is None:
            return None
        text = str(value).strip()
        if text == "" or text.lower() == "none":
            return None
        return float(text)
    
