import os
import importlib.util
import sys
import types
from pathlib import Path

import pytest


def load_slm_plane_modules():
    package_name = "slm_plane_calibration_test_pkg"
    package_module = types.ModuleType(package_name)
    package_module.__path__ = []
    sys.modules[package_name] = package_module

    module_dir = (
        Path(__file__).resolve().parents[2]
        / "controller"
        / "patterndesigners"
    )

    section_spec = importlib.util.spec_from_file_location(
        f"{package_name}.slmSectionCalibration",
        module_dir / "slmSectionCalibration.py",
    )
    section_module = importlib.util.module_from_spec(section_spec)
    sys.modules[section_spec.name] = section_module
    section_spec.loader.exec_module(section_module)

    plane_spec = importlib.util.spec_from_file_location(
        f"{package_name}.slmPlaneCalibration",
        module_dir / "slmPlaneCalibration.py",
    )
    plane_module = importlib.util.module_from_spec(plane_spec)
    sys.modules[plane_spec.name] = plane_module
    plane_spec.loader.exec_module(plane_module)

    return plane_module, section_module.SLMSectionCalibration


plane_module, SLMSectionCalibration = load_slm_plane_modules()
add_plane_definition = plane_module.add_plane_definition
calibration_file_path = plane_module.calibration_file_path
clear_default_active_plane_name = plane_module.clear_default_active_plane_name
delete_plane_calibration_files = plane_module.delete_plane_calibration_files
empty_plane_definitions = plane_module.empty_plane_definitions
load_plane_definitions = plane_module.load_plane_definitions
load_section_calibration = plane_module.load_section_calibration
plane_slug = plane_module.plane_slug
remove_plane_definition = plane_module.remove_plane_definition
save_plane_definitions = plane_module.save_plane_definitions
save_section_calibration = plane_module.save_section_calibration
set_default_active_plane = plane_module.set_default_active_plane


def test_plane_definitions_roundtrip_and_duplicate_slug(tmp_path):
    definitions = add_plane_definition(
        empty_plane_definitions(),
        {
            "name": "Sample Plane",
            "detector_name": "Widefield",
            "detector_pixel_size_um": 0.077,
            "description": "main imaging plane",
        },
    )

    save_plane_definitions(tmp_path, definitions)
    loaded = load_plane_definitions(tmp_path)

    assert list(loaded["planes"]) == ["Sample Plane"]
    assert loaded["planes"]["Sample Plane"]["detector_name"] == "Widefield"
    assert loaded["planes"]["Sample Plane"]["detector_pixel_size_um"] == 0.077
    assert plane_slug("Sample Plane") == "sample_plane"

    with pytest.raises(ValueError, match="conflicts"):
        add_plane_definition(
            loaded,
            {
                "name": "Sample-Plane",
                "detector_name": "Other",
                "detector_pixel_size_um": 1.0,
            },
        )


def test_section_calibration_file_roundtrip(tmp_path):
    calibration = SLMSectionCalibration(
        kx_per_um=0.01,
        ky_per_um=0.02,
        plane="Sample Plane",
        cam_px_size_um=0.077,
    )

    path = save_section_calibration(
        tmp_path,
        slm_name="slm",
        slm_serial="SER123",
        sec_key="sec_0",
        plane_name="Sample Plane",
        calibration=calibration,
    )

    assert path == os.path.join(tmp_path, "SER123", "sec_0", "sample_plane.json")
    assert calibration_file_path(tmp_path, "SER123", "sec_0", "Sample Plane") == path

    loaded = load_section_calibration(tmp_path, "SER123", "sec_0", "Sample Plane")

    assert loaded.is_valid()
    assert loaded.plane == "Sample Plane"
    assert loaded.cam_px_size_um == 0.077
    assert loaded.kx_per_um == 0.01
    assert loaded.ky_per_um == 0.02


def test_delete_plane_removes_matching_files_and_definition(tmp_path):
    definitions = empty_plane_definitions()
    definitions = add_plane_definition(
        definitions,
        {
            "name": "Sample Plane",
            "detector_name": "Widefield",
            "detector_pixel_size_um": 0.077,
        },
    )
    definitions = add_plane_definition(
        definitions,
        {
            "name": "Other Plane",
            "detector_name": "Widefield",
            "detector_pixel_size_um": 0.077,
        },
    )

    calibration = SLMSectionCalibration(kx_per_um=0.01, ky_per_um=0.02)
    sample_path = save_section_calibration(
        tmp_path, "slm", "SER123", "sec_0", "Sample Plane", calibration
    )
    other_path = save_section_calibration(
        tmp_path, "slm", "SER123", "sec_0", "Other Plane", calibration
    )

    definitions = remove_plane_definition(definitions, "Sample Plane")
    deleted = delete_plane_calibration_files(tmp_path, "Sample Plane")

    assert "Sample Plane" not in definitions["planes"]
    assert deleted == [sample_path]
    assert not os.path.exists(sample_path)
    assert os.path.exists(other_path)


def test_default_active_plane_helpers_drop_old_calibration_values():
    manager_properties = {
        "sectionCalibrations": {"sec_0": {"calibration": {"kx_per_um": 1}}},
        "defaultActivePlanes": {"sec_0": "Sample Plane", "sec_1": "Other Plane"},
    }

    set_default_active_plane(manager_properties, "sec_2", "Sample Plane")

    assert "sectionCalibrations" not in manager_properties
    assert manager_properties["defaultActivePlanes"]["sec_2"] == "Sample Plane"

    clear_default_active_plane_name(manager_properties, "Sample Plane")

    assert manager_properties["defaultActivePlanes"] == {"sec_1": "Other Plane"}
