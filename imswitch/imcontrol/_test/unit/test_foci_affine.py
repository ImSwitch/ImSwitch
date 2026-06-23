import numpy as np
import pytest

from imswitch.imcontrol.model.foci_affine import (
    FociAffineCalibration,
    calibrate_foci_affine,
    order_grid_points,
    pixel_affine_to_napari_world_affine,
    save_calibration,
    load_calibration,
    xy_affine_to_napari_yx,
)


def test_xy_affine_to_napari_yx_swaps_coordinate_order():
    H_xy = np.array(
        [
            [1, 0, 5],
            [0, 1, 7],
            [0, 0, 1],
        ],
        dtype=float,
    )

    H_yx = xy_affine_to_napari_yx(H_xy)

    np.testing.assert_allclose(
        H_yx,
        np.array(
            [
                [1, 0, 7],
                [0, 1, 5],
                [0, 0, 1],
            ],
            dtype=float,
        ),
    )


def test_pixel_affine_to_napari_world_affine_scales_translation():
    H_px_yx = np.array(
        [
            [1, 0, 2],
            [0, 1, 3],
            [0, 0, 1],
        ],
        dtype=float,
    )

    H_world = pixel_affine_to_napari_world_affine(H_px_yx, [0.5, 2.0])

    np.testing.assert_allclose(
        H_world,
        np.array(
            [
                [1, 0, 1],
                [0, 1, 6],
                [0, 0, 1],
            ],
            dtype=float,
        ),
    )


def test_save_load_calibration_roundtrip(tmp_path):
    calibration = FociAffineCalibration(
        matrix_xy=np.array([[1.0, 0.1, 2.0], [0.0, 0.9, 3.0], [0.0, 0.0, 1.0]]),
        matrix_yx_napari=np.array([[0.9, 0.0, 3.0], [0.1, 1.0, 2.0], [0.0, 0.0, 1.0]]),
        reference_points_xy=np.array([[1.0, 2.0], [3.0, 4.0]]),
        moving_points_xy=np.array([[5.0, 6.0], [7.0, 8.0]]),
        transformed_moving_points_xy=np.array([[1.1, 2.1], [3.1, 4.1]]),
        residuals_px=np.array([0.1, 0.2]),
        metadata={"transform_direction": "moving_to_reference", "n_points": 2},
    )
    path = tmp_path / "calibration.npz"

    save_calibration(path, calibration)
    loaded = load_calibration(path)

    np.testing.assert_allclose(loaded.matrix_xy, calibration.matrix_xy)
    np.testing.assert_allclose(loaded.matrix_yx_napari, calibration.matrix_yx_napari)
    np.testing.assert_allclose(loaded.reference_points_xy, calibration.reference_points_xy)
    np.testing.assert_allclose(loaded.moving_points_xy, calibration.moving_points_xy)
    np.testing.assert_allclose(
        loaded.transformed_moving_points_xy,
        calibration.transformed_moving_points_xy,
    )
    np.testing.assert_allclose(loaded.residuals_px, calibration.residuals_px)
    assert loaded.metadata == calibration.metadata


def test_order_grid_points_rejects_wrong_count():
    points_xy = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]])

    with pytest.raises(ValueError, match="Expected 4 points"):
        order_grid_points(points_xy, n_rows=2, n_cols=2)


def test_calibrate_foci_affine_synthetic_grid():
    n_rows = 4
    n_cols = 5
    moving_points_xy = _grid_points(n_rows=n_rows, n_cols=n_cols)
    matrix_xy = np.array(
        [
            [1.02, 0.04, 3.5],
            [-0.03, 0.98, 5.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=float,
    )
    reference_points_xy = _apply_homogeneous(moving_points_xy, matrix_xy)

    calibration = calibrate_foci_affine(
        reference_image=_render_spots(reference_points_xy),
        moving_image=_render_spots(moving_points_xy),
        n_rows=n_rows,
        n_cols=n_cols,
        detection_params={
            "min_distance": 8,
            "threshold_rel": 0.2,
            "refine_radius": 4,
            "gaussian_sigma": 1.0,
        },
        residual_threshold=2.0,
    )

    np.testing.assert_allclose(calibration.matrix_xy, matrix_xy, atol=1e-2)
    assert calibration.metadata["n_points"] == n_rows * n_cols
    assert calibration.metadata["n_inliers"] == n_rows * n_cols
    assert calibration.metadata["mean_residual_px"] < 0.02


def _grid_points(n_rows, n_cols):
    cols = np.arange(20, 20 + n_cols * 15, 15)
    rows = np.arange(25, 25 + n_rows * 16, 16)
    xx, yy = np.meshgrid(cols, rows)
    return np.column_stack([xx.ravel(), yy.ravel()]).astype(float)


def _apply_homogeneous(points_xy, matrix_xy):
    points_h = np.column_stack([points_xy, np.ones(len(points_xy))])
    transformed_h = points_h @ matrix_xy.T
    return transformed_h[:, :2] / transformed_h[:, 2:3]


def _render_spots(points_xy, shape=(128, 128), sigma=1.2):
    yy, xx = np.indices(shape)
    image = np.zeros(shape, dtype=float)

    for x, y in points_xy:
        image += np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * sigma ** 2))

    return image
