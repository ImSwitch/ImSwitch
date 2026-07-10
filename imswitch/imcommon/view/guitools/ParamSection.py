from numbers import Number
from typing import Any, Dict, Optional, Sequence, Tuple

from qtpy import QtCore, QtWidgets

from . import CollapsibleSection, ParamForm, ParamField, ElidedLabel

from imswitch.imcommon.model.paramDef import(
    ParamDef,
    as_param_def,
    make_display_name,
    param,
)

SECTION_META_KEY = "_section"
SECTION_ACTIVE_KEY = "active"

class ParamSection(QtCore.QObject):
    """
    Manage one collapsible parameter section.

    Responsibilities:
        - CollapsibleSection construction
        - optional section-level active ParamField
        - built-in "In use:" summary
        - ParamForm creation and storage
        - standard shared-grid mounting
        - section-level value-change signal

    """

    sigValueChanged = QtCore.Signal(str, str, object) # form_name, parameter_key, canonical_value

    sigActiveChanged = QtCore.Signal(bool)

    VALID_SUMMARY_MODES = {
        "none",
        "active_forms",
        "nonzero_fields",
        "enabled_fields",
        "runtime_value",
    }

    def __init__(
        self,
        name: str,
        title: str,
        active_def: Optional[ParamDef] = None,
        section_definitions: Optional[Sequence[ParamDef]] = None,
        summary_mode: str = "none",
        summary_prefix: str = "In use:",
        summary_max_width: int = 220,
        conversion_context=None,
        collapsible_kwargs: Optional[dict] = None,
        horizontal_spacing: int = 10,
        vertical_spacing: int = 4,
    ):
        if summary_mode not in self.VALID_SUMMARY_MODES:
            raise ValueError(
                f"Unknown summary mode '{summary_mode}'. "
                f"Expected one of {sorted(self.VALID_SUMMARY_MODES)}."
            )

        collapsible_kwargs = dict(collapsible_kwargs or {})
        widget = CollapsibleSection(title, **collapsible_kwargs)

        # ParamSection is destroyed with its visible section.
        super().__init__(widget)

        self.name = name
        self.widget = widget
        self.summary_mode = summary_mode

        self._conversion_context = conversion_context
        self._forms: Dict[str, ParamForm] = {}
        self._form_definitions: Dict[str, Tuple[ParamDef, ...]] = {}
        self._form_labels: Dict[str, str] = {}

        self._runtime_summary: Any = None
        self._next_row = 0

        # Standard content layout.
        self.layout = QtWidgets.QGridLayout()
        self.layout.setHorizontalSpacing(horizontal_spacing)
        self.layout.setVerticalSpacing(vertical_spacing)

        self.widget.setContentLayout(self.layout)

        # Section-level metadata stored under the reserved "_section" key.
        self.general_form: Optional[ParamForm] = None
        self.active_field: Optional[ParamField] = None
        
        metadata_definitions = [
            as_param_def(definition) for definition in (section_definitions or [])
        ]

        # "active" has dedicated behavior and must be supplied through active_def.
        if any(
            definition.key == SECTION_ACTIVE_KEY for definition in metadata_definitions
        ):
            raise ValueError(
                f"Section metadata key '{SECTION_ACTIVE_KEY}' must be provided through "
                f"active_def, not section_definitions."
            )

        if active_def is not None:
            active_def = as_param_def(active_def)
            if active_def.key != SECTION_ACTIVE_KEY:
                raise ValueError(
                    f"ParamSection active parameter must use the key '{SECTION_ACTIVE_KEY}'."
                )
            metadata_definitions.insert(0, active_def)

        if metadata_definitions:
            self.general_form = ParamForm(
                name=SECTION_META_KEY,
                definitions=metadata_definitions,
                conversion_context=conversion_context,
                parent=self.widget,
                per_row=1,
                use_subsection=True,
                editor_width=60,
                show_complementary=False,
            )

            # Only the active control is mounted automatically in the header.
            if active_def is not None:
                self.active_field = self.general_form.field("active")
                self.widget.addHeaderWidget(self.active_field.editor)

            form_name = self.general_form.name
            self.general_form.sigValueChanged.connect(
                lambda key, value, name=form_name: self._on_form_value_changed(name, key, value)
            )

        # Standard summary header.
        self.summary_prefix_label: Optional[QtWidgets.QLabel] = None
        self.summary_label: Optional[ElidedLabel] = None

        if summary_mode != "none":
            self.summary_prefix_label = QtWidgets.QLabel(summary_prefix)
            self.summary_label = ElidedLabel("None")
            self.summary_label.setMaximumWidth(summary_max_width)
            self.summary_label.setStyleSheet("color: #888;")

            self.widget.addHeaderWidget(self.summary_prefix_label)
            self.widget.addHeaderWidget(self.summary_label)

        self.refresh_summary()

    # ------------------------------------------------------------------
    # Form construction
    # ------------------------------------------------------------------

    def add_form(
        self,
        name: str,
        definitions: Sequence[ParamDef],
        *,
        add_active_field: bool = False,
        active_default: bool = False,
        use_subsection: bool = True,
        per_row: int = 1,
        editor_width: int = 60,
        show_complementary: bool = False,
        mount: bool = True,
        layout_spec: Optional[Sequence[Sequence[str]]] = None,
    ) -> ParamForm:
        """
        Create, store and optionally mount one ParamForm.

        For pattern-like forms, ``add_active_field=True`` automatically adds:

            param("active", False, bool, make_display_name(name))
        """
        if name == SECTION_META_KEY:
            raise ValueError(f"'{SECTION_META_KEY}' is reserved for section metadata.")

        if name in self._forms:
            raise KeyError(
                f"Form '{name}' is already registered in section '{self.name}'."
            )

        normalized_defs = [
            as_param_def(definition)
            for definition in definitions
        ]

        if add_active_field:
            has_active = any(definition.key == "active" for definition in normalized_defs)

            if not has_active:
                normalized_defs.insert(
                    0,
                    param("active",active_default,bool,make_display_name(name)),
                )

        form = ParamForm(
            name=name,
            definitions=normalized_defs,
            conversion_context=self._conversion_context,
            parent=self.widget,
            per_row=per_row,
            use_subsection=use_subsection,
            editor_width=editor_width,
            show_complementary=show_complementary,
        )

        self._forms[name] = form
        self._form_definitions[name] = tuple(normalized_defs)
        self._form_labels[name] = make_display_name(name)

        form.sigValueChanged.connect(
            lambda key, value, form_name=name: self._on_form_value_changed(form_name, key, value)
        )

        if mount:
            self._next_row = form.add_to_grid(
                layout=self.layout,start_row=self._next_row,layout_spec=layout_spec,
            )

        self.refresh_summary()
        return form

    # ------------------------------------------------------------------
    # Access
    # ------------------------------------------------------------------

    @property
    def forms(self) -> Tuple[ParamForm, ...]:
        """Return the general form followed by all regular forms."""

        forms = []

        if self.general_form is not None:
            forms.append(self.general_form)

        forms.extend(self._forms.values())
        return tuple(forms)

    @property
    def next_row(self) -> int:
        return self._next_row

    def form(self, name: str) -> ParamForm:
        if self.general_form is not None and self.general_form.name == name:
            return self.general_form

        return self._forms[name]

    def section_field(self, key: str) -> ParamField:
        """
        Return a field stored in the reserved ``_section`` form.
        """
        if self.general_form is None:
            raise KeyError(f"Section '{self.name}' has no section metadata.")
        return self.general_form.field(key)


    def is_active(self) -> bool:
        if self.active_field is None:
            return True

        return bool(self.active_field.value())

    def set_active(self, active: bool, emit: bool = False) -> None:
        if self.active_field is None:
            return

        self.active_field.set_value(active, emit=emit)
        self.refresh_summary()

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def set_summary_value(self, value: Any) -> None:
        """
        Set the summary used by ``summary_mode="runtime_value"``.

        Examples:
            section.set_summary_value("multi_foci_31x31")
            section.set_summary_value(["Correction bitmap", "2π correction"])
        """

        self._runtime_summary = value
        self.refresh_summary()

    def refresh_summary(self) -> None:
        if self.summary_label is None:
            return

        if not self.is_active():
            summary = "None"
        else:
            items = self._build_summary_items()
            summary = ", ".join(items) if items else "None"

        self.summary_label.set_full_text(summary)

    def _build_summary_items(self) -> list:
        if self.summary_mode == "none":
            return []

        if self.summary_mode == "runtime_value":
            value = self._runtime_summary

            if value is None:
                return []

            if isinstance(value, (list, tuple, set)):
                return [
                    str(item)
                    for item in value
                    if item not in (None, "")
                ]

            return [str(value)] if value != "" else []

        if self.summary_mode == "active_forms":
            items = []

            for name, form in self._forms.items():
                values = form.values()

                if bool(values.get("active", False)):
                    items.append(self._form_labels[name])

            return items

        if self.summary_mode == "enabled_fields":
            items = []

            for name, form in self._forms.items():
                values = form.values()

                for definition in self._form_definitions[name]:
                    if definition.key == "active":
                        continue

                    value = values.get(definition.key)

                    if definition.ptype is bool and bool(value):
                        items.append(definition.display_label)

            return items

        if self.summary_mode == "nonzero_fields":
            items = []

            for name, form in self._forms.items():
                values = form.values()

                for definition in self._form_definitions[name]:
                    value = values.get(definition.key)

                    if (
                        isinstance(value, Number)
                        and not isinstance(value, bool)
                        and value != 0
                    ):
                        items.append(definition.display_label)

            return items

        return []

    # ------------------------------------------------------------------
    # Values
    # ------------------------------------------------------------------

    def values(self) -> Dict[str, Any]:
        """
        Gather values using the same subsection rules as SLMsWidget.
        """

        result: Dict[str, Any] = {}

        for form in self.forms:
            values = form.values()

            if form.use_subsection:
                result[form.name] = values
            else:
                result.update(values)

        return result

    def set_values(self,values: Dict[str, Any], emit: bool = False) -> None:
        for form in self.forms:
            if form.use_subsection:
                form_values = values.get(form.name, {})
            else:
                form_values = values

            if isinstance(form_values, dict):
                form.set_values(form_values, emit=emit)

        self.refresh_summary()

    def set_unit_mode(self, mode: str) -> None:
        for form in self.forms:
            form.set_unit_mode(mode)

    def refresh(self) -> None:
        for form in self.forms:
            form.refresh()

        self.refresh_summary()

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    def _on_form_value_changed(
        self,
        form_name: str,
        key: str,
        value: Any,
    ) -> None:
        self.refresh_summary()

        if (
            self.general_form is not None
            and form_name == self.general_form.name
            and self.active_field is not None
            and key == self.active_field.definition.key
        ):
            self.sigActiveChanged.emit(bool(value))

        self.sigValueChanged.emit(form_name, key, value)