"""PySide2 Maya dialogs and recursive attribute-editor widgets."""

from dataclasses import dataclass, field as dataclass_field

from .node_wrapper import Attr, wrap_node

import maya.cmds as cmds
from PySide2 import QtWidgets
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui


import sys

import re


@dataclass
class AttributeWidget:
    """Attribute editor controls. Add .widget to a Qt layout.

    Leaf editors expose .field; containers expose .children in display order.
    Array editors also expose .add_button and update .children when adding rows.
    """

    attribute: Attr
    widget: QtWidgets.QWidget
    layout: QtWidgets.QLayout
    label: QtWidgets.QLabel | None = None
    field: QtWidgets.QWidget | None = None
    add_button: QtWidgets.QPushButton | None = None
    children: list["AttributeWidget"] = dataclass_field(default_factory=list)


class PandaUIBaseClass(QtWidgets.QDialog):
    """Maya-parented dialog with optional managed script jobs.

    Subclasses must implement create_widget(), create_layout(), and
    create_connections(), called in that order during construction. Set
    state needed by those hooks before calling super().__init__().

    Optionally override create_script_jobs() and use add_script_job().
    The hook runs on first show and after reopening a closed dialog.
    Closing, accepting, rejecting, or destroying removes tracked jobs.
    Hiding alone leaves jobs active."""

    def __init__(self, name: str, parent=None, width:float=None, height:float=None):
        """Build the dialog using name as its object name and window title.

        parent defaults to the Maya main window. Resize only if both width
        and height are supplied; use dimensions accepted by Qt.resize()."""
        super().__init__(maya_main_window() if parent is None else parent)
        self._script_jobs = set()
        self._script_jobs_active = False
        # Capture the registry, not self: destruction may outlive the wrapper.
        jobs = self._script_jobs
        self.destroyed.connect(lambda *_: _clear_script_jobs(jobs))
        self.setObjectName(name)
        self.setWindowTitle(name)
        if width is not None and height is not None:
            self.resize(width, height)
        self.create_widget()
        self.create_layout()
        self.create_connections()

    def create_widget(self):
        """Create the dialog's widgets."""
        raise NotImplementedError("Subclasses must implement create_widget().")

    def create_layout(self):
        """Arrange the widgets in layouts."""
        raise NotImplementedError("Subclasses must implement create_layout().")

    def create_connections(self):
        """Connect widget signals to their handlers."""
        raise NotImplementedError("Subclasses must implement create_connections().")

    def get_selection(self):
        """Return current selection as specialized node wrappers."""
        return [wrap_node(node) for node in cmds.ls(selection=True, long=True)]

    def create_script_jobs(self):
        """Optional hook for registering listeners through add_script_job().

        Does nothing by default. Runs on first show and after a completed
        close, accept, or reject. An override of showEvent must call super().

        Example:
            self.add_script_job(event=["SelectionChanged", self.refresh])"""
        pass

    def add_script_job(self, **kwargs):
        """Create and track a cmds.scriptJob, returning its integer ID.

        Pass creation flags such as event=[event_name, callback] or
        attributeChange=[path, callback]. Permanent and protected jobs are
        rejected. Query, listing, and kill flags are not supported; all supplied
        flags are passed directly to Maya.

        Prefer registering in create_script_jobs() to recreate jobs on reopen.
        Jobs added elsewhere are tracked but not automatically recreated. Maya
        may independently delete one-shot or scene-bound jobs."""
        if any(kwargs.get(flag) for flag in ("permanent", "per", "protected", "pro")):
            raise ValueError("UI script jobs must be removable and unprotected.")
        job_id = cmds.scriptJob(**kwargs)
        if type(job_id) is not int:
            raise ValueError("add_script_job() requires flags that create a job.")
        self._script_jobs.add(job_id)
        return job_id

    def clear_script_jobs(self):
        """Remove tracked jobs, skipping IDs already removed by Maya.

        Does not reset the show lifecycle or immediately recreate listeners."""
        _clear_script_jobs(self._script_jobs)

    def showEvent(self, event):
        """Run the job hook once per open session and clean up if it raises."""
        super().showEvent(event)
        if not self._script_jobs_active:
            try:
                self.create_script_jobs()
            except Exception:
                self.clear_script_jobs()
                raise
            self._script_jobs_active = True

    def closeEvent(self, event):
        """Clean up jobs and reset their lifecycle when Qt accepts the close event."""
        super().closeEvent(event)
        if event.isAccepted():
            self.clear_script_jobs()
            self._script_jobs_active = False

    def done(self, result):
        # QDialog.accept()/reject() (including Escape) also end the UI session.
        """Clean up jobs for accept/reject and finish the dialog with result."""
        self.clear_script_jobs()
        self._script_jobs_active = False
        super().done(result)


def _clear_script_jobs(jobs):
    """Kill existing IDs in the mutable set and discard processed IDs."""
    for job_id in list(jobs):
        if cmds.scriptJob(exists=job_id):
            cmds.scriptJob(kill=job_id)
        jobs.discard(job_id)

def maya_main_window():
    """Return Maya's main window as a wrapped QtWidgets.QWidget."""
    main_window_ptr = omui.MQtUtil.mainWindow()
    if sys.version_info.major >= 3:
        return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)
    else:
        return wrapInstance(long(main_window_ptr), QtWidgets.QWidget)

def run_window(
    object_ui_name: str, ui_class: type[PandaUIBaseClass], parent=None
) -> PandaUIBaseClass:
    """Show and return a PandaUIBaseClass subclass, replacing matching windows.

    Close and schedule deletion of top-level widgets whose objectName()
    matches object_ui_name. ui_class must accept name and parent keywords.
    Keep the returned instance for later interaction."""
    for widget in QtWidgets.QApplication.topLevelWidgets():
        if widget.objectName() == object_ui_name:
            widget.close()
            widget.deleteLater()

    window = ui_class(name=object_ui_name, parent=parent)
    window.show()
    return window

def create_attribute_widget(
    attribute: Attr | str,
    parent:QtWidgets.QWidget=None,
    parent_attr_name:str=None,
    is_connected: bool = False,
) -> AttributeWidget:
    """Build an attribute editor and return its AttributeWidget controls.

    attribute accepts an Attr or node-qualified path; parent is the Qt
    parent. Compounds and arrays recursively expose children. parent_attr_name
    removes a parent name from component labels; is_connected propagates
    incoming-connection highlighting.

    Scalar editors support bool, numeric, angle, distance, time, enum, and
    string values. Edits call Attr.set(); unsettable scalar editors are
    disabled. Unsupported scalar types raise TypeError. Values are read
    at creation; this function does not install scene-change listeners.

    Array + inserts an editor for next_index_attr(). It does not store a
    value or reserve a distinct index until a value is written to Maya."""
    displayed_indices = set()

    def add_to_array(child_layout:QtWidgets.QHBoxLayout):
        """Insert a pending array-element editor before the + button layout."""
        next_index_attr = attribute.next_index_attr()
        child_editor = create_attribute_widget(
            next_index_attr, widget, parent_attr_name, is_connected
        )
        child_layout.insertWidget(child_layout.count() - 1, child_editor.widget)
        result.children.append(child_editor)

    def write_value(value):
        attribute.set(value)
    
    # Attribute checking
    attribute = attribute if isinstance(attribute, Attr) else Attr(attribute)
    attribute_name = [part for part in re.split(r"[.\[\]]", attribute.attr_name) if part][-1]
    attribute_type = attribute.type_

    # See if attribute or ancestors of attribuite has connections
    is_connected = attribute.has_src_connection() or is_connected
    curr_attribute = attribute
    while not is_connected and curr_attribute.parent is not None:
        curr_attribute = curr_attribute.parent
        is_connected = curr_attribute.has_src_connection()

    # recurssive if it has children
    if attribute.has_children():
        widget = QtWidgets.QWidget(parent)
        widget.setToolTip(str(attribute))
        parent_label = QtWidgets.QLabel(attribute_name)

        horizontal = (
            not attribute.plug.isArray
            and attribute_type in {"double2", "double3"}
        )
        parent_layout = QtWidgets.QHBoxLayout() if horizontal else QtWidgets.QVBoxLayout()
        parent_layout.setContentsMargins(0, 0, 0, 0)
        child_layout = QtWidgets.QHBoxLayout() if horizontal else QtWidgets.QVBoxLayout()
        child_layout.setContentsMargins(15, 0, 0, 0)
        result = AttributeWidget(
            attribute=attribute, widget=widget, layout=parent_layout,
            label=parent_label,
        )

        if horizontal:
            parent_attr_name = attribute_name
        for child_attr in attribute:
            child_editor = create_attribute_widget(
                child_attr, widget, parent_attr_name, is_connected
            )
            child_layout.addWidget(child_editor.widget)
            result.children.append(child_editor)
            if attribute.plug.isArray:
                displayed_indices.add(child_attr.index)

        parent_layout.addWidget(parent_label)
        parent_layout.addLayout(child_layout)
        if attribute.plug.isArray:
            child_add_btn = QtWidgets.QPushButton("+")
            result.add_button = child_add_btn
            child_add_btn.setToolTip("Add an element row; write its value to save it in Maya.")
            child_add_btn.clicked.connect(lambda checked=False: add_to_array(child_layout))
            child_form_layout = QtWidgets.QFormLayout()
            child_form_layout.setContentsMargins(0, 0, 0, 0)
            child_form_layout.setHorizontalSpacing(6)
            child_form_layout.setVerticalSpacing(0)
            child_form_layout.addRow("", child_add_btn)
            child_layout.addLayout(child_form_layout)

        widget.setLayout(parent_layout)
        return result

    attribute_value = attribute.value
    supported_types = [
        "bool", "byte", "char", "short", "long", "float", "double",
        "doubleAngle", "doubleLinear", "time", "enum", "string"
    ]
    if attribute_type not in supported_types:
        raise TypeError(f"No attribute widget for {attribute} ({attribute_type}).")

    widget = QtWidgets.QWidget(parent)
    widget.setToolTip(str(attribute))
    layout = QtWidgets.QFormLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setHorizontalSpacing(6)
    layout.setVerticalSpacing(0)
    widget.setLayout(layout)
    form_name = attribute_name.replace(parent_attr_name, "") if parent_attr_name else attribute_name
    
    if re.fullmatch(r"[0-9]+", form_name):
        form_name = f"[{form_name}]"
    if attribute_type == "bool":
        field_widget = QtWidgets.QCheckBox(widget)
        field_widget.setChecked(bool(attribute_value))
        field_widget.toggled.connect(write_value)

    elif attribute_type == "enum":
        field_widget = QtWidgets.QComboBox(widget)
        # Query the attribute definition name, without compound paths or indices.
        enum_names = cmds.attributeQuery(
            attribute.attr_name, node=attribute.node.full_name, listEnum=True
        )[0]
        enum_value = 0
        for item in enum_names.split(":"):
            label, separator, explicit_value = item.partition("=")
            if separator:
                enum_value = int(explicit_value)
            field_widget.addItem(label, enum_value)
            enum_value += 1
        field_widget.setCurrentIndex(field_widget.findData(int(attribute_value)))
        field_widget.currentIndexChanged.connect(
            lambda index: write_value(field_widget.itemData(index))
            if index >= 0 else None
        )

    elif attribute_type == "string":
        field_widget = QtWidgets.QLineEdit(widget)
        field_widget.setText(attribute_value or "")
        field_widget.editingFinished.connect(
            lambda: write_value(field_widget.text())
        )

    elif attribute_type in {"byte", "char", "short", "long"}:
        field_widget = QtWidgets.QSpinBox(widget)
        field_widget.setRange(-2147483648, 2147483647)
        field_widget.setValue(int(attribute_value))
        field_widget.setKeyboardTracking(False)
        field_widget.valueChanged.connect(write_value)

    else:
        # float, double, doubleAngle, doubleLinear, and time.
        field_widget = QtWidgets.QDoubleSpinBox(widget)
        field_widget.setRange(-1e100, 1e100)
        field_widget.setDecimals(3)
        field_widget.setSingleStep(0.1)
        field_widget.setValue(attribute_value)
        field_widget.setKeyboardTracking(False)
        field_widget.valueChanged.connect(write_value)

    if is_connected:
        field_widget.setStyleSheet("background-color: #f1f1a5")
    layout.addRow(form_name, field_widget)
    
    widget.setEnabled(bool(cmds.getAttr(str(attribute), settable=True)))
    return AttributeWidget(
        attribute=attribute, widget=widget, layout=layout,
        label=layout.labelForField(field_widget), field=field_widget,
    )

def create_separator():
    """Return a sunken horizontal QFrame for insertion into a Qt layout."""
    separator = QtWidgets.QFrame()
    separator.setFrameShape(QtWidgets.QFrame.HLine)
    separator.setFrameShadow(QtWidgets.QFrame.Sunken)

    return separator
