#!/usr/bin/env python3
"""
ImSwitch Config Studio
Visual editor for ImSwitch JSON configuration files.

Run:      python tools/imswitch_config_editor.py [/path/to/config/dir]
Requires: pip install PyQt5
"""

import colorsys
import copy
import json
import os
import sys
from pathlib import Path
import glob
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog,
    QFormLayout, QFrame, QHBoxLayout, QInputDialog, QLabel, QLineEdit,
    QMainWindow, QMenu, QMessageBox, QPushButton, QScrollArea, QSizePolicy,
    QSpinBox, QSplitter, QStatusBar, QTabWidget, QToolBar, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget, QAction, QGridLayout, QDialog, QTextEdit,
)

# =============================================================================
# Schema loading – reads builtin_templates/{category}/*.json at startup
# =============================================================================
def _load_schemas() -> dict:
    """Load all built-in manager schemas from builtin_templates/ subdirectories."""
    schemas: dict = {}
    base = Path(__file__).resolve().parent / "builtin_templates"
    if base.is_dir():
        for cat_dir in sorted(base.iterdir()):
            if not cat_dir.is_dir():
                continue
            for f in sorted(cat_dir.glob("*.json")):
                try:
                    with open(f, encoding="utf-8") as fh:
                        schemas[f.stem] = json.load(fh)
                except Exception:
                    pass
    return schemas


def _hsv_palette(n: int, saturation: float = 0.60, value: float = 0.78) -> list:
    """Return n evenly-spaced HSV hex colours, offset slightly from pure red."""
    out = []
    for i in range(max(n, 1)):
        h = (i / max(n, 1) + 0.05) % 1.0
        r, g, b = colorsys.hsv_to_rgb(h, saturation, value)
        out.append("#{:02X}{:02X}{:02X}".format(int(r * 255), int(g * 255), int(b * 255)))
    return out


_LABEL_OVERRIDES = {
    "rs232devices": "RS232 Devices",
    "slms": "SLMs",
}


def _build_cat_palette(schemas: dict) -> tuple:
    """Derive (CAT_COLOR, CAT_LABEL) from the categories found in schemas."""
    cats: list = []
    seen: set = set()
    for s in schemas.values():
        cat = s.get("category", "")
        if cat and cat not in seen:
            cats.append(cat)
            seen.add(cat)
    cats.sort()
    colours = _hsv_palette(len(cats))
    cat_color = {cat: colours[i] for i, cat in enumerate(cats)}
    cat_label: dict = {}
    for cat in cats:
        words = cat.replace("_", " ").split()
        label = " ".join(w.capitalize() for w in words)
        cat_label[cat] = _LABEL_OVERRIDES.get(cat, label)
    return cat_color, cat_label


# =============================================================================
# Palette & schema registry (derived from JSON files at import time)
# Field helper: (key, label, type, default, required, group, tooltip, options)
# Types: text | int | float | bool | select | path
# =============================================================================
def _f(key, label, tp="text", default="", req=False,
       grp="Basic", tip="", opts=None):
    return dict(key=key, label=label, type=tp, default=default,
                req=req, grp=grp, tip=tip, opts=opts or [])


SCHEMAS = _load_schemas()
CAT_COLOR, CAT_LABEL = _build_cat_palette(SCHEMAS)
DEVICE_CATS = sorted({s["category"] for s in SCHEMAS.values() if s.get("category")})
# "others" is a permanent catch-all — always last, never stored in schemas
if "others" not in DEVICE_CATS:
    DEVICE_CATS = DEVICE_CATS + ["others"]
CAT_COLOR.setdefault("others", "#888888")
CAT_LABEL.setdefault("others", "Others")


# Build category → [manager names] index
CAT_MANAGERS: dict = {}
for _m, _s in SCHEMAS.items():
    CAT_MANAGERS.setdefault(_s["category"], []).append(_m)
for _lst in CAT_MANAGERS.values():
    _lst.sort()


# =============================================================================
# Helpers for reading / writing device data
# =============================================================================
def _json_to_display(value, field_type: str) -> str:
    """Convert a JSON value to a display string for a text/select widget."""
    if value is None:
        return "null"
    if field_type in ("int", "float"):
        return str(value)
    return str(value)


def _display_to_json(text: str, field_type: str):
    """Convert a display string back to the correct Python type."""
    text = text.strip()
    if text.lower() == "null":
        return None
    if field_type == "int":
        try:
            return int(text)
        except ValueError:
            return text
    if field_type == "float":
        try:
            return float(text)
        except ValueError:
            return text
    return text


def _build_default_device(manager_name: str) -> dict:
    """Return a new device dict pre-filled with schema defaults."""
    schema = SCHEMAS.get(manager_name, {})
    d: dict = {"managerName": manager_name, "managerProperties": {}}
    for f in schema.get("top", []):
        v = f["default"]
        if f["type"] == "bool" and isinstance(v, bool):
            d[f["key"]] = v
        elif v == "null":
            d[f["key"]] = None
        else:
            d[f["key"]] = _display_to_json(str(v), f["type"]) if v != "" else v
    for f in schema.get("props", []):
        v = f["default"]
        d["managerProperties"][f["key"]] = (
            _display_to_json(str(v), f["type"]) if v != "" else v
        )
    for nest_key, nest_fields in schema.get("nested", {}).items():
        sub = {}
        for f in nest_fields:
            v = f["default"]
            sub[f["key"]] = _display_to_json(str(v), f["type"]) if v != "" else v
        d["managerProperties"][nest_key] = sub
    return d


def _collect_daq_channels(data: dict) -> dict:
    """Return {channel_string: [device_name, ...]} for all assigned DAQ lines."""
    used: dict = {}
    for cat in DEVICE_CATS:
        for name, dev in (data.get(cat) or {}).items():
            for key in ("analogChannel", "digitalLine"):
                val = dev.get(key)
                if val and val != "null":
                    used.setdefault(val, []).append(name)
    return used


# =============================================================================
# DeviceCard
# =============================================================================
class DeviceCard(QFrame):
    """Compact coloured card for one device."""

    # Emitted to the canvas; canvas passes signals up to MainWindow
    sig_clicked   = pyqtSignal(str, str)   # (category, name)
    sig_duplicate = pyqtSignal(str, str)
    sig_rename    = pyqtSignal(str, str)
    sig_delete    = pyqtSignal(str, str)
    sig_save_tmpl = pyqtSignal(str, str)

    def __init__(self, category: str, name: str, device_data: dict, parent=None):
        super().__init__(parent)
        self.category = category
        self.device_name = name
        self.device_data = device_data
        self._selected = False
        self._init_ui()

    def _init_ui(self):
        self.setFixedWidth(195)
        self.setMinimumHeight(80)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.setCursor(Qt.PointingHandCursor)
        self._apply_style(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 7, 7, 7)
        layout.setSpacing(2)

        self._name_lbl = QLabel(self.device_name)
        bold = QFont()
        bold.setBold(True)
        bold.setPointSize(9)
        self._name_lbl.setFont(bold)
        self._name_lbl.setWordWrap(True)
        layout.addWidget(self._name_lbl)

        mgr = self.device_data.get("managerName", "")
        short_mgr = mgr.replace("Manager", "").replace("LaserManager", "")
        schema = SCHEMAS.get(mgr, {})
        self._mgr_lbl = QLabel(schema.get("display", short_mgr))
        self._mgr_lbl.setStyleSheet("color:#666;font-size:8pt;")
        layout.addWidget(self._mgr_lbl)

        info = self._summary()
        if info:
            lbl = QLabel(info)
            lbl.setStyleSheet("color:#888;font-size:8pt;")
            lbl.setWordWrap(True)
            layout.addWidget(lbl)

        layout.addStretch()

    def _summary(self) -> str:
        d = self.device_data
        props = d.get("managerProperties") or {}
        _skip = {"managerName", "managerProperties", "forAcquisition",
                 "forFocusLock", "forPositioning", "forScanning"}
        parts = []
        for k, v in d.items():
            if k in _skip or v is None or v == "null" or v == "" or isinstance(v, (dict, list, bool)):
                continue
            parts.append(f"{k}: {v}")
            if len(parts) >= 2:
                break
        for k, v in props.items():
            if v is None or v == "" or isinstance(v, (dict, list)):
                continue
            parts.append(f"{k}: {v}")
            if len(parts) >= 3:
                break
        return "  ·  ".join(parts[:3])

    def _apply_style(self, selected: bool):
        color = CAT_COLOR.get(self.category, "#888")
        bw = "5px" if selected else "3px"
        bg = "#EEF4FF" if selected else "#F8F8F8"
        self.setStyleSheet(f"""
            DeviceCard {{
                background: {bg};
                border: 1px solid #DDD;
                border-left: {bw} solid {color};
                border-radius: 4px;
            }}
            DeviceCard:hover {{
                background: #EFF6FF;
                border-left: 5px solid {color};
            }}
        """)

    def set_selected(self, selected: bool):
        self._selected = selected
        self._apply_style(selected)

    def refresh(self):
        self._name_lbl.setText(self.device_name)
        self._init_ui()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.sig_clicked.emit(self.category, self.device_name)
        super().mousePressEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        a_dup  = menu.addAction("Duplicate")
        a_ren  = menu.addAction("Rename…")
        menu.addSeparator()
        a_tmpl = menu.addAction("Save as Template")
        menu.addSeparator()
        a_del  = menu.addAction("Delete")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == a_dup:
            self.sig_duplicate.emit(self.category, self.device_name)
        elif action == a_ren:
            self.sig_rename.emit(self.category, self.device_name)
        elif action == a_tmpl:
            self.sig_save_tmpl.emit(self.category, self.device_name)
        elif action == a_del:
            self.sig_delete.emit(self.category, self.device_name)


# =============================================================================
# DeviceCanvas – scrollable grid of cards grouped by category
# =============================================================================
class DeviceCanvas(QScrollArea):
    sig_device_selected = pyqtSignal(str, str)
    sig_device_deleted  = pyqtSignal(str, str)
    sig_device_duped    = pyqtSignal(str, str)
    sig_device_renamed  = pyqtSignal(str, str)
    sig_save_tmpl       = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(12, 12, 12, 12)
        self._layout.setSpacing(18)
        self.setWidget(self._container)
        self._cards: dict[tuple, DeviceCard] = {}   # (cat, name) → card
        self._selected: object = None
        self._section_grids: dict[str, QGridLayout] = {}

    def load(self, data: dict):
        self._clear()
        for cat in DEVICE_CATS:
            devices = data.get(cat) or {}
            if not devices and cat != "others":
                continue
            self._add_section(cat, devices, data)
        self._layout.addStretch()

    def _clear(self):
        self._cards.clear()
        self._selected = None
        self._section_grids.clear()
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _add_section(self, cat: str, devices: dict, data: dict):
        color = CAT_COLOR[cat]
        label_text = CAT_LABEL[cat]

        # Section header
        header = QWidget()
        hlay = QHBoxLayout(header)
        hlay.setContentsMargins(0, 0, 0, 4)

        dot = QLabel("●")
        dot.setStyleSheet(f"color:{color}; font-size:14px;")
        hlay.addWidget(dot)

        lbl = QLabel(f"<b>{label_text}</b>  <span style='color:#999;font-size:9pt;'>"
                     f"({len(devices)} device{'s' if len(devices)!=1 else ''})</span>")
        lbl.setTextFormat(Qt.RichText)
        hlay.addWidget(lbl)
        hlay.addStretch()

        add_btn = QPushButton("＋ Add")
        add_btn.setFixedHeight(22)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {color}22; border: 1px solid {color}66;
                border-radius: 3px; color: {color}; font-size: 9pt;
                padding: 0 8px;
            }}
            QPushButton:hover {{ background: {color}44; }}
        """)
        add_btn.clicked.connect(lambda _, c=cat: self._request_add(c))
        hlay.addWidget(add_btn)
        self._layout.addWidget(header)

        # Grid of cards
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(8)
        self._section_grids[cat] = grid

        col, row = 0, 0
        cols = 4
        for name, dev_data in devices.items():
            card = DeviceCard(cat, name, dev_data)
            card.sig_clicked.connect(self._on_card_clicked)
            card.sig_duplicate.connect(self.sig_device_duped)
            card.sig_rename.connect(self.sig_device_renamed)
            card.sig_delete.connect(self.sig_device_deleted)
            card.sig_save_tmpl.connect(self.sig_save_tmpl)
            grid.addWidget(card, row, col)
            self._cards[(cat, name)] = card
            col += 1
            if col >= cols:
                col = 0
                row += 1

        self._layout.addWidget(grid_widget)

    def _on_card_clicked(self, cat: str, name: str):
        if self._selected:
            old = self._cards.get(self._selected)
            if old:
                old.set_selected(False)
        self._selected = (cat, name)
        card = self._cards.get((cat, name))
        if card:
            card.set_selected(True)
        self.sig_device_selected.emit(cat, name)

    def _request_add(self, cat: str):
        if cat == "others":
            choices = ["[Free-form / Custom]"] + sorted(SCHEMAS.keys())
        else:
            choices = CAT_MANAGERS.get(cat, [])
        if not choices:
            return
        mgr, ok = QInputDialog.getItem(
            self, f"Add {CAT_LABEL[cat]}", "Select manager type:", choices, 0, False
        )
        if not ok:
            return
        name, ok2 = QInputDialog.getText(
            self, "Device Name", f"Name for new {CAT_LABEL[cat]} device:"
        )
        if not ok2 or not name.strip():
            return
        mgr_key = "__custom__" if mgr == "[Free-form / Custom]" else mgr
        self.sig_device_duped.emit("__ADD__", f"{cat}|{name.strip()}|{mgr_key}")

    def deselect_all(self):
        if self._selected:
            old = self._cards.get(self._selected)
            if old:
                old.set_selected(False)
        self._selected = None


# =============================================================================
# FieldWidget – single editable field row
# =============================================================================
class FieldWidget(QWidget):
    def __init__(self, field_def: dict, current_value, parent=None):
        super().__init__(parent)
        self._def = field_def
        self._init_widget(current_value)

    def _init_widget(self, value):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        tp = self._def["type"]
        if tp == "bool":
            self._w = QCheckBox()
            self._w.setChecked(bool(value) if value is not None else False)
        elif tp == "int":
            self._w = QSpinBox()
            self._w.setRange(-999999, 999999)
            self._w.setValue(int(value) if value is not None else 0)
        elif tp == "float":
            self._w = QDoubleSpinBox()
            self._w.setRange(-1e9, 1e9)
            self._w.setDecimals(4)
            self._w.setValue(float(value) if value is not None else 0.0)
        elif tp == "select":
            self._w = QComboBox()
            self._w.addItems(self._def["opts"])
            idx = self._w.findText(str(value) if value is not None else "")
            if idx >= 0:
                self._w.setCurrentIndex(idx)
        elif tp == "path":
            row = QWidget()
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            self._w = QLineEdit(str(value) if value is not None else "")
            btn = QPushButton("…")
            btn.setFixedWidth(28)
            btn.clicked.connect(self._pick_path)
            rl.addWidget(self._w)
            rl.addWidget(btn)
            lay.addWidget(row)
            if self._def.get("tip"):
                self._w.setToolTip(self._def["tip"])
            return
        else:  # text
            self._w = QLineEdit(
                "null" if value is None else str(value)
            )
        lay.addWidget(self._w)
        if self._def.get("tip"):
            self._w.setToolTip(self._def["tip"])

    def _pick_path(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select file")
        if path:
            self._w.setText(path)

    def get_value(self):
        tp = self._def["type"]
        if tp == "bool":
            return self._w.isChecked()
        if tp == "int":
            return self._w.value()
        if tp == "float":
            return self._w.value()
        if tp == "select":
            return self._w.currentText()
        # text / path
        txt = self._w.text().strip()
        if txt.lower() == "null":
            return None
        return txt


# =============================================================================
# PropertyEditor – right panel
# =============================================================================
class PropertyEditor(QWidget):
    sig_apply = pyqtSignal(str, str, dict)   # (category, name, new_device_dict)
    sig_rename = pyqtSignal(str, str, str)    # (category, old_name, new_name)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(320)
        self._cat = ""
        self._name = ""
        self._device = {}
        self._field_widgets: dict[tuple, FieldWidget] = {}   # (section, key) → widget

        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(6)

        # ── Header ──
        hdr = QFrame()
        hdr.setStyleSheet("background:#F0F4F8; border-radius:4px;")
        hdr_lay = QVBoxLayout(hdr)
        hdr_lay.setContentsMargins(8, 6, 8, 6)
        hdr_lay.setSpacing(4)

        row1 = QHBoxLayout()
        self._name_lbl = QLabel("<i>No device selected</i>")
        self._name_lbl.setTextFormat(Qt.RichText)
        bold = QFont()
        bold.setBold(True)
        bold.setPointSize(10)
        self._name_lbl.setFont(bold)
        row1.addWidget(self._name_lbl)
        row1.addStretch()
        rename_btn = QPushButton("Rename…")
        rename_btn.setFixedHeight(22)
        rename_btn.setStyleSheet("font-size:8pt;")
        rename_btn.clicked.connect(self._do_rename)
        row1.addWidget(rename_btn)
        hdr_lay.addLayout(row1)

        # Manager type: combo for known schemas + line-edit for custom/free-form
        self._mgr_combo = QComboBox()
        self._mgr_combo.addItem("— Custom / Free-form —", "__custom__")
        for mgr in sorted(SCHEMAS):
            self._mgr_combo.addItem(SCHEMAS[mgr]["display"], mgr)
        self._mgr_combo.currentIndexChanged.connect(self._on_manager_changed)
        hdr_lay.addWidget(self._mgr_combo)

        self._custom_mgr_edit = QLineEdit()
        self._custom_mgr_edit.setPlaceholderText("Manager class name (e.g. MyCustomManager)…")
        self._custom_mgr_edit.setVisible(False)
        hdr_lay.addWidget(self._custom_mgr_edit)
        outer.addWidget(hdr)

        # ── Tab widget (populated dynamically) ──
        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        outer.addWidget(self._tabs, 1)

        # ── Validation label ──
        self._val_lbl = QLabel()
        self._val_lbl.setWordWrap(True)
        self._val_lbl.setStyleSheet("color:#C06000; font-size:8pt;")
        outer.addWidget(self._val_lbl)

        # ── Add custom field buttons ──
        add_row = QHBoxLayout()
        add_top_btn = QPushButton("⊕ Add field")
        add_top_btn.setFixedHeight(22)
        add_top_btn.setStyleSheet("font-size:8pt; padding:0 6px;")
        add_top_btn.setToolTip("Add an arbitrary top-level field to this device")
        add_top_btn.clicked.connect(lambda: self._add_custom_field("top"))
        add_row.addWidget(add_top_btn)
        add_prop_btn = QPushButton("⊕ Add property")
        add_prop_btn.setFixedHeight(22)
        add_prop_btn.setStyleSheet("font-size:8pt; padding:0 6px;")
        add_prop_btn.setToolTip("Add an arbitrary field inside managerProperties")
        add_prop_btn.clicked.connect(lambda: self._add_custom_field("props"))
        add_row.addWidget(add_prop_btn)
        outer.addLayout(add_row)

        # ── Apply button ──
        apply_btn = QPushButton("Apply Changes")
        apply_btn.setStyleSheet("""
            QPushButton {
                background:#3A7FC1; color:white; border-radius:4px;
                padding:6px; font-size:10pt;
            }
            QPushButton:hover { background:#2A6FAF; }
        """)
        apply_btn.clicked.connect(self._do_apply)
        outer.addWidget(apply_btn)

        self._block_combo = False

    def load_device(self, cat: str, name: str, device: dict):
        self._cat = cat
        self._name = name
        self._device = copy.deepcopy(device)
        self._name_lbl.setText(name)

        mgr = device.get("managerName", "")
        self._block_combo = True
        idx = self._mgr_combo.findData(mgr)
        if idx >= 0:
            self._mgr_combo.setCurrentIndex(idx)
            self._custom_mgr_edit.setVisible(False)
        else:
            self._mgr_combo.setCurrentIndex(0)          # "Custom / Free-form"
            self._custom_mgr_edit.setText(mgr)
            self._custom_mgr_edit.setVisible(True)
        self._block_combo = False

        self._rebuild_form()

    def _on_manager_changed(self, _):
        if self._block_combo:
            return
        if not self._cat:
            return
        new_mgr = self._mgr_combo.currentData()
        is_custom = new_mgr == "__custom__"
        self._custom_mgr_edit.setVisible(is_custom)
        if is_custom:
            return  # user types the manager name; rebuild happens on Apply
        if new_mgr and new_mgr != self._device.get("managerName"):
            default = _build_default_device(new_mgr)
            default["managerName"] = new_mgr
            self._device = default
            self._rebuild_form()

    def _rebuild_form(self):
        self._tabs.clear()
        self._field_widgets.clear()

        raw_mgr = self._mgr_combo.currentData()
        if raw_mgr == "__custom__":
            mgr = self._custom_mgr_edit.text().strip() or self._device.get("managerName", "")
        else:
            mgr = raw_mgr or self._device.get("managerName", "")
        schema = SCHEMAS.get(mgr, {})
        props = self._device.get("managerProperties") or {}

        # Collect fields grouped by grp
        groups: dict[str, list] = {}
        all_fields = []
        for f in schema.get("top", []):
            all_fields.append(("top", f))
        for f in schema.get("props", []):
            all_fields.append(("props", f))
        for nest_key, nest_fields in schema.get("nested", {}).items():
            for f in nest_fields:
                all_fields.append((f"nested:{nest_key}", f))

        for section, f in all_fields:
            grp = f["grp"]
            groups.setdefault(grp, []).append((section, f))

        # Ensure "Basic" is first, "Advanced" is last
        ordered_groups = sorted(groups.keys(),
                                key=lambda g: (0 if g == "Basic" else
                                               2 if g == "Advanced" else 1))

        for grp in ordered_groups:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            inner = QWidget()
            form = QFormLayout(inner)
            form.setContentsMargins(8, 8, 8, 8)
            form.setSpacing(6)
            form.setLabelAlignment(Qt.AlignRight)

            for section, f in groups[grp]:
                if section == "top":
                    current = self._device.get(f["key"], f["default"])
                elif section == "props":
                    current = props.get(f["key"], f["default"])
                else:
                    nest_key = section.split(":", 1)[1]
                    current = (props.get(nest_key) or {}).get(f["key"], f["default"])

                fw = FieldWidget(f, current)
                lbl = f["label"]
                if f["req"]:
                    lbl = f"<b>{lbl}</b> *"
                row_label = QLabel(lbl)
                row_label.setTextFormat(Qt.RichText)
                row_label.setToolTip(f.get("tip", ""))
                form.addRow(row_label, fw)
                self._field_widgets[(section, f["key"])] = fw

            scroll.setWidget(inner)
            self._tabs.addTab(scroll, grp)

        # Unknown managerProperties not covered by schema (shown in "Properties" tab)
        unknown_props, unknown_top = self._collect_unknown(schema)

        def _make_raw_tab(items, section_key, tab_label):
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            inner = QWidget()
            form = QFormLayout(inner)
            form.setContentsMargins(8, 8, 8, 8)
            form.setSpacing(4)
            for k, v in items.items():
                display = json.dumps(v) if not isinstance(v, str) else v
                le = QLineEdit(display)
                form.addRow(QLabel(k), le)
                self._field_widgets[(section_key, k)] = le
            scroll.setWidget(inner)
            self._tabs.addTab(scroll, tab_label)

        if unknown_props:
            _make_raw_tab(unknown_props, "raw_prop", "Properties")
        if unknown_top:
            _make_raw_tab(unknown_top, "raw", "Other")

    def _collect_unknown(self, schema: dict):
        """Return (unknown_props dict, unknown_top dict) — fields not covered by schema."""
        known_top = {f["key"] for f in schema.get("top", [])}
        known_top |= {"managerName", "managerProperties"}
        unknown_top = {k: v for k, v in self._device.items() if k not in known_top}

        known_props = {f["key"] for f in schema.get("props", [])}
        known_props |= set(schema.get("nested", {}).keys())
        props = self._device.get("managerProperties") or {}
        # Expose scalar/list props; leave nested dicts collapsed in JSON
        unknown_props = {
            k: v for k, v in props.items()
            if k not in known_props and not isinstance(v, dict)
        }
        return unknown_props, unknown_top

    def _do_rename(self):
        if not self._cat:
            return
        new_name, ok = QInputDialog.getText(
            self, "Rename Device", "New name:", text=self._name
        )
        if ok and new_name.strip() and new_name.strip() != self._name:
            self.sig_rename.emit(self._cat, self._name, new_name.strip())
            self._name = new_name.strip()
            self._name_lbl.setText(self._name)

    def _do_apply(self):
        if not self._cat:
            return
        raw_mgr = self._mgr_combo.currentData()
        if raw_mgr == "__custom__":
            mgr = self._custom_mgr_edit.text().strip() or self._device.get("managerName", "")
        else:
            mgr = raw_mgr or self._device.get("managerName", "")
        schema = SCHEMAS.get(mgr, {})
        new_device: dict = {"managerName": mgr, "managerProperties": {}}
        props = new_device["managerProperties"]

        nested_keys: dict[str, dict] = {}
        for nest_key in schema.get("nested", {}):
            nested_keys[nest_key] = {}

        for (section, key), fw in self._field_widgets.items():
            if section in ("raw", "raw_prop"):
                raw_val = fw.text().strip()  # type: ignore[attr-defined]
                try:
                    value = json.loads(raw_val)
                except Exception:
                    value = raw_val
                if section == "raw_prop":
                    props[key] = value
                else:
                    new_device[key] = value
                continue
            val = fw.get_value()
            if section == "top":
                if key == "axes":
                    # Axes stored as array in JSON
                    if isinstance(val, str):
                        val = [a.strip() for a in val.split(",") if a.strip()]
                elif key == "digitalPorts":
                    if isinstance(val, str):
                        val = [p.strip() for p in val.split(",") if p.strip()]
                new_device[key] = val
            elif section == "props":
                props[key] = val
            else:
                nest_key = section.split(":", 1)[1]
                nested_keys[nest_key][key] = val

        for nest_key, nest_vals in nested_keys.items():
            if nest_vals:
                props[nest_key] = nest_vals

        # Validate required fields
        warnings = []
        for f in schema.get("top", []) + schema.get("props", []):
            if f["req"]:
                v = new_device.get(f["key"]) if f in schema.get("top", []) else props.get(f["key"])
                if v is None or v == "":
                    warnings.append(f"⚠  Required: {f['label']}")
        self._val_lbl.setText("\n".join(warnings))

        self.sig_apply.emit(self._cat, self._name, new_device)

    def _add_custom_field(self, where: str):
        """Prompt for a key+value and inject it into the in-memory device, then rebuild."""
        if not self._cat:
            return
        key, ok = QInputDialog.getText(self, "Add Field", "Key name:")
        if not ok or not key.strip():
            return
        val_str, ok2 = QInputDialog.getText(
            self, "Add Field",
            'Value  (JSON: 42, true, "text", null, [1,2], {...}):',
            text="null",
        )
        if not ok2:
            return
        try:
            value = json.loads(val_str.strip()) if val_str.strip() else None
        except json.JSONDecodeError:
            value = val_str.strip()

        if where == "top":
            self._device[key.strip()] = value
        else:
            if not isinstance(self._device.get("managerProperties"), dict):
                self._device["managerProperties"] = {}
            self._device["managerProperties"][key.strip()] = value
        self._rebuild_form()

    def clear(self):
        self._cat = ""
        self._name = ""
        self._device = {}
        self._field_widgets.clear()
        self._tabs.clear()
        self._name_lbl.setText("<i>No device selected</i>")
        self._val_lbl.clear()
        self._custom_mgr_edit.setVisible(False)


# =============================================================================
# JsonEditorDialog – modal JSON editor for arbitrary config sections
# =============================================================================
class JsonEditorDialog(QDialog):
    def __init__(self, section_key: str, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit section: {section_key}")
        self.resize(520, 440)
        self._original = json.dumps(data, indent=2, ensure_ascii=False)
        self._result = data
        self._changed = False

        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)

        hint = QLabel(
            f"<span style='color:#555;font-size:8pt;'>Editing: <b>{section_key}</b>"
            "  —  Valid JSON required  —  Close with unsaved changes to be prompted</span>"
        )
        hint.setTextFormat(Qt.RichText)
        lay.addWidget(hint)

        self._edit = QTextEdit()
        mono = QFont("Courier New", 10)
        self._edit.setFont(mono)
        self._edit.setPlainText(self._original)
        lay.addWidget(self._edit, 1)

        self._err_lbl = QLabel()
        self._err_lbl.setStyleSheet("color:#C04000; font-size:8pt;")
        self._err_lbl.setWordWrap(True)
        lay.addWidget(self._err_lbl)

        btns = QHBoxLayout()
        btns.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        ok_btn = QPushButton("Apply")
        ok_btn.setDefault(True)
        ok_btn.setStyleSheet(
            "QPushButton { background:#3A7FC1; color:white; padding:4px 16px; }"
            "QPushButton:hover { background:#2A6FAF; }"
        )
        ok_btn.clicked.connect(self._try_apply)
        btns.addWidget(cancel_btn)
        btns.addWidget(ok_btn)
        lay.addLayout(btns)

    def _try_apply(self):
        text = self._edit.toPlainText()
        try:
            self._result = json.loads(text)
            self._changed = (text.strip() != self._original.strip())
            self.accept()
        except json.JSONDecodeError as e:
            self._err_lbl.setText(f"JSON error: {e}")

    def closeEvent(self, event):
        text = self._edit.toPlainText()
        if text.strip() != self._original.strip():
            r = QMessageBox.question(
                self, "Unsaved Changes",
                "Apply changes before closing?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            )
            if r == QMessageBox.Cancel:
                event.ignore()
                return
            if r == QMessageBox.Yes:
                try:
                    self._result = json.loads(text)
                    self._changed = True
                except json.JSONDecodeError as e:
                    QMessageBox.warning(self, "Invalid JSON",
                                        f"Fix JSON before closing:\n{e}")
                    event.ignore()
                    return
        event.accept()

    @property
    def result_data(self):
        return self._result

    @property
    def changed(self):
        return self._changed


# =============================================================================
# ConfigExtrasBar – availableWidgets list + buttons for other config sections
# =============================================================================
class ConfigExtrasBar(QFrame):
    sig_modified = pyqtSignal()   # any change → MainWindow marks dirty

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("QFrame { background:#F5F5F5; border-top:1px solid #DDD; }")
        self.setFixedHeight(64)
        self._data: dict = {}

        root = QHBoxLayout(self)
        root.setContentsMargins(10, 4, 10, 4)
        root.setSpacing(10)

        # ── Available Widgets ──────────────────────────────────────────────
        wlbl = QLabel("<b style='font-size:8pt;'>Available Widgets:</b>")
        wlbl.setTextFormat(Qt.RichText)
        root.addWidget(wlbl)

        self._widgets_inner = QWidget()
        self._widgets_lay = QHBoxLayout(self._widgets_inner)
        self._widgets_lay.setContentsMargins(0, 0, 0, 0)
        self._widgets_lay.setSpacing(4)
        w_scroll = QScrollArea()
        w_scroll.setWidgetResizable(True)
        w_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        w_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        w_scroll.setFrameShape(QFrame.NoFrame)
        w_scroll.setFixedHeight(54)
        w_scroll.setWidget(self._widgets_inner)
        root.addWidget(w_scroll, 1)

        add_w_btn = QPushButton("＋")
        add_w_btn.setFixedSize(24, 24)
        add_w_btn.setToolTip("Add a widget name")
        add_w_btn.setStyleSheet(
            "QPushButton { font-size:12pt; border:1px solid #AAA; border-radius:3px; }"
            "QPushButton:hover { background:#DDD; }"
        )
        add_w_btn.clicked.connect(self._add_widget)
        root.addWidget(add_w_btn)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color:#CCC;")
        root.addWidget(sep)

        # ── Other sections ─────────────────────────────────────────────────
        slbl = QLabel("<b style='font-size:8pt;'>Other sections:</b>")
        slbl.setTextFormat(Qt.RichText)
        root.addWidget(slbl)

        self._sections_inner = QWidget()
        self._sections_lay = QHBoxLayout(self._sections_inner)
        self._sections_lay.setContentsMargins(0, 0, 0, 0)
        self._sections_lay.setSpacing(4)
        root.addWidget(self._sections_inner)
        root.addStretch()

    # ── Public ────────────────────────────────────────────────────────────

    def load(self, data: dict):
        self._data = data
        self._refresh_widgets()
        self._refresh_sections()

    def clear(self):
        self._data = {}
        self._refresh_widgets()
        self._refresh_sections()

    # ── Widget chips ─────────────────────────────────────────────────────

    def _refresh_widgets(self):
        while self._widgets_lay.count():
            item = self._widgets_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for w in (self._data.get("availableWidgets") or []):
            self._widgets_lay.addWidget(self._make_chip(str(w)))
        self._widgets_lay.addStretch()

    def _make_chip(self, name: str) -> QWidget:
        chip = QFrame()
        chip.setStyleSheet(
            "QFrame { background:#E0E8F0; border:1px solid #B0C4D8; "
            "border-radius:3px; }"
        )
        lay = QHBoxLayout(chip)
        lay.setContentsMargins(5, 1, 2, 1)
        lay.setSpacing(2)
        lbl = QLabel(name)
        lbl.setStyleSheet("font-size:8pt; border:none; background:transparent;")
        lay.addWidget(lbl)
        del_btn = QPushButton("×")
        del_btn.setFixedSize(14, 14)
        del_btn.setStyleSheet(
            "QPushButton { border:none; color:#666; background:transparent; font-size:9pt; }"
            "QPushButton:hover { color:#C00; }"
        )
        del_btn.clicked.connect(lambda _, n=name: self._remove_widget(n))
        lay.addWidget(del_btn)
        return chip

    def _add_widget(self):
        name, ok = QInputDialog.getText(self, "Add Widget", "Widget name:")
        if not ok or not name.strip():
            return
        widgets = list(self._data.get("availableWidgets") or [])
        if name.strip() not in widgets:
            widgets.append(name.strip())
            self._data["availableWidgets"] = widgets
            self._refresh_widgets()
            self.sig_modified.emit()

    def _remove_widget(self, name: str):
        widgets = list(self._data.get("availableWidgets") or [])
        if name in widgets:
            widgets.remove(name)
            self._data["availableWidgets"] = widgets
            self._refresh_widgets()
            self.sig_modified.emit()

    # ── Section buttons ──────────────────────────────────────────────────

    def _refresh_sections(self):
        while self._sections_lay.count():
            item = self._sections_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        excluded = set(DEVICE_CATS) | {"availableWidgets"}
        for key, val in self._data.items():
            if key in excluded:
                continue
            btn = QPushButton(key)
            btn.setFixedHeight(26)
            btn.setStyleSheet(
                "QPushButton { font-size:8pt; padding:0 8px; border:1px solid #B0B8C0; "
                "border-radius:3px; background:#EEF2F6; }"
                "QPushButton:hover { background:#DDE8F2; }"
            )
            btn.setToolTip(f"View / edit '{key}' section")
            btn.clicked.connect(lambda _, k=key: self._open_section(k))
            self._sections_lay.addWidget(btn)

    def _open_section(self, key: str):
        val = self._data.get(key)
        dlg = JsonEditorDialog(key, val, self)
        dlg.exec_()
        if dlg.changed:
            self._data[key] = dlg.result_data
            self._refresh_sections()
            self.sig_modified.emit()


# =============================================================================
# TemplateStore – file-backed user template library
# =============================================================================
class TemplateStore:
    """
    Persists user templates as JSON files in a templates/ directory next to
    the script.  One sub-directory per category; one JSON file per template.
    templates/
      detectors/
        MyAPD.json
      lasers/
        My488nm.json
    """

    def __init__(self, store_dir: object = None):
        if store_dir is None:
            store_dir = Path(os.path.abspath(__file__)).parent / "templates"
        self._dir = Path(store_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict = {}   # cat → {name: device}
        self.reload()

    def reload(self):
        self._cache.clear()
        for cat_dir in sorted(self._dir.iterdir()):
            if not cat_dir.is_dir():
                continue
            templates: dict = {}
            for f in sorted(cat_dir.glob("*.json")):
                try:
                    with open(f, encoding="utf-8") as fh:
                        templates[f.stem] = json.load(fh)
                except Exception:
                    pass
            if templates:
                self._cache[cat_dir.name] = templates

    @property
    def store_dir(self) -> Path:
        return self._dir

    def categories(self) -> list:
        return sorted(self._cache.keys())

    def templates_in(self, cat: str) -> dict:
        return dict(self._cache.get(cat, {}))

    def add(self, cat: str, name: str, device: dict):
        self._cache.setdefault(cat, {})[name] = copy.deepcopy(device)
        self._flush(cat, name, device)

    def delete(self, cat: str, name: str):
        if cat not in self._cache:
            return
        self._cache[cat].pop(name, None)
        p = self._dir / cat / f"{name}.json"
        p.unlink(missing_ok=True)
        if not self._cache[cat]:
            del self._cache[cat]
            try:
                (self._dir / cat).rmdir()
            except OSError:
                pass

    def move(self, from_cat: str, name: str, to_cat: str):
        device = self._cache.get(from_cat, {}).get(name)
        if device is None:
            return
        self.delete(from_cat, name)
        self.add(to_cat, name, device)

    def create_category(self, cat: str):
        if cat not in self._cache:
            self._cache[cat] = {}
            (self._dir / cat).mkdir(exist_ok=True)

    def delete_category(self, cat: str):
        self._cache.pop(cat, None)
        import shutil
        cat_dir = self._dir / cat
        if cat_dir.exists():
            shutil.rmtree(cat_dir, ignore_errors=True)

    def _flush(self, cat: str, name: str, device: dict):
        cat_dir = self._dir / cat
        cat_dir.mkdir(exist_ok=True)
        with open(cat_dir / f"{name}.json", "w", encoding="utf-8") as fh:
            json.dump(device, fh, indent=2, ensure_ascii=False)


# =============================================================================
# LeftPanel – file browser + template library
# =============================================================================
class LeftPanel(QWidget):
    sig_file_open = pyqtSignal(str)
    # (category, device_or_mgr_name): str mgr_name for builtin, dict for user
    sig_tmpl_add  = pyqtSignal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        self._store = TemplateStore()
        self._config_dir: object = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(6)

        # ── Config Files ──
        hdr = QLabel("<b>Config Files</b>")
        hdr.setTextFormat(Qt.RichText)
        lay.addWidget(hdr)

        open_btn = QPushButton("Open Folder…")
        open_btn.clicked.connect(self._open_folder)
        lay.addWidget(open_btn)

        self._file_list = QTreeWidget()
        self._file_list.setHeaderHidden(True)
        self._file_list.setIndentation(12)
        self._file_list.setMaximumHeight(160)
        self._file_list.itemDoubleClicked.connect(self._on_file_double_click)
        lay.addWidget(self._file_list)

        # ── Templates ──
        tmpl_hdr = QHBoxLayout()
        tmpl_lbl = QLabel("<b>Templates</b>")
        tmpl_lbl.setTextFormat(Qt.RichText)
        tmpl_hdr.addWidget(tmpl_lbl)
        tmpl_hdr.addStretch()
        new_cat_btn = QPushButton("＋ Category")
        new_cat_btn.setFixedHeight(20)
        new_cat_btn.setStyleSheet("font-size:8pt; padding:0 4px;")
        new_cat_btn.setToolTip("Create a new user template category")
        new_cat_btn.clicked.connect(self._new_user_category)
        tmpl_hdr.addWidget(new_cat_btn)
        lay.addLayout(tmpl_hdr)

        self._tmpl_tree = QTreeWidget()
        self._tmpl_tree.setHeaderHidden(True)
        self._tmpl_tree.setIndentation(12)
        self._tmpl_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tmpl_tree.customContextMenuRequested.connect(self._tmpl_context_menu)
        self._tmpl_tree.itemDoubleClicked.connect(self._on_tmpl_double_click)
        lay.addWidget(self._tmpl_tree, 1)

        hint = QLabel("<span style='color:#888;font-size:8pt;'>Double-click to instantiate</span>")
        hint.setTextFormat(Qt.RichText)
        lay.addWidget(hint)

        self._refresh_tmpl_tree()

    # ── File browser ──────────────────────────────────────────────────────
    def _open_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Open Config Folder",
                                             str(Path.home()))
        if d:
            self._config_dir = d
            self._refresh_file_list(d)

    def _refresh_file_list(self, folder: str):
        self._file_list.clear()
        for p in sorted(Path(folder).glob("*.json")):
            item = QTreeWidgetItem([p.name])
            item.setData(0, Qt.UserRole, str(p))
            self._file_list.addTopLevelItem(item)

    def _on_file_double_click(self, item: QTreeWidgetItem, _col: int):
        path = item.data(0, Qt.UserRole)
        if path:
            self.sig_file_open.emit(path)

    def set_folder(self, folder: str):
        self._config_dir = folder
        self._refresh_file_list(folder)

    # ── Template tree ─────────────────────────────────────────────────────
    def _refresh_tmpl_tree(self):
        self._tmpl_tree.clear()
        from PyQt5.QtGui import QColor as _QColor

        # ── Built-in section ──
        builtin_root = QTreeWidgetItem(["Built-in"])
        bold = QFont(); bold.setBold(True)
        builtin_root.setFont(0, bold)
        builtin_root.setForeground(0, _QColor("#444"))
        self._tmpl_tree.addTopLevelItem(builtin_root)

        for cat in DEVICE_CATS:
            managers = CAT_MANAGERS.get(cat, [])
            if not managers:
                continue
            cat_item = QTreeWidgetItem([CAT_LABEL[cat]])
            cat_item.setForeground(0, _QColor(CAT_COLOR[cat]))
            f = QFont(); f.setBold(True)
            cat_item.setFont(0, f)
            cat_item.setData(0, Qt.UserRole, ("builtin_cat", cat))
            builtin_root.addChild(cat_item)
            for mgr in managers:
                child = QTreeWidgetItem([SCHEMAS[mgr]["display"]])
                child.setData(0, Qt.UserRole, ("builtin", cat, mgr))
                cat_item.addChild(child)
            cat_item.setExpanded(True)
        builtin_root.setExpanded(True)

        # ── My Templates section ──
        user_cats = self._store.categories()
        if user_cats:
            my_root = QTreeWidgetItem(["My Templates"])
            my_root.setFont(0, bold)
            my_root.setForeground(0, _QColor("#444"))
            self._tmpl_tree.addTopLevelItem(my_root)

            for cat in user_cats:
                templates = self._store.templates_in(cat)
                color = CAT_COLOR.get(cat, "#888")
                label = CAT_LABEL.get(cat, cat)
                cat_item = QTreeWidgetItem([f"{label}  ({len(templates)})"])
                cat_item.setForeground(0, _QColor(color))
                f2 = QFont(); f2.setBold(True)
                cat_item.setFont(0, f2)
                cat_item.setData(0, Qt.UserRole, ("user_cat", cat))
                my_root.addChild(cat_item)
                for tname, tdata in templates.items():
                    child = QTreeWidgetItem([tname])
                    child.setData(0, Qt.UserRole, ("user", cat, tname, tdata))
                    cat_item.addChild(child)
                cat_item.setExpanded(True)
            my_root.setExpanded(True)

    def add_user_template(self, cat: str, name: str, device_data: dict):
        self._store.add(cat, name, device_data)
        self._refresh_tmpl_tree()

    def _new_user_category(self):
        name, ok = QInputDialog.getText(self, "New Template Category",
                                        "Category name (e.g. 'my_detectors'):")
        if ok and name.strip():
            self._store.create_category(name.strip())
            self._refresh_tmpl_tree()

    def _on_tmpl_double_click(self, item: QTreeWidgetItem, _col: int):
        payload = item.data(0, Qt.UserRole)
        if not payload:
            return
        kind = payload[0]
        if kind == "builtin":
            _k, cat, mgr = payload
            self.sig_tmpl_add.emit(cat, mgr)
        elif kind == "user":
            _k, cat, tname, tdata = payload
            self.sig_tmpl_add.emit(cat, copy.deepcopy(tdata))

    def _tmpl_context_menu(self, pos):
        item = self._tmpl_tree.itemAt(pos)
        if not item:
            return
        payload = item.data(0, Qt.UserRole)
        if not payload:
            return
        kind = payload[0]
        menu = QMenu(self)

        if kind == "user":
            _k, cat, tname, tdata = payload
            a_move = menu.addAction("Move to Category…")
            menu.addSeparator()
            a_del = menu.addAction("Delete Template")
            action = menu.exec_(self._tmpl_tree.mapToGlobal(pos))
            if action == a_del:
                self._store.delete(cat, tname)
                self._refresh_tmpl_tree()
            elif action == a_move:
                self._move_template(cat, tname)

        elif kind == "user_cat":
            _k, cat = payload
            a_new = menu.addAction("New Category…")
            menu.addSeparator()
            a_del = menu.addAction("Delete Category")
            action = menu.exec_(self._tmpl_tree.mapToGlobal(pos))
            if action == a_new:
                self._new_user_category()
            elif action == a_del:
                templates = self._store.templates_in(cat)
                if templates:
                    QMessageBox.warning(self, "Delete Category",
                                        f"Category '{cat}' still has {len(templates)} template(s). "
                                        f"Delete or move them first.")
                else:
                    self._store.delete_category(cat)
                    self._refresh_tmpl_tree()

    def _move_template(self, from_cat: str, name: str):
        cats = self._store.categories()
        choices = cats + ["── New Category… ──"]
        choice, ok = QInputDialog.getItem(self, "Move Template",
                                          "Move to category:", choices, 0, False)
        if not ok:
            return
        if choice == "── New Category… ──":
            new_cat, ok2 = QInputDialog.getText(self, "New Category", "Category name:")
            if not ok2 or not new_cat.strip():
                return
            choice = new_cat.strip()
        self._store.move(from_cat, name, choice)
        self._refresh_tmpl_tree()


# =============================================================================
# ValidationPanel – DAQ conflict summary
# =============================================================================
class ValidationPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setMaximumHeight(120)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 4, 6, 4)
        lbl = QLabel("<b>Validation</b>")
        lbl.setTextFormat(Qt.RichText)
        lay.addWidget(lbl)
        self._text = QLabel("No config loaded.")
        self._text.setWordWrap(True)
        self._text.setTextFormat(Qt.RichText)
        self._text.setStyleSheet("font-size:8pt;")
        lay.addWidget(self._text)

    def validate(self, data: dict):
        issues = []
        used = _collect_daq_channels(data)
        for ch, names in used.items():
            if len(names) > 1:
                issues.append(f"⚠ DAQ conflict <b>{ch}</b>: {', '.join(names)}")

        # All device categories are optional — only flag real conflicts
        present = [CAT_LABEL[c] for c in DEVICE_CATS if data.get(c)]
        devcount = sum(len(data.get(c) or {}) for c in DEVICE_CATS)

        if issues:
            self._text.setText("<br>".join(issues))
            self._text.setStyleSheet("font-size:8pt; color:#C04000;")
        else:
            cats_str = ", ".join(present) if present else "none"
            self._text.setText(
                f"<span style='color:#3A8B3A;'>✓ No issues</span>"
                f"<span style='color:#666;'> — {devcount} devices"
                f" ({cats_str})</span>"
            )
            self._text.setStyleSheet("font-size:8pt;")


# =============================================================================
# MainWindow
# =============================================================================
class MainWindow(QMainWindow):
    # Well-known location of imcontrol_options.json
    _OPTIONS_SEARCH_ROOTS = [
        Path.home() / "Documents" / "ImSwitchConfig" / "config",
        Path.home() / "ImSwitchConfig" / "config",
        Path("/") / "etc" / "imswitch",
    ]

    def __init__(self, start_folder: str = ""):
        super().__init__()
        self.setWindowTitle("ImSwitch Config Studio")
        self.resize(1280, 780)
        self._data: dict = {}
        self._path: str = ""
        self._modified = False
        self._options_path: str = ""   # path to imcontrol_options.json if found

        self._build_toolbar()
        self._build_ui()
        self._build_status_bar()

        if start_folder and os.path.isdir(start_folder):
            self._left.set_folder(start_folder)

        self._detect_options_file()

    # ── Build UI ──────────────────────────────────────────────────────────
    def _build_toolbar(self):
        tb = QToolBar()
        tb.setMovable(False)
        tb.setStyleSheet("QToolBar { spacing:4px; padding:4px; }")
        self.addToolBar(tb)

        def _btn(label, slot, tip=""):
            a = QAction(label, self)
            a.setToolTip(tip)
            a.triggered.connect(slot)
            tb.addAction(a)
            return a

        _btn("New",        self._new_file,   "Create blank config")
        _btn("Open File…", self._open_file,  "Open a JSON config file")
        _btn("Save",       self._save_file,  "Save current file (Ctrl+S)")
        _btn("Save As…",   self._save_as,    "Save to a new file")
        tb.addSeparator()
        _btn("Validate",   self._run_validation, "Check for DAQ conflicts")

        self.addAction(self._make_shortcut("Ctrl+S", self._save_file))

    def _make_shortcut(self, key, slot):
        a = QAction(self)
        a.setShortcut(key)
        a.triggered.connect(slot)
        return a

    def _build_ui(self):
        root = QWidget()
        root_lay = QVBoxLayout(root)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)
        self.setCentralWidget(root)

        # ── Active-config banner (hidden until options file found) ──
        self._active_banner = QFrame()
        self._active_banner.setStyleSheet(
            "QFrame { background:#1A3A5C; border-bottom:1px solid #0D2540; }"
        )
        self._active_banner.setFixedHeight(36)
        bl = QHBoxLayout(self._active_banner)
        bl.setContentsMargins(10, 0, 10, 0)

        self._active_lbl = QLabel()
        self._active_lbl.setStyleSheet("color:#9CC4F0; font-size:9pt;")
        self._active_lbl.setTextFormat(Qt.RichText)
        bl.addWidget(self._active_lbl)
        bl.addStretch()

        set_active_btn = QPushButton("Set as Active Config")
        set_active_btn.setFixedHeight(24)
        set_active_btn.setStyleSheet("""
            QPushButton {
                background:#2E6DA4; color:white; border-radius:3px;
                font-size:9pt; padding:0 10px;
            }
            QPushButton:hover { background:#3A85C4; }
            QPushButton:disabled { background:#334; color:#668; }
        """)
        set_active_btn.clicked.connect(self._set_as_active_config)
        self._set_active_btn = set_active_btn
        bl.addWidget(set_active_btn)

        self._active_banner.setVisible(False)
        root_lay.addWidget(self._active_banner)

        splitter = QSplitter(Qt.Horizontal)
        root_lay.addWidget(splitter, 1)

        # Left
        self._left = LeftPanel()
        self._left.sig_file_open.connect(self._load_file)
        self._left.sig_tmpl_add.connect(self._add_from_template)
        splitter.addWidget(self._left)

        # Centre + validation
        centre = QWidget()
        cl = QVBoxLayout(centre)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)
        self._canvas = DeviceCanvas()
        self._canvas.sig_device_selected.connect(self._on_device_selected)
        self._canvas.sig_device_deleted.connect(self._on_device_deleted)
        self._canvas.sig_device_duped.connect(self._on_device_duped_or_add)
        self._canvas.sig_device_renamed.connect(self._on_device_rename_from_canvas)
        self._canvas.sig_save_tmpl.connect(self._on_save_template)
        cl.addWidget(self._canvas, 1)
        self._val_panel = ValidationPanel()
        cl.addWidget(self._val_panel)
        splitter.addWidget(centre)

        # Right
        self._editor = PropertyEditor()
        self._editor.sig_apply.connect(self._on_editor_apply)
        self._editor.sig_rename.connect(self._on_device_rename)
        splitter.addWidget(self._editor)

        splitter.setSizes([220, 780, 340])

        # ── Extras bar: availableWidgets + other sections ──
        self._extras_bar = ConfigExtrasBar()
        self._extras_bar.sig_modified.connect(self._on_extras_modified)
        root_lay.addWidget(self._extras_bar)

    def _build_status_bar(self):
        sb = QStatusBar()
        self.setStatusBar(sb)
        self._status = QLabel("Ready")
        sb.addWidget(self._status)

    # ── File operations ───────────────────────────────────────────────────
    def _new_file(self):
        if not self._confirm_discard():
            return
        self._data = {cat: {} for cat in DEVICE_CATS}
        self._data["availableWidgets"] = []
        self._path = ""
        self._modified = False
        self._refresh_canvas()
        self._editor.clear()
        self._extras_bar.load(self._data)
        self._status.setText("New config (unsaved)")
        self.setWindowTitle("ImSwitch Config Studio — [new]")

    def _open_file(self):
        if not self._confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Config", "", "JSON files (*.json)"
        )
        if path:
            self._load_file(path)

    def _load_file(self, path: str):
        try:
            with open(path, encoding="utf-8") as fh:
                self._data = json.load(fh)
            self._path = path
            self._modified = False
            self._refresh_canvas()
            self._editor.clear()
            self._extras_bar.load(self._data)
            self._val_panel.validate(self._data)
            self.setWindowTitle(f"ImSwitch Config Studio — {Path(path).name}")
            self._status.setText(f"Loaded: {path}")
            # Try to find options file near the loaded config if not yet found
            if not self._options_path:
                self._detect_options_file()
            else:
                self._update_active_banner()
        except Exception as e:
            QMessageBox.critical(self, "Load Error", str(e))

    def _save_file(self):
        if not self._path:
            self._save_as()
            return
        self._write_file(self._path)

    def _save_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Config As", self._path or "", "JSON files (*.json)"
        )
        if path:
            self._write_file(path)

    def _write_file(self, path: str):
        try:
            data_to_write = copy.deepcopy(self._data)
            # Strip empty "others" dict to keep saved JSON clean
            if "others" in data_to_write and not data_to_write["others"]:
                del data_to_write["others"]
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(data_to_write, fh, indent=2, ensure_ascii=False)
            self._path = path
            self._modified = False
            self.setWindowTitle(f"ImSwitch Config Studio — {Path(path).name}")
            self._status.setText(f"Saved: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))

    def _confirm_discard(self) -> bool:
        if not self._modified:
            return True
        r = QMessageBox.question(
            self, "Unsaved Changes",
            "Discard unsaved changes?",
            QMessageBox.Yes | QMessageBox.No,
        )
        return r == QMessageBox.Yes

    # ── Canvas ↔ data ─────────────────────────────────────────────────────
    def _refresh_canvas(self):
        self._canvas.load(self._data)

    def _run_validation(self):
        self._val_panel.validate(self._data)

    def _on_device_selected(self, cat: str, name: str):
        device = (self._data.get(cat) or {}).get(name)
        if device is not None:
            self._editor.load_device(cat, name, device)

    def _on_editor_apply(self, cat: str, name: str, new_device: dict):
        if cat not in self._data or not isinstance(self._data[cat], dict):
            self._data[cat] = {}
        self._data[cat][name] = new_device
        self._modified = True
        self._refresh_canvas()
        self._val_panel.validate(self._data)
        self._status.setText(f"Updated: {name}")
        # Reselect the card
        self._canvas._on_card_clicked(cat, name)

    def _on_device_rename(self, cat: str, old_name: str, new_name: str):
        section = self._data.get(cat)
        if not section or old_name not in section:
            return
        if new_name in section:
            QMessageBox.warning(self, "Rename", f"Name '{new_name}' already exists.")
            return
        section[new_name] = section.pop(old_name)
        self._modified = True
        self._refresh_canvas()
        self._canvas._on_card_clicked(cat, new_name)

    def _on_device_rename_from_canvas(self, cat: str, name: str):
        new_name, ok = QInputDialog.getText(
            self, "Rename Device", "New name:", text=name
        )
        if ok and new_name.strip():
            self._on_device_rename(cat, name, new_name.strip())

    def _on_device_deleted(self, cat: str, name: str):
        if cat == "__ADD__":
            return
        r = QMessageBox.question(
            self, "Delete Device",
            f"Delete '{name}' from {CAT_LABEL.get(cat, cat)}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if r == QMessageBox.Yes:
            section = self._data.get(cat) or {}
            section.pop(name, None)
            self._modified = True
            self._editor.clear()
            self._refresh_canvas()
            self._val_panel.validate(self._data)

    def _on_device_duped_or_add(self, cat_signal: str, name_signal: str):
        # Handle the "Add" path from canvas's internal _request_add
        if cat_signal == "__ADD__":
            parts = name_signal.split("|", 2)
            if len(parts) == 3:
                cat, dev_name, mgr = parts
                if mgr == "__custom__":
                    device = {"managerName": "", "managerProperties": {}}
                else:
                    device = _build_default_device(mgr)
                self._add_device(cat, dev_name, device)
            return
        # Normal duplicate
        section = self._data.get(cat_signal) or {}
        original = section.get(name_signal)
        if original is None:
            return
        base = name_signal + "_copy"
        i = 1
        while base in section:
            base = f"{name_signal}_copy{i}"
            i += 1
        section[base] = copy.deepcopy(original)
        self._modified = True
        self._refresh_canvas()
        self._canvas._on_card_clicked(cat_signal, base)

    def _add_from_template(self, cat: str, device_or_mgr):
        """Slot for LeftPanel.sig_tmpl_add(cat, device_or_mgr).

        device_or_mgr is either a manager name string (builtin template)
        or a device dict (user template).
        """
        if isinstance(device_or_mgr, str):
            tdata = _build_default_device(device_or_mgr)
        else:
            tdata = copy.deepcopy(device_or_mgr)

        name, ok = QInputDialog.getText(
            self, "New Device Name",
            f"Name for new {CAT_LABEL.get(cat, cat)} device:"
        )
        if not ok or not name.strip():
            return
        self._add_device(cat, name.strip(), tdata)

    def _add_device(self, cat: str, name: str, device: dict):
        if cat not in self._data or not isinstance(self._data.get(cat), dict):
            self._data[cat] = {}
        if name in self._data[cat]:
            name = name + "_1"
        self._data[cat][name] = device
        self._modified = True
        self._refresh_canvas()
        self._canvas._on_card_clicked(cat, name)
        self._editor.load_device(cat, name, device)

    def _on_save_template(self, cat: str, name: str):
        device = (self._data.get(cat) or {}).get(name)
        if device is None:
            return
        tname, ok = QInputDialog.getText(
            self, "Save Template", "Template name:", text=name
        )
        if not ok or not tname.strip():
            return
        tname = tname.strip()

        # Ask which category to file this under
        existing = self._left._store.categories()
        # Suggest the device's natural category as default
        default_cat = SCHEMAS.get(device.get("managerName", ""), {}).get("category", cat)
        choices = existing + ["── New Category… ──"]
        default_idx = choices.index(default_cat) if default_cat in choices else 0
        dest_cat, ok2 = QInputDialog.getItem(
            self, "Template Category",
            "Save to category:", choices, default_idx, False
        )
        if not ok2:
            return
        if dest_cat == "── New Category… ──":
            dest_cat, ok3 = QInputDialog.getText(
                self, "New Category", "Category name:"
            )
            if not ok3 or not dest_cat.strip():
                return
            dest_cat = dest_cat.strip()

        self._left.add_user_template(dest_cat, tname, device)
        self._status.setText(f"Template '{tname}' saved to '{dest_cat}'")

    def _on_extras_modified(self):
        self._modified = True
        t = self.windowTitle()
        if not t.endswith(" *"):
            self.setWindowTitle(t + " *")

    # ── Active config / options file ──────────────────────────────────────
    def _detect_options_file(self):
        """Search well-known locations for imcontrol_options.json."""
        candidates = list(self._OPTIONS_SEARCH_ROOTS)
        # Also look next to an already-open config file
        if self._path:
            candidates.insert(0, Path(self._path).parent.parent / "config")
        for root in candidates:
            p = Path(root) / "imcontrol_options.json"
            if p.exists():
                self._options_path = str(p)
                self._active_banner.setVisible(True)
                self._update_active_banner()
                return
        self._active_banner.setVisible(False)

    def _update_active_banner(self):
        if not self._options_path:
            return
        try:
            with open(self._options_path, encoding="utf-8") as fh:
                opts = json.load(fh)
            active = opts.get("setupFileName", "<not set>")
        except Exception:
            active = "<error reading options>"

        is_current = bool(self._path) and Path(self._path).name == active
        mark = "  <span style='color:#5DADE2;'>◀ currently open</span>" if is_current else ""
        self._active_lbl.setText(
            f"<b style='color:#9CC4F0;'>Active config:</b>"
            f"  <span style='color:white;'>{active}</span>{mark}"
            f"  <span style='color:#5A7A9A; font-size:8pt;'>"
            f"({Path(self._options_path).parent})</span>"
        )
        # Disable "Set as Active" if this file is already active or nothing is open
        already_active = is_current or not self._path
        self._set_active_btn.setEnabled(not already_active)
        self._set_active_btn.setToolTip(
            "This file is already the active config" if is_current
            else "Open a config file first" if not self._path
            else f"Set {Path(self._path).name} as the active ImSwitch config"
        )

    def _set_as_active_config(self):
        if not self._path or not self._options_path:
            return
        # Optionally save unsaved changes first
        if self._modified:
            r = QMessageBox.question(
                self, "Unsaved Changes",
                "Save changes before setting as active config?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            )
            if r == QMessageBox.Cancel:
                return
            if r == QMessageBox.Yes:
                self._save_file()

        try:
            with open(self._options_path, encoding="utf-8") as fh:
                opts = json.load(fh)
            opts["setupFileName"] = Path(self._path).name
            with open(self._options_path, "w", encoding="utf-8") as fh:
                json.dump(opts, fh, indent=4, ensure_ascii=False)
            self._update_active_banner()
            self._status.setText(
                f"Active config set to: {Path(self._path).name}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not update options file:\n{e}")

    def closeEvent(self, event):
        if self._modified and not self._confirm_discard():
            event.ignore()
        else:
            event.accept()

def dark_theme(palette): # currently ugly
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.black)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    return palette

# =============================================================================
# Entry point
# =============================================================================
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ImSwitch Config Studio")
    app.setStyle("Fusion")

    # Clean up default palette for a neutral look
    palette = app.palette()
    # palette = dark_theme(palette) # remove this line for light theme
    app.setPalette(palette)

    if len(sys.argv) > 1:
        folder = sys.argv[1]
    else:
        _default = Path.home() / "Documents" / "ImSwitchConfig" / "imcontrol_setups"
        folder = str(_default) if _default.is_dir() else ""
    win = MainWindow(start_folder=folder)
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
