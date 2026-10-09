from dataclasses import dataclass, field as dataclass_field

from .node_wrapper import Attr

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
    """Maya-parented dialog that builds widgets, layout, then connections.

    Subclasses must implement all three creation methods. Initialize any
    state they need before calling this constructor.
    """

    def __init__(self, name: str, parent=None, width:float=None, height:float=None):
        super().__init__(maya_main_window() if parent is None else parent)
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

def create_attribute_widget(
    attribute: Attr | str,
    parent:QtWidgets.QWidget=None,
    parent_attr_name:str=None,
    is_connected: bool = False,
) -> AttributeWidget:
    """Return the editor's outer widget, controls, and recursive child results."""
    displayed_indices = set()

    def add_to_array(child_layout:QtWidgets.QHBoxLayout):
        """Append a pending element editor immediately before the + button"""
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
    separator = QtWidgets.QFrame()
    separator.setFrameShape(QtWidgets.QFrame.HLine)
    separator.setFrameShadow(QtWidgets.QFrame.Sunken)

    return separator