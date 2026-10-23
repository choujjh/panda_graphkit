from dataclasses import dataclass, field as dataclass_field

from .node_wrapper import Attr, wrap_node

import maya.cmds as cmds
from PySide2 import QtWidgets
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui


import sys

import re


class PandaUIBaseClass(QtWidgets.QDialog):
    """Maya-parented dialog that builds widgets, layout, then connections.

    Subclasses must implement all three creation methods. Initialize any
    state they need before calling this constructor.
    """

    def __init__(
        self, name: str, parent=None, width: float = None, height: float = None
    ):
        super().__init__(maya_main_window() if parent is None else parent)
        self.setObjectName(name)
        self.setWindowTitle(name)
        if width is not None and height is not None:
            self.resize(width, height)
        # Script Jobs
        self.script_jobs = ScriptJobManager()
        self._script_jobs_active = False
        self.destroyed.connect(self.script_jobs.clear)

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

    def create_script_jobs(self):
        pass

    def get_selection(self):
        return [wrap_node(node) for node in cmds.ls(sl=True, long=True)]

    def showEvent(self, event):
        super().showEvent(event)

        if not self._script_jobs_active:
            try:
                self.create_script_jobs()
            except Exception:
                self.script_jobs.clear()
                raise

            self._script_jobs_active = True

    def closeEvent(self, event):
        self.script_jobs.clear()
        self._script_jobs_active = False
        super().closeEvent(event)

    def done(self, result):
        self.script_jobs.clear()
        self._script_jobs_active = False
        super().done(result)


def maya_main_window():
    """
    Return the Maya main window widget as a Python object
    """
    main_window_ptr = omui.MQtUtil.mainWindow()
    if sys.version_info.major >= 3:
        return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)
    else:
        return wrapInstance(long(main_window_ptr), QtWidgets.QWidget)


def run_window(
    object_ui_name: str, ui_class: type[PandaUIBaseClass], parent=None
) -> PandaUIBaseClass:
    """Show a PandaUIBaseClass subclass, replacing windows with the same name.

    The subclass constructor must accept name and parent keyword arguments.
    """
    for widget in QtWidgets.QApplication.topLevelWidgets():
        if widget.objectName() == object_ui_name:
            widget.close()
            widget.deleteLater()

    window = ui_class(name=object_ui_name, parent=parent)
    window.show()
    return window


class ScriptJobManager:
    def __init__(self):
        self._jobs = set()

    def add(self, **kwargs):
        if any(kwargs.get(flag) for flag in ("permanent", "per", "protected", "pro")):
            raise ValueError("Managed Jobs must be removable")

        job_id = cmds.scriptJob(**kwargs)
        self._jobs.add(job_id)

        return job_id

    def on_selection_change(self, callback):
        return self.add(event=["SelectionChanged", callback])

    def on_attribute_change(self, attribute, callback, **kwargs):
        return self.add(attributeChange=[str(attribute), callback], **kwargs)

    def on_connection_changed(self, attribute, callback):
        return self.add(connectionChange=[str(attribute), callback])

    def clear(self):
        for job_id in tuple(self._jobs):
            if cmds.scriptJob(exists=job_id):
                cmds.scriptJob(kill=job_id)
            self._jobs.discard(job_id)


class AttributeWidget(QtWidgets.QWidget):
    def __init__(
        self,
        attribute: Attr | str,
        parent=None,
        parent_attr_name=None,
        is_connected=False,
        watch_changes=False,
    ):
        super().__init__(parent)
        self.attribute = attribute if isinstance(attribute, Attr) else Attr(attribute)
        self.parent_attr_name = parent_attr_name
        self.is_connected = is_connected

        self.script_jobs = ScriptJobManager()
        self.destroyed.connect(self.script_jobs.clear)
        self.watch_changes = watch_changes
        self.supported_type = False

        self._attr_is_array = (
            self.attribute.has_children() and self.attribute.plug.isArray
        )
        self._is_double_compound_attr = self.attribute.type_ in ["double2", "double3"]

        self.field = None
        self.add_button = None
        self.delete_button = None
        self.child_widgets = []
        self._children_layout = None

        self._build_widget()

    def _build_widget(self):
        # Widget
        self.setToolTip(f"{self.attribute} ({self.attribute.type_})")

        # Attribute Name
        attribute_full_name = [
            part for part in re.split(r"[.\[\]]", self.attribute.attr_name) if part
        ][-1]
        attribute_name = (
            attribute_full_name
            if not self.parent_attr_name
            else attribute_full_name.replace(self.parent_attr_name, "")
        )
        if re.fullmatch(r"[0-9]+", attribute_full_name):
            attribute_name = f"[{attribute_name}]"
        self.parent_attr_name = attribute_full_name

        # Properties
        self._update_properties()

        child_layout = None
        if self.attribute.has_children():
            child_layout = self._build_children()

        if (
            self.attribute.has_children()
            and not self._attr_is_array
            and not self._is_double_compound_attr
        ):
            child_layout.setContentsMargins(10, 0, 0, 0)
            layout = QtWidgets.QVBoxLayout()
            layout.addWidget(QtWidgets.QLabel(attribute_name))
            layout.addLayout(child_layout)

        else:
            layout = QtWidgets.QFormLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setHorizontalSpacing(6)
            layout.setVerticalSpacing(0)

            if child_layout:
                layout.addRow(attribute_name, child_layout)

            else:
                self.field = self._build_field()
                layout.addRow(attribute_name, self.field)

        self.setLayout(layout)

    def _update_properties(self):
        # connected
        self.is_connected = self._is_connected() or self.is_connected

    def _is_connected(self):
        is_connected = self.attribute.has_src_connection()
        curr_attribute = self.attribute
        while not is_connected and curr_attribute.parent is not None:
            curr_attribute = curr_attribute.parent
            is_connected = curr_attribute.has_src_connection()
        return is_connected

    def _build_children(self):
        curr_layout = self._child_layout()
        self._children_layout = curr_layout

        for child_attr in self.attribute:
            widget = AttributeWidget(
                child_attr,
                None,
                "" if not self._is_double_compound_attr else self.parent_attr_name,
                self.is_connected,
                self.watch_changes,
            )
            curr_layout.addWidget(widget)
            if self._attr_is_array:
                widget._array_index = child_attr.index
            self.child_widgets.append(widget)

        if self._attr_is_array:
            btn_layout = QtWidgets.QHBoxLayout()
            self.add_button = QtWidgets.QPushButton("+")
            self.delete_button = QtWidgets.QPushButton("-")

            btn_layout.addWidget(self.add_button)
            btn_layout.addWidget(self.delete_button)

            curr_layout.addLayout(btn_layout)

            self.add_button.clicked.connect(self._add_to_array)
            self.delete_button.clicked.connect(self._delete_from_array)

        return curr_layout

    def _child_layout(self):
        child_layout = QtWidgets.QVBoxLayout()
        if self._is_double_compound_attr:
            child_layout = QtWidgets.QHBoxLayout()

        return child_layout

    def _build_field(self):
        attribute_type = self.attribute.type_
        try:
            attribute_value = self.attribute.value
        except RuntimeError:
            attribute_value = None

        self.supported_type = True
        if attribute_type == "bool":
            self.field = QtWidgets.QCheckBox()
            self.field.setChecked(bool(attribute_value))
            self.field.toggled.connect(self.write_value)

        elif attribute_type == "enum":
            self.field = QtWidgets.QComboBox()
            enum_value = 0
            for enum_name in self.attribute.enum_names:
                label, separator, explicit_value = enum_name.partition("=")
                if separator:
                    enum_value = int(explicit_value)
                self.field.addItem(label, enum_value)
                enum_value += 1
            self.field.setCurrentIndex(self.field.findData(attribute_value))
            self.field.currentIndexChanged.connect(
                lambda index: self.write_value(self.field.itemData(index))
                if index >= 0
                else None
            )
        elif attribute_type == "string":
            self.field = QtWidgets.QLineEdit()
            self.field.setText(attribute_value or "")
            self.field.editingFinished.connect(
                lambda: self.write_value(self.field.text())
            )

        elif attribute_type in {"byte", "char", "short", "long"}:
            self.field = QtWidgets.QSpinBox()
            self.field.setRange(-2147483648, 2147483647)
            self.field.setValue(int(attribute_value))
            self.field.setKeyboardTracking(False)
            self.field.valueChanged.connect(self.write_value)

        elif attribute_type in {
            "float",
            "double",
            "doubleLinear",
            "doubleAngle",
            "time",
        }:
            # float, double, doubleAngle, doubleLinear, and time.
            self.field = QtWidgets.QDoubleSpinBox()
            self.field.setRange(-1e100, 1e100)
            self.field.setDecimals(3)
            self.field.setSingleStep(0.1)
            self.field.setValue(attribute_value)
            self.field.setKeyboardTracking(False)
            self.field.valueChanged.connect(self.write_value)

        else:
            self.supported_type = False
            self.field = QtWidgets.QLineEdit()
            self.field.setDisabled(True)
            if self.attribute.has_src_connection():
                self.field.setText(self.attribute.get_src_connection().name)

        self.update_connection_style()

        return self.field

    def write_value(self, value):
        self.attribute.set(value)

    def _add_to_array(self):
        """Append a pending element editor immediately before the + button"""
        if not self._attr_is_array or self._children_layout is None:
            return
        next_index_attr = self.attribute.next_index_attr()
        AttributeWidget(
            next_index_attr,
            None,
            self.parent_attr_name,
            self.is_connected,
            self.watch_changes,
        )
        self._refresh_array_children()

    def _delete_from_array(self):
        if not self._attr_is_array or self._children_layout is None:
            return
        last_index = self.attribute.get_indicies()[-1]
        self.attribute.remove_index(last_index)

        self._refresh_array_children()

    def _refresh_array_children(self):
        """Match child editors to existing array indices without modifying Maya.

        Reuse unchanged editors, destroy obsolete or duplicate rows, and insert
        missing rows in logical-index order before the array buttons.
        """
        if not self._attr_is_array or self._children_layout is None:
            return

        indices = sorted(self.attribute.get_indicies())
        existing_widgets = {}

        # creating child existing dict
        for child in self.child_widgets:
            index = child._array_index
            self._children_layout.removeWidget(child)
            if index in indices and index not in existing_widgets:
                existing_widgets[index] = child

        # add them back in
        children = []
        for position, index in enumerate(indices):
            child = existing_widgets.get(index)
            if child is None:
                child = AttributeWidget(
                    self.attribute[index],
                    parent=self,
                    parent_attr_name=self.parent_attr_name,
                    is_connected=self.is_connected,
                    watch_changes=self.watch_changes,
                )
                child._array_index = index
            self._children_layout.insertWidget(position, child)
            if self.isVisible():
                child.show()
            children.append(child)
        self.child_widgets = children

    def refresh(self):
        if self.field:
            previous = self.field.blockSignals(True)
            try:
                value = self.attribute.value if self.supported_type else None
                if isinstance(self.field, QtWidgets.QCheckBox):
                    self.field.setChecked(value)

                elif isinstance(self.field, QtWidgets.QComboBox):
                    self.field.setCurrentIndex(self.field.findData(value))

                elif isinstance(
                    self.field, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)
                ):
                    self.field.setValue(value)

                elif isinstance(self.field, QtWidgets.QLineEdit):
                    self.field.setText("" if value is None else str(value))

            finally:
                self.field.blockSignals(previous)

    def update_connection_style(self):
        self._update_properties()
        if self.field:
            override_str = ""
            if self._is_connected():
                self.field.setStyleSheet("background-color: #f1f1a5")
                override_str = str(self.attribute.get_src_connection())

            else:
                self.field.setStyleSheet("")

            if not self.supported_type and isinstance(self.field, QtWidgets.QLineEdit):
                self.field.setText(override_str)

        if self.supported_type:
            self.field.setEnabled(
                bool(cmds.getAttr(str(self.attribute), settable=True))
            )

    def showEvent(self, event):
        super().showEvent(event)

        self.script_jobs.clear()
        self.refresh()
        self.update_connection_style()

        self.script_jobs.clear()
        if self.watch_changes and self.field is not None:
            if self.supported_type:
                self.script_jobs.on_attribute_change(self.attribute, self.refresh)
            self.script_jobs.on_connection_changed(
                self.attribute, self.update_connection_style
            )
        elif self._attr_is_array:
            self._refresh_array_children()
            self.script_jobs.on_attribute_change(
                self.attribute,
                self._refresh_array_children,
                disregardIndex=True,
                allChildren=True,
            )

    def hideEvent(self, event):
        self.script_jobs.clear()
        super().hideEvent(event)


def create_separator():
    """Return a sunken horizontal QFrame for insertion into a Qt layout."""
    separator = QtWidgets.QFrame()
    separator.setFrameShape(QtWidgets.QFrame.HLine)
    separator.setFrameShadow(QtWidgets.QFrame.Sunken)

    return separator
