import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
from scipy import ndimage as ndi
from skimage import feature, filters, measure, transform


@dataclass
class FociAffineCalibration:
    matrix_xy: np.ndarray
    matrix_yx_napari: np.ndarray
    reference_points_xy: np.ndarray
    moving_points_xy: np.ndarray
    transformed_moving_points_xy: np.ndarray
    residuals_px: np.ndarray
    metadata: Dict[str, Any]


def detect_spot_centers(
    image,
    expected_n: Optional[int] = None,
    min_distance: int = 10,
    threshold_rel: float = 0.2,
    refine_radius: int = 5,
    gaussian_sigma: float = 1.0,
):
    """Detect bright foci centers and return them as Nx2 x/y coordinates."""
    img = _as_2d_float_image(image)

    p1, p99 = np.percentile(img, [1, 99.9])
    img_norm = (img - p1) / (p99 - p1 + 1e-12)
    img_norm = np.clip(img_norm, 0, 1)
    img_smooth = filters.gaussian(img_norm, sigma=float(gaussian_sigma))

    peak_kwargs = {
        "min_distance": int(min_distance),
        "threshold_rel": float(threshold_rel),
    }
    if expected_n is not None:
        peak_kwargs["num_peaks"] = int(expected_n)

    peaks_rc = feature.peak_local_max(img_smooth, **peak_kwargs)
    centers_xy = []

    for row, col in peaks_rc:
        r0 = max(0, int(row) - int(refine_radius))
        r1 = min(img.shape[0], int(row) + int(refine_radius) + 1)
        c0 = max(0, int(col) - int(refine_radius))
        c1 = min(img.shape[1], int(col) + int(refine_radius) + 1)

        patch = img_norm[r0:r1, c0:c1]
        patch_bg = np.percentile(patch, 10)
        patch = np.clip(patch - patch_bg, 0, None)

        if patch.sum() <= 0:
            centers_xy.append([float(col), float(row)])
            continue

        center_y, center_x = ndi.center_of_mass(patch)
        centers_xy.append([c0 + center_x, r0 + center_y])

    return np.asarray(centers_xy, dtype=float)


def order_grid_points(points_xy, n_rows: int, n_cols: int):
    """Order grid points row-major in x/y coordinates."""
    points_xy = np.asarray(points_xy, dtype=float)
    expected_n = int(n_rows) * int(n_cols)

    if points_xy.ndim != 2 or points_xy.shape[1] != 2:
        raise ValueError(f"Expected points with shape (N, 2), got {points_xy.shape}")
    if len(points_xy) != expected_n:
        raise ValueError(f"Expected {expected_n} points, got {len(points_xy)}")
    if expected_n == 0:
        return points_xy.copy()

    row_axis, col_axis = _estimate_grid_axes(points_xy, int(n_rows), int(n_cols))
    centered = points_xy - points_xy.mean(axis=0)
    row_coord = centered @ row_axis
    col_coord = centered @ col_axis

    row_sorted_indices = np.argsort(row_coord)
    rows = np.array_split(row_sorted_indices, int(n_rows))

    ordered = []
    for row_indices in rows:
        row_col_coord = col_coord[row_indices]
        ordered.append(points_xy[row_indices[np.argsort(row_col_coord)]])

    return np.vstack(ordered)


def estimate_affine_from_points(
    moving_points_xy,
    reference_points_xy,
    residual_threshold: float = 2.0,
):
    """Estimate an affine transform from moving x/y points to reference x/y points."""
    moving_points_xy = np.asarray(moving_points_xy, dtype=float)
    reference_points_xy = np.asarray(reference_points_xy, dtype=float)

    if moving_points_xy.shape != reference_points_xy.shape:
        raise ValueError(
            "moving_points_xy and reference_points_xy must have the same shape, "
            f"got {moving_points_xy.shape} and {reference_points_xy.shape}"
        )
    if moving_points_xy.ndim != 2 or moving_points_xy.shape[1] != 2:
        raise ValueError(f"Expected point arrays with shape (N, 2), got {moving_points_xy.shape}")
    if len(moving_points_xy) < 3:
        raise ValueError("At least 3 point pairs are required for affine estimation")

    try:
        model, inliers = measure.ransac(
            (moving_points_xy, reference_points_xy),
            transform.AffineTransform,
            min_samples=3,
            residual_threshold=float(residual_threshold),
            max_trials=500,
        )
    except ValueError:
        model = transform.AffineTransform()
        if not model.estimate(moving_points_xy, reference_points_xy):
            raise ValueError("Could not estimate affine transform")
        inliers = np.ones(len(moving_points_xy), dtype=bool)

    if model is None:
        raise ValueError("Could not estimate affine transform")

    transformed_moving_points_xy = model(moving_points_xy)
    residuals_px = np.linalg.norm(
        transformed_moving_points_xy - reference_points_xy,
        axis=1,
    )

    if inliers is None:
        inliers = np.ones(len(moving_points_xy), dtype=bool)

    return model.params, transformed_moving_points_xy, residuals_px, np.asarray(inliers, dtype=bool)


def calibrate_foci_affine(
    reference_image,
    moving_image,
    n_rows: int,
    n_cols: int,
    detection_params: Optional[Dict[str, Any]] = None,
    residual_threshold: float = 2.0,
):
    detection_params = dict(detection_params or {})
    expected_n = int(n_rows) * int(n_cols)

    reference_image = _as_2d_float_image(reference_image)
    moving_image = _as_2d_float_image(moving_image)

    reference_points_xy = detect_spot_centers(
        reference_image,
        expected_n=expected_n,
        **detection_params,
    )
    moving_points_xy = detect_spot_centers(
        moving_image,
        expected_n=expected_n,
        **detection_params,
    )

    reference_points_xy = order_grid_points(reference_points_xy, n_rows, n_cols)
    moving_points_xy = order_grid_points(moving_points_xy, n_rows, n_cols)

    matrix_xy, transformed_moving_points_xy, residuals_px, inliers = estimate_affine_from_points(
        moving_points_xy=moving_points_xy,
        reference_points_xy=reference_points_xy,
        residual_threshold=residual_threshold,
    )
    matrix_yx_napari = xy_affine_to_napari_yx(matrix_xy)

    metadata = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "transform_direction": "moving_to_reference",
        "reference_image_shape": list(reference_image.shape),
        "moving_image_shape": list(moving_image.shape),
        "n_rows": int(n_rows),
        "n_cols": int(n_cols),
        "n_points": int(len(reference_points_xy)),
        "n_inliers": int(np.sum(inliers)),
        "mean_residual_px": float(np.mean(residuals_px)),
        "median_residual_px": float(np.median(residuals_px)),
        "max_residual_px": float(np.max(residuals_px)),
        "detection_params": detection_params,
        "residual_threshold": float(residual_threshold),
        "file_format_version": 1,
    }

    return FociAffineCalibration(
        matrix_xy=np.asarray(matrix_xy, dtype=float),
        matrix_yx_napari=np.asarray(matrix_yx_napari, dtype=float),
        reference_points_xy=reference_points_xy,
        moving_points_xy=moving_points_xy,
        transformed_moving_points_xy=transformed_moving_points_xy,
        residuals_px=residuals_px,
        metadata=metadata,
    )


def xy_affine_to_napari_yx(H_xy):
    """Convert homogeneous x/y affine coordinates to napari y/x data coordinates."""
    H_xy = _as_homogeneous_affine(H_xy)
    swap = np.array(
        [
            [0, 1, 0],
            [1, 0, 0],
            [0, 0, 1],
        ],
        dtype=float,
    )
    return swap @ H_xy @ swap


def pixel_affine_to_napari_world_affine(H_px_yx, layer_scale):
    """Convert a pixel-space y/x affine to the world-space affine napari stores."""
    H_px_yx = _as_homogeneous_affine(H_px_yx)
    scale = np.asarray(layer_scale if layer_scale is not None else [1, 1], dtype=float).ravel()

    if scale.size < 2:
        scale = np.ones(2, dtype=float)
    else:
        scale = scale[-2:]

    S = np.array(
        [
            [scale[0], 0, 0],
            [0, scale[1], 0],
            [0, 0, 1],
        ],
        dtype=float,
    )

    return S @ H_px_yx @ np.linalg.inv(S)


def save_calibration(path, calibration: FociAffineCalibration):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    np.savez_compressed(
        path,
        matrix_xy=np.asarray(calibration.matrix_xy, dtype=float),
        matrix_yx_napari=np.asarray(calibration.matrix_yx_napari, dtype=float),
        reference_points_xy=np.asarray(calibration.reference_points_xy, dtype=float),
        moving_points_xy=np.asarray(calibration.moving_points_xy, dtype=float),
        transformed_moving_points_xy=np.asarray(
            calibration.transformed_moving_points_xy,
            dtype=float,
        ),
        residuals_px=np.asarray(calibration.residuals_px, dtype=float),
        metadata_json=json.dumps(calibration.metadata, indent=2, sort_keys=True),
    )


def load_calibration(path):
    with np.load(path, allow_pickle=False) as data:
        metadata_raw = data["metadata_json"]
        if hasattr(metadata_raw, "item"):
            metadata_raw = metadata_raw.item()
        metadata = json.loads(str(metadata_raw))

        return FociAffineCalibration(
            matrix_xy=np.asarray(data["matrix_xy"], dtype=float),
            matrix_yx_napari=np.asarray(data["matrix_yx_napari"], dtype=float),
            reference_points_xy=np.asarray(data["reference_points_xy"], dtype=float),
            moving_points_xy=np.asarray(data["moving_points_xy"], dtype=float),
            transformed_moving_points_xy=np.asarray(
                data["transformed_moving_points_xy"],
                dtype=float,
            ),
            residuals_px=np.asarray(data["residuals_px"], dtype=float),
            metadata=metadata,
        )


def _as_2d_float_image(image):
    image = np.asarray(image)
    image = np.squeeze(image)

    if image.ndim != 2:
        raise ValueError(f"Expected a 2D image, got shape {image.shape}")

    return image.astype(float, copy=False)


def _as_homogeneous_affine(affine):
    affine = np.asarray(affine, dtype=float)

    if affine.shape == (2, 3):
        H = np.eye(3, dtype=float)
        H[:2, :] = affine
        return H
    if affine.shape == (3, 3):
        return affine

    raise ValueError(f"Expected affine shape (3, 3) or (2, 3), got {affine.shape}")


def _estimate_grid_axes(points_xy, n_rows: int, n_cols: int) -> Tuple[np.ndarray, np.ndarray]:
    centered = points_xy - points_xy.mean(axis=0)
    _, _, vh = np.linalg.svd(centered, full_matrices=False)
    axis0 = vh[0]
    axis1 = vh[1]

    if n_cols == n_rows:
        col_axis, row_axis = (axis0, axis1) if abs(axis0[0]) >= abs(axis1[0]) else (axis1, axis0)
    elif n_cols > n_rows:
        col_axis, row_axis = axis0, axis1
    else:
        row_axis, col_axis = axis0, axis1

    if col_axis[0] < 0:
        col_axis = -col_axis
    if row_axis[1] < 0:
        row_axis = -row_axis

    return row_axis, col_axis
