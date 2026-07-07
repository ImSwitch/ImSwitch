"""Generic parameter editors driven by ParamDef.

ParamDef stores the converter *class*. Each ParamField creates a temporary
converter using the calibration of its own SLM section, so calibration state is
never shared through the registry.
"""

from __future__ import annotations
from qtpy import QtCore, QtGui, QtWidgets
from typing import (
    Any, 
    Callable, 
    Dict, 
    Iterable, 
    Optional, 
    Sequence, 
    TYPE_CHECKING
)

if TYPE_CHECKING:
    from imswitch.imcontrol.controller.patterndesigners.paramDef import ParamDef

PIXEL_MODE = "pixels"
METRIC_MODE = "metric"
_VALID_UNIT_MODES = (PIXEL_MODE, METRIC_MODE)


class ParamField(QtWidgets.QWidget):
    """Runtime editor for one ParamDef.

    The field always stores a validated canonical value in SLM/pixel units.
    Metric mode only changes how this canonical value is displayed and edited.
    """

    sigValueChanged = QtCore.Signal(str, object)  # key, canonical value
    sigValidityChanged = QtCore.Signal(str, bool, str)  # key, valid, message

    _INVALID_STYLE = "QLineEdit { border: 1px solid #c44; }"

    def __init__(
        self,
        definition: ParamDef,
        calibration_provider: Optional[Callable[[], Any]] = None,
        parent: Optional[QtWidgets.QWidget] = None,
        editor_width: int = 70,
        show_complementary: bool = False,
    ):
        super().__init__(parent)

        self.definition = definition
        self._calibration_provider = calibration_provider or (lambda: None)
        self._unit_mode = PIXEL_MODE
        self._canonical_value = definition.validate(definition.default)
        self._last_error = ""
        self._show_complementary = bool(show_complementary)
        self._updating_editor = False

        self.label = QtWidgets.QLabel()
        self.editor = self._create_editor(editor_width)
        self.complementaryLabel = QtWidgets.QLabel()
        self.complementaryLabel.setStyleSheet("color: #888;")
        self.complementaryLabel.setVisible(self._show_complementary)

        self._connect_editor()
        self._render()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def key(self) -> str:
        return self.definition.key

    @property
    def unit_mode(self) -> str:
        return self._unit_mode

    def value(self) -> Any:
        """Return the canonical validated value."""
        return self._canonical_value

    def set_value(self, value: Any, emit: bool = False) -> None:
        """Set a canonical value, normally from a config or model."""
        canonical = self.definition.validate(value)
        changed = canonical != self._canonical_value
        self._canonical_value = canonical
        self._set_valid(True, "")
        self._render()

        if emit and changed:
            self.sigValueChanged.emit(self.key, canonical)

    def set_unit_mode(self, mode: str) -> None:
        """Switch display mode without changing the canonical value."""
        if mode not in _VALID_UNIT_MODES:
            raise ValueError("Unknown unit mode: {}".format(mode))

        if mode == METRIC_MODE and self.definition.metric_available:
            self._require_calibration()

        self._unit_mode = mode
        self._render()

    def refresh(self) -> None:
        """Refresh after calibration/context changes."""
        self._render()
    
    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def add_to_grid(self,layout: QtWidgets.QGridLayout,row: int,column: int) -> int:
        """Add this field directly to a shared parent grid.

        Returns the next available column.
        """

        if self.definition.hidden:
            self.label.hide()
            self.editor.hide()
            self.complementaryLabel.hide()
            return column

        if isinstance(self.editor, QtWidgets.QCheckBox):
            layout.addWidget(self.editor,row,column,1,1,
                             alignment=QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            return column + 1

        layout.addWidget(self.label,row,column,1,1,
                         alignment=QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        layout.addWidget(self.editor,row,column + 1,1,1,
                         alignment=QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        next_column = column + 2

        if self.add_to_grid:
            layout.addWidget(self.complementaryLabel,row,next_column,1,1,
                             alignment=QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            next_column += 1

        return next_column

    def _create_editor(self, editor_width: int) -> QtWidgets.QWidget:
        editor_type = getattr(self.definition, "editor_type", None)
        if callable(editor_type):
            editor_type = editor_type()
        if not editor_type:
            editor_type = getattr(self.definition, "widget", None)
        if not editor_type:
            if self.definition.ptype is bool:
                editor_type = "checkbox"
            elif self.definition.choices is not None:
                editor_type = "combo"
            else:
                editor_type = "lineedit"

        editor_type = str(editor_type).lower()

        if editor_type == "checkbox":
            editor = QtWidgets.QCheckBox(self.definition.display_label)

        elif editor_type in ("combo", "combobox"):
            editor = QtWidgets.QComboBox()
            for value, label in zip(
                self.definition.choices or (),
                self.definition.display_choices,
            ):
                editor.addItem(label, value)
            editor.setMinimumWidth(editor_width)

        elif editor_type in ("spinbox", "int_spinbox"):
            # A metric representation can be fractional even when the canonical
            # pixel value is int. Therefore metric-capable parameters use a
            # QDoubleSpinBox in both modes.
            if self.definition.metric_available:
                editor = QtWidgets.QDoubleSpinBox()
                editor.setDecimals(6)
            else:
                editor = QtWidgets.QSpinBox()
            editor.setKeyboardTracking(False)
            editor.setMinimumWidth(editor_width)

        elif editor_type in ("double_spinbox", "doublespinbox"):
            editor = QtWidgets.QDoubleSpinBox()
            editor.setDecimals(6)
            editor.setKeyboardTracking(False)
            editor.setMinimumWidth(editor_width)

        else:
            editor = QtWidgets.QLineEdit()
            editor.setFixedWidth(editor_width)
            editor.setAlignment(QtCore.Qt.AlignRight)

        if self.definition.tooltip:
            self.setToolTip(self.definition.tooltip)
            editor.setToolTip(self.definition.tooltip)

        return editor

    def _build_layout(self) -> None:
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        if isinstance(self.editor, QtWidgets.QCheckBox):
            self.label.hide()
            layout.addWidget(self.editor)
        else:
            layout.addWidget(self.label)
            layout.addWidget(self.editor)
            layout.addWidget(self.complementaryLabel)

        layout.addStretch(1)

    def _connect_editor(self) -> None:
        if isinstance(self.editor, QtWidgets.QLineEdit):
            self.editor.textEdited.connect(self._try_commit_editor)
            self.editor.editingFinished.connect(self._finish_line_edit)

        elif isinstance(self.editor, QtWidgets.QCheckBox):
            self.editor.toggled.connect(self._commit_editor)

        elif isinstance(self.editor, QtWidgets.QComboBox):
            self.editor.currentIndexChanged.connect(self._commit_editor)

        elif isinstance(
            self.editor,
            (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox),
        ):
            self.editor.valueChanged.connect(self._commit_editor)


    def _on_editor_changed(self, *args):
        if isinstance(self.editor, QtWidgets.QLineEdit):
            text = self.editor.text()

            if text.strip() == "":
                return

        try:
            displayed_value = self._read_editor()
            canonical_value = self._to_canonical(displayed_value)
        except (TypeError, ValueError):
            return

        if canonical_value == self._canonical_value:
            return

        self._canonical_value = canonical_value
        self.sigValueChanged.emit(
            self.definition.key,
            canonical_value,
        )

        self._update_complementary_label()

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    def _calibration(self) -> Any:
        return self._calibration_provider()

    def _require_calibration(self) -> Any:
        calibration = self._calibration()
        if calibration is None:
            raise RuntimeError(
                "{} requires a valid section calibration in metric mode".format(
                    self.key
                )
            )
        return calibration

    def _converter(self) -> Any:
        converter = self.definition.converter

        if converter is None:
            raise RuntimeError(
                f"{self.definition.key} has no metric converter"
            )

        if isinstance(converter, type):
            raise TypeError(
                f"{self.definition.key}: converter must be an initialized "
                f"converter instance, for example "
                f"PeriodDisplacementConverter(axis='x')"
            )

        return converter


    def _call_converter(
        self,
        method_name: str,
        value: Any,
    ) -> Any:
        calibration = self._require_calibration()
        converter = self._converter()
        method = getattr(converter, method_name)

        return method(value, calibration)


    def _to_metric(self, canonical_value: Any) -> Any:
        return self._call_converter(
            "to_metric",
            canonical_value,
        )


    def _to_canonical(self, displayed_value: Any) -> Any:
        if (
            self._unit_mode == METRIC_MODE
            and self.definition.metric_available
        ):
            displayed_value = self._call_converter(
                "to_slm",
                displayed_value,
            )

        return self.definition.validate(displayed_value)

    # ------------------------------------------------------------------
    # Editor reading/writing
    # ------------------------------------------------------------------

    def _read_editor(self) -> Any:
        if isinstance(self.editor, QtWidgets.QCheckBox):
            return self.editor.isChecked()

        if isinstance(self.editor, QtWidgets.QComboBox):
            value = self.editor.currentData()
            return self.editor.currentText() if value is None else value

        if isinstance(
            self.editor,
            (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox),
        ):
            return self.editor.value()

        text = self.editor.text().strip().replace(",", ".")
        if text == "":
            if self.definition.allow_none:
                return None
            raise ValueError("{} cannot be empty".format(self.key))

        # Metric values are generally floating point even if canonical pixels
        # are ints. ParamDef.validate() performs the canonical type conversion
        # after the converter has run.
        if self._unit_mode == METRIC_MODE and self.definition.metric_available:
            return float(text)

        if self.definition.ptype is int:
            return int(text)
        if self.definition.ptype is float:
            return float(text)
        return self.definition.ptype(text)

    def _write_editor(self, displayed_value: Any) -> None:
        self._updating_editor = True
        try:
            blocker = QtCore.QSignalBlocker(self.editor)
            try:
                if isinstance(self.editor, QtWidgets.QCheckBox):
                    self.editor.setChecked(bool(displayed_value))

                elif isinstance(self.editor, QtWidgets.QComboBox):
                    index = self.editor.findData(displayed_value)
                    if index < 0:
                        index = self.editor.findText(str(displayed_value))
                    if index >= 0:
                        self.editor.setCurrentIndex(index)

                elif isinstance(self.editor, QtWidgets.QSpinBox):
                    self.editor.setValue(int(displayed_value))

                elif isinstance(self.editor, QtWidgets.QDoubleSpinBox):
                    self.editor.setValue(float(displayed_value))

                else:
                    self.editor.setText(self._format_value(displayed_value))
            finally:
                del blocker
        finally:
            self._updating_editor = False

    @staticmethod
    def _format_value(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, float):
            return "{:.8g}".format(value)
        return str(value)

    # ------------------------------------------------------------------
    # Validation and rendering
    # ------------------------------------------------------------------

    def _try_commit_editor(self, *_args: Any) -> None:
        try:
            self._commit_editor()
        except Exception:
            # _commit_editor already updates visual validity. Partial text such
            # as '-' should simply remain editable until editing is finished.
            pass

    def _commit_editor(self, *_args: Any) -> None:
        if self._updating_editor:
            return

        try:
            displayed = self._read_editor()
            canonical = self._to_canonical(displayed)
        except Exception as error:
            self._set_valid(False, str(error))
            raise

        changed = canonical != self._canonical_value
        self._canonical_value = canonical
        self._set_valid(True, "")
        self._update_complementary_label()

        if changed:
            self.sigValueChanged.emit(self.key, canonical)

    def _finish_line_edit(self) -> None:
        try:
            self._commit_editor()
        except Exception:
            # Restore the last valid canonical value.
            self._render()

    def _set_valid(self, valid: bool, message: str) -> None:
        self._last_error = message

        if isinstance(self.editor, QtWidgets.QLineEdit):
            self.editor.setStyleSheet("" if valid else self._INVALID_STYLE)

        self.editor.setToolTip(message or self.definition.tooltip or "")
        self.sigValidityChanged.emit(self.key, valid, message)

    def _render(self) -> None:
        if self.definition.hidden:
            self.label.hide()
            self.editor.hide()
            self.complementaryLabel.hide()
            return
        
        metric_display = (
            self._unit_mode == METRIC_MODE
            and self.definition.metric_available
        )

        if metric_display:
            displayed_value = self._to_metric(self._canonical_value)
            label = self.definition.metric_label or self.definition.display_label
        else:
            displayed_value = self._canonical_value
            label = self.definition.display_label

        if not isinstance(self.editor, QtWidgets.QCheckBox):
            self.label.setText("{}:".format(label))

        self._apply_spinbox_constraints()
        self._write_editor(displayed_value)
        self._update_complementary_label()

    def _apply_spinbox_constraints(self) -> None:
        if not isinstance(
            self.editor,
            (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox),
        ):
            return

        pdef = self.definition

        if self._unit_mode == PIXEL_MODE or not pdef.metric_available:
            minimum = pdef.min_value
            maximum = pdef.max_value
            step = pdef.step
        else:
            # Canonical validation remains the source of truth. These converted
            # limits only improve spinbox UX. Sorting handles decreasing
            # conversions such as period <-> displacement.
            converted = []
            for boundary in (pdef.min_value, pdef.max_value):
                if boundary is None:
                    converted.append(None)
                else:
                    try:
                        converted.append(float(self._to_metric(boundary)))
                    except Exception:
                        converted.append(None)

            valid_boundaries = [v for v in converted if v is not None]
            minimum = min(valid_boundaries) if valid_boundaries else None
            maximum = max(valid_boundaries) if valid_boundaries else None
            step = None  # A canonical step is not generally constant in metric space.

        if isinstance(self.editor, QtWidgets.QSpinBox):
            low_default, high_default = -2147483647, 2147483647
            if minimum is not None:
                self.editor.setMinimum(int(minimum))
            else:
                self.editor.setMinimum(low_default)
            if maximum is not None:
                self.editor.setMaximum(int(maximum))
            else:
                self.editor.setMaximum(high_default)
            if step is not None:
                self.editor.setSingleStep(max(1, int(step)))

        else:
            low_default, high_default = -1e100, 1e100
            self.editor.setMinimum(
                float(minimum) if minimum is not None else low_default
            )
            self.editor.setMaximum(
                float(maximum) if maximum is not None else high_default
            )
            if step is not None:
                self.editor.setSingleStep(float(step))

            if self._unit_mode == PIXEL_MODE and pdef.ptype is int:
                self.editor.setDecimals(0)
            else:
                self.editor.setDecimals(6)

    def _update_complementary_label(self) -> None:
        if not self._show_complementary or not self.definition.metric_available:
            self.complementaryLabel.hide()
            return

        try:
            if self._unit_mode == METRIC_MODE:
                text = "({}: {})".format(
                    self.definition.display_label,
                    self._format_value(self._canonical_value),
                )
            else:
                metric_value = self._to_metric(self._canonical_value)
                text = "({}: {})".format(
                    self.definition.metric_label or "Metric",
                    self._format_value(metric_value),
                )
            self.complementaryLabel.setText(text)
            self.complementaryLabel.show()
        except Exception:
            self.complementaryLabel.setText("(metric unavailable)")
            self.complementaryLabel.show()


class ParamForm(QtCore.QObject):
    """Collection of ParamFields for one pattern, target, or flat group."""

    sigValueChanged = QtCore.Signal(str, object) #key, value

    def __init__(
        self,
        name: str,
        definitions: Sequence[ParamDef],
        calibration_provider: Optional[Callable[[], Any]] = None,
        parent: Optional[QtWidgets.QWidget] = None,
        per_row: int = 1,
        use_subsection: bool = True,
        editor_width: int = 70,
        show_complementary: bool = False,
    ):
        super().__init__(parent)

        self.name = name
        self.use_subsection = bool(use_subsection)
        self._unit_mode = PIXEL_MODE
        self._fields: Dict[str, ParamField] = {}
        self._per_row = max(1, int(per_row))

        for definition in definitions:
            field = ParamField(
                definition=definition,
                calibration_provider=calibration_provider,
                parent=None,
                editor_width=editor_width,
                show_complementary=show_complementary,
            )

            self._fields[definition.key] = field
            field.sigValueChanged.connect(self.sigValueChanged)

    @property
    def fields(self) -> Dict[str, ParamField]:
        return self._fields

    def field(self, key: str) -> ParamField:
        return self._fields[key]

    def values(self) -> Dict[str, Any]:
        return {key: field.value() for key, field in self._fields.items()}

    def set_values(self, values: Dict[str, Any], emit: bool = False) -> None:
        for key, value in values.items():
            field = self._fields.get(key)
            if field is not None:
                field.set_value(value, emit=emit)

    def set_unit_mode(self, mode: str) -> None:
        # Render every field through the same API. Non-metric fields simply keep
        # their normal representation.
        for field in self._fields.values():
            field.set_unit_mode(mode)
        self._unit_mode = mode

    def refresh(self) -> None:
        """Refresh fields whose display depends on calibration."""
        for field in self._fields.values():
            if field.definition.metric_available:
                field.refresh()

    def canonical_definitions(self) -> Iterable[ParamDef]:
        for field in self._fields.values():
            yield field.definition

    # def add_to_grid(self,layout: QtWidgets.QGridLayout,start_row: int) -> int:
    #     """Insert all fields into an existing shared grid.
    #     Returns the next unused row.
    #     """

    #     visible_fields = [
    #         field
    #         for field in self._fields.values()
    #         if not field.definition.hidden
    #     ]

    #     if not visible_fields:
    #         return start_row

    #     row = start_row
    #     column = 0
    #     fields_in_row = 0

    #     for field in visible_fields:
    #         if fields_in_row >= self._per_row:
    #             row += 1
    #             column = 0
    #             fields_in_row = 0

    #         column = field.add_to_grid(layout=layout,row=row,column=column)

    #         fields_in_row += 1

    #     return row + 1

    def add_to_grid(
        self,
        layout: QtWidgets.QGridLayout,
        start_row: int,
        layout_spec: Optional[Sequence[Sequence[str]]] = None,
        ) -> int:
        """
        Insert all visible fields into an existing shared grid.

        Parameters
        ----------
        layout:
            Grid layout receiving the field widgets.
        start_row:
            First available row in the layout.
        layout_spec:
            Optional explicit arrangement of parameter keys.
            When omitted, the existing automatic layout based on
            ``self._per_row`` is used unchanged.

            Fields omitted from the specification are appended afterwards
            using the normal automatic layout.

        Returns
        -------
        int
            Next unused layout row.
        """

        visible_fields = [
            field
            for field in self._fields.values()
            if not field.definition.hidden
        ]

        if not visible_fields:
            return start_row

        # -----------------------
        # Normal automatic layout
        # -----------------------
        if layout_spec is None:
            row = start_row
            column = 0
            fields_in_row = 0

            for field in visible_fields:
                if fields_in_row >= self._per_row:
                    row += 1
                    column = 0
                    fields_in_row = 0

                column = field.add_to_grid(
                    layout=layout,
                    row=row,
                    column=column,
                )

                fields_in_row += 1

            return row + 1

        # ------------------------------
        # Explicit layout specification.
        # ------------------------------
        visible_by_key = {
            field.definition.key: field
            for field in visible_fields
        }

        specified_keys = set()
        row = start_row

        for spec_row in layout_spec:
            column = 0
            row_has_fields = False

            for key in spec_row:
                if key not in self._fields:
                    raise KeyError(
                        f"Unknown parameter '{key}' in layout specification "
                        f"for form '{self.name}'."
                    )

                if key in specified_keys:
                    raise ValueError(
                        f"Parameter '{key}' appears more than once in the "
                        f"layout specification for form '{self.name}'."
                    )

                specified_keys.add(key)

                # The field exists but is hidden: do not place it.
                field = visible_by_key.get(key)
                if field is None:
                    continue

                column = field.add_to_grid(
                    layout=layout,
                    row=row,
                    column=column,
                )
                row_has_fields = True

            if row_has_fields:
                row += 1

        # ----------------------------------------------------
        # Append any visible fields omitted from layout_spec.
        # This prevents parameters from silently disappearing.
        # ----------------------------------------------------
        remaining_fields = [
            field
            for field in visible_fields
            if field.definition.key not in specified_keys
        ]

        if not remaining_fields:
            return row

        column = 0
        fields_in_row = 0

        for field in remaining_fields:
            if fields_in_row >= self._per_row:
                row += 1
                column = 0
                fields_in_row = 0

            column = field.add_to_grid(
                layout=layout,
                row=row,
                column=column,
            )

            fields_in_row += 1

        return row + 1