"""File helpers for SLM plane definitions and per-plane calibrations."""

import json
import os
import re
from datetime import datetime

from .slmSectionCalibration import SLMSectionCalibration


PLANE_DEFINITIONS_FILENAME = "planes.json"
PLANE_STORE_VERSION = 1
CALIBRATION_STORE_VERSION = 1


def empty_plane_definitions():
    return {"version": PLANE_STORE_VERSION, "planes": {}}


def plane_slug(plane_name):
    text = str(plane_name or "").strip().lower()
    text = re.sub(r"[^0-9a-z_ -]", "", text)
    text = re.sub(r"[\s-]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    if not text:
        raise ValueError("Plane name must contain at least one letter or number.")
    return text


def plane_definitions_path(calibration_dir):
    return os.path.join(calibration_dir, PLANE_DEFINITIONS_FILENAME)


def normalize_plane_definition(definition):
    if not isinstance(definition, dict):
        raise ValueError("Plane definition must be a dictionary.")

    name = str(definition.get("name", "")).strip()
    detector_name = str(definition.get("detector_name", "")).strip()
    description = str(definition.get("description", "") or "").strip()

    if not name:
        raise ValueError("Plane name is required.")
    if not detector_name:
        raise ValueError("Detector name is required.")

    try:
        detector_pixel_size_um = float(definition.get("detector_pixel_size_um"))
    except Exception:
        raise ValueError("Detector pixel size must be a number.")
    if detector_pixel_size_um <= 0.0:
        raise ValueError("Detector pixel size must be > 0.")

    created_at = str(definition.get("created_at") or datetime.now().isoformat())

    return {
        "name": name,
        "detector_name": detector_name,
        "detector_pixel_size_um": detector_pixel_size_um,
        "description": description,
        "created_at": created_at,
    }


def load_plane_definitions(calibration_dir):
    path = plane_definitions_path(calibration_dir)
    if not os.path.isfile(path):
        return empty_plane_definitions()

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    planes = data.get("planes", {}) if isinstance(data, dict) else {}
    if not isinstance(planes, dict):
        raise ValueError("Plane definitions file must contain a 'planes' object.")

    normalized = {}
    seen_slugs = {}
    for key, definition in planes.items():
        definition = dict(definition or {})
        definition.setdefault("name", key)
        plane = normalize_plane_definition(definition)
        slug = plane_slug(plane["name"])
        if slug in seen_slugs:
            raise ValueError(
                f'Plane "{plane["name"]}" conflicts with "{seen_slugs[slug]}".'
            )
        seen_slugs[slug] = plane["name"]
        normalized[plane["name"]] = plane

    return {"version": PLANE_STORE_VERSION, "planes": normalized}


def save_plane_definitions(calibration_dir, definitions):
    path = plane_definitions_path(calibration_dir)
    _write_json(path, definitions)


def add_plane_definition(definitions, definition):
    data = {
        "version": PLANE_STORE_VERSION,
        "planes": dict((definitions or {}).get("planes", {}) or {}),
    }
    plane = normalize_plane_definition(definition)
    name = plane["name"]
    slug = plane_slug(name)

    if name in data["planes"]:
        raise ValueError(f'Plane "{name}" already exists.')

    for existing_name in data["planes"]:
        if plane_slug(existing_name) == slug:
            raise ValueError(
                f'Plane "{name}" conflicts with existing plane "{existing_name}".'
            )

    data["planes"][name] = plane
    return data


def remove_plane_definition(definitions, plane_name):
    name = str(plane_name or "").strip()
    data = {
        "version": PLANE_STORE_VERSION,
        "planes": dict((definitions or {}).get("planes", {}) or {}),
    }
    if name not in data["planes"]:
        raise KeyError(f'Plane "{name}" does not exist.')

    del data["planes"][name]
    return data


def calibration_file_path(calibration_dir, slm_serial, sec_key, plane_name):
    return os.path.join(
        calibration_dir,
        str(slm_serial),
        str(sec_key),
        f"{plane_slug(plane_name)}.json",
    )


def save_section_calibration(
    calibration_dir,
    slm_name,
    slm_serial,
    sec_key,
    plane_name,
    calibration,
):
    calibration = SLMSectionCalibration.from_dict(calibration)
    if not calibration.created_at:
        calibration.created_at = datetime.now().isoformat()
    path = calibration_file_path(calibration_dir, slm_serial, sec_key, plane_name)
    payload = {
        "version": CALIBRATION_STORE_VERSION,
        "slm_name": str(slm_name),
        "slm_serial": str(slm_serial),
        "section": str(sec_key),
        "plane_name": str(plane_name),
        "created_at": calibration.created_at,
        "calibration": calibration.to_dict(),
    }
    _write_json(path, payload)
    return path


def load_section_calibration(calibration_dir, slm_serial, sec_key, plane_name):
    path = calibration_file_path(calibration_dir, slm_serial, sec_key, plane_name)
    if not os.path.isfile(path):
        return SLMSectionCalibration()

    with open(path, "r", encoding="utf-8") as file:
        payload = json.load(file)
    return SLMSectionCalibration.from_dict(payload)


def delete_plane_calibration_files(calibration_dir, plane_name):
    filename = f"{plane_slug(plane_name)}.json"
    deleted = []
    if not os.path.isdir(calibration_dir):
        return deleted

    for root, _dirs, files in os.walk(calibration_dir):
        rel_root = os.path.relpath(root, calibration_dir)
        if rel_root == "." or len(rel_root.split(os.sep)) < 2:
            continue
        if filename not in files:
            continue

        path = os.path.join(root, filename)
        os.remove(path)
        deleted.append(path)

    return deleted


def get_default_active_planes(manager_properties):
    defaults = (manager_properties or {}).get("defaultActivePlanes")
    if isinstance(defaults, dict):
        return defaults
    return {}


def set_default_active_plane(manager_properties, sec_key, plane_name):
    manager_properties.pop("sectionCalibrations", None)

    defaults = manager_properties.get("defaultActivePlanes")
    if not isinstance(defaults, dict):
        defaults = {}

    plane_name = str(plane_name).strip() if plane_name else None
    if plane_name:
        defaults[str(sec_key)] = plane_name
    else:
        defaults.pop(str(sec_key), None)

    if defaults:
        manager_properties["defaultActivePlanes"] = defaults
    else:
        manager_properties.pop("defaultActivePlanes", None)

    return manager_properties


def clear_default_active_plane_name(manager_properties, plane_name):
    manager_properties.pop("sectionCalibrations", None)

    defaults = manager_properties.get("defaultActivePlanes")
    if not isinstance(defaults, dict):
        manager_properties.pop("defaultActivePlanes", None)
        return manager_properties

    plane_name = str(plane_name or "").strip()
    for sec_key, active_plane in list(defaults.items()):
        if active_plane == plane_name:
            defaults.pop(sec_key, None)

    if defaults:
        manager_properties["defaultActivePlanes"] = defaults
    else:
        manager_properties.pop("defaultActivePlanes", None)

    return manager_properties


def _write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, sort_keys=True)
        file.write("\n")
    os.replace(tmp_path, path)
