"""Maya node, attribute, matrix, and vector wrappers with undo-aware scene helpers."""

from __future__ import annotations
from maya.api import OpenMaya as om2
import maya.cmds as cmds
from typing import Union
from . import apiundo
import re as re
from collections import deque
import math
from enum import Enum


class _OMUtils:
    """Internal helpers for resolving Maya dependency nodes and plugs."""
    @classmethod
    def try_int(cls, s):
        """Return int(s), or None on TypeError or ValueError."""
        try:
            return int(s)
        except (TypeError, ValueError):
            return None

    @classmethod
    def get_dep_node(cls, node: Union[om2.MObject, om2.MPlug, str]):
        """Resolve a name, Node, MObject, MPlug, or MFnDependencyNode.

        Return an MFnDependencyNode, or None for unsupported inputs. Missing
        or ambiguous names can raise lookup errors rather than returning None."""
        if isinstance(node, om2.MFnDependencyNode):
            return node
        if isinstance(node, om2.MObject):
            if node.hasFn(om2.MFn.kDependencyNode):
                return om2.MFnDependencyNode(node)

        # if can be added to a MSelectionList
        m_sel_list = om2.MSelectionList()
        if isinstance(node, str):
            full_name = cmds.ls(str(node), long=True)
            if len(full_name) > 1:
                cmds.error(f"more than 1 object named {node}")
            node = full_name[0]
        elif isinstance(node, om2.MPlug):
            return _OMUtils.get_dep_node(node.node())
        elif isinstance(node, Node):
            return node.get_dep_node()

        # if not string or mplug
        else:
            return None

        m_sel_list.add(node)
        dep_node = m_sel_list.getDependNode(0)
        return om2.MFnDependencyNode(dep_node)

    @classmethod
    def get_child_plug(cls, plug: om2.MPlug, attr: str):
        """Return a named immediate child MPlug, or None when absent.

        Pass attr=None to return a dictionary mapping child names to plugs."""
        child_plugs = [plug.child(index) for index in range(plug.numChildren())]
        child_plugs = {x.name().rsplit(".", 1)[1]: x for x in child_plugs}
        if attr is None:
            return child_plugs
        if attr in child_plugs.keys():
            return child_plugs[attr]
        return None

    @classmethod
    def get_plug(
        cls,
        attr_parent: Union[om2.MPlug, om2.MFnDependencyNode, str],
        attr: Union[om2.MPlug, str],
    ):
        """Resolve attr relative to a node name, MFnDependencyNode, or MPlug.

        attr can be an MPlug or a path with compound children and logical array
        indices. Pass attr_parent=None for a node-qualified path. Unresolved
        paths may return None or raise a Maya lookup error."""

        if isinstance(attr, om2.MPlug):
            return attr
        elif isinstance(attr_parent, om2.MPlug):
            attr_str = str(attr)
            curr_plug = attr_parent
            for x in [x for x in re.split(r"[.|\[|\]]", attr_str) if x != ""]:
                if curr_plug.isArray:
                    curr_plug = curr_plug.elementByLogicalIndex(int(x))
                elif curr_plug.isCompound:
                    new_val = _OMUtils.try_int(x)
                    if new_val is not None:
                        curr_plug = curr_plug.child(new_val)
                    else:
                        curr_plug = _OMUtils.get_child_plug(curr_plug, x)
                    if curr_plug is None:
                        return None
                else:
                    return None
            return curr_plug
        elif attr_parent is None:
            attr_parent = _OMUtils.get_dep_node(attr)
            attr_str = attr.split(".", 1)[1]
            return _OMUtils.get_plug(attr_parent, attr_str)
        elif isinstance(attr_parent, str):
            attr_parent = _OMUtils.get_dep_node(attr_parent)
            return _OMUtils.get_plug(attr_parent, attr)
        elif isinstance(attr_parent, om2.MFnDependencyNode):
            split_attr = re.split(r"[.|\[|\]]", attr, 1)
            plug = attr_parent.findPlug(split_attr[0], False)
            if len(split_attr) == 1:
                return plug
            return _OMUtils.get_plug(plug, split_attr[1])

    @classmethod
    def connect_plugs(cls, src_plug: om2.MPlug, dest_plug: om2.MPlug):
        """Connect source to destination and register undo/redo callbacks.

        On RuntimeError, fall back to cmds.connectAttr(force=True)."""

        def redo(src_plug, dest_plug):
            dgMod = om2.MDGModifier()
            dgMod.connect(src_plug, dest_plug)
            dgMod.doIt()

        def undo(src_plug, dest_plug):
            dgMod = om2.MDGModifier()
            dgMod.disconnect(src_plug, dest_plug)
            dgMod.doIt()

        use_connect_attr = False
        try:
            redo(src_plug, dest_plug)
            apiundo.commit(
                redo=lambda: redo(src_plug, dest_plug),
                undo=lambda: undo(src_plug, dest_plug),
            )
        except RuntimeError:
            use_connect_attr = True
        if use_connect_attr:
            cmds.connectAttr(str(src_plug), str(dest_plug), force=True)


class Matrix(om2.MMatrix):
    """MMatrix subclass with translation, rotation, and scale helpers."""

    def __init__(self, *args):
        """Initialize from MMatrix arguments, 16 positional entries, or a matrix Attr.

        An Attr with value None initializes entries to the integers 0..15."""
        if len(args) > 0 and isinstance(args[0], Attr):
            if args[0].value is None:
                super(Matrix, self).__init__([x for x in range(16)])
            elif args[0].type_ == "matrix":
                super(Matrix, self).__init__(args[0].value)
        elif len(args) == 16:
            super(Matrix, self).__init__(args)
        else:
            super(Matrix, self).__init__(*args)

    def get(self, r, c):
        """Return the entry at zero-based row r and column c."""
        return self[r * 4 + c]

    def setT(self, t):
        """Set translation in place from the first three values of t."""
        self[12] = t[0]
        self[13] = t[1]
        self[14] = t[2]

    def __str__(self):
        """Return a translation, rotation-in-degrees, and scale summary."""
        return (
            f"Translate: {self.translate} | Rotate: {self.rotate} | Scale: {self.scale}"
        )

    @property
    def rotate(self):
        """Return the three Euler rotation components in degrees as a tuple."""
        return self.as_degrees

    @property
    def translate(self):
        """Return the three translation entries as a tuple."""
        return self[12], self[13], self[14]

    @property
    def scale(self):
        """Return basis-vector lengths, negating Z for a negative determinant."""
        z_scalar = 1
        if self.det4x4() < 0:
            z_scalar = -1
        return (
            om2.MVector(self.column(0)).length(),
            om2.MVector(self.column(1)).length(),
            om2.MVector(self.column(2)).length() * z_scalar,
        )

    def column(self, index):
        """Return three consecutive entries starting at index * 4 as a tuple.

        Despite the name, this follows the flattened matrix row layout."""
        i = index * 4
        return self[i], self[i + 1], self[i + 2]

    @property
    def as_radians(self):
        """Return the three Euler rotation components in radians as a tuple."""
        rx, ry, rz, ro = om2.MTransformationMatrix(self).rotationComponents(
            asQuaternion=False
        )
        return rx, ry, rz

    @property
    def as_degrees(self):
        """Return the three Euler rotation components in degrees as a tuple."""
        rx, ry, rz, ro = om2.MTransformationMatrix(self).rotationComponents(
            asQuaternion=False
        )
        return math.degrees(rx), math.degrees(ry), math.degrees(rz)

    @property
    def quaternion(self):
        """Return om2.QuaternionOrPoint().setValue(self).

        Requires that helper to exist in the installed OpenMaya API."""
        return om2.QuaternionOrPoint().setValue(self)

    def set_transform(self, transform: Transform, world_space: bool = False):
        """Apply this matrix to transform using cmds.xform.

        world_space=False uses object space; True uses world space."""
        cmds.xform(str(transform), worldSpace=world_space, matrix=list(self))

    @classmethod
    def identity_matrix(cls):
        """Return the 16 identity-matrix entries as a flat list."""
        return [
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
        ]

    @classmethod
    def zero_matrix(cls):
        """Return a Matrix with all 16 entries set to zero."""
        return cls([0.0 for x in range(16)])

    @classmethod
    def translate_matrix(cls, *translation):
        """Return a Matrix from positional X, Y, Z translation values.

        Missing components default to zero; values beyond three are ignored."""
        matrix = cls.identity_matrix()
        translation = make_len(list(translation), len_=3, default=0)
        matrix[12] = translation[0]
        matrix[13] = translation[1]
        matrix[14] = translation[2]

        return cls(matrix)

    @classmethod
    def scale_matrix(cls, *scale):
        """Return a flat 16-entry scale-matrix list from positional X, Y, Z values.

        Missing components default to one; values beyond three are ignored."""
        matrix = cls.identity_matrix()
        scale = make_len(list(scale), len_=3, default=1)
        matrix[0] = scale[0]
        matrix[5] = scale[1]
        matrix[10] = scale[2]

        return matrix


class Vector(om2.MVector):
    """MVector subclass that wraps vector-valued arithmetic results as Vector."""

    def _cast_return_type(self, return_obj):
        if isinstance(return_obj, om2.MVector):
            return Vector(return_obj)
        return return_obj

    def __add__(self, other):
        return self._cast_return_type(super().__add__(other))

    def __iadd__(self, other):
        return self._cast_return_type(super().__iadd__(other))

    def __imul__(self, other):
        return self._cast_return_type(super().__imul__(other))

    def __isub__(self, other):
        return self._cast_return_type(super().__isub__(other))

    def __itruediv__(self, other):
        return self._cast_return_type(super().__itruediv__(other))

    def __mul__(self, other):
        return self._cast_return_type(super().__mul__(other))

    def __neg__(self):
        return self._cast_return_type(super().__neg__())

    def __radd__(self, other):
        return self._cast_return_type(super().__radd__(other))

    def __rmul__(self, other):
        return self._cast_return_type(super().__rmul__(other))

    def __rsub__(self, other):
        return self._cast_return_type(super().__rsub__(other))

    def __rtruediv__(self, other):
        return self._cast_return_type(super().__rtruediv__(other))

    def __rxor__(self, other):
        """Return the reflected cross product other ^ self."""
        return self._cast_return_type(super().__rxor__(other))

    def __sub__(self, other):
        return self._cast_return_type(super().__sub__(other))

    def __truediv__(self, other):
        return self._cast_return_type(super().__truediv__(other))

    def __xor__(self, other):
        """Return the cross product self ^ other."""
        return self._cast_return_type(super().__xor__(other))


def wrap_node(node, **attr_data_dict):
    """Wrap an existing node name or Node as Container, Transform, or Node.

    Keyword attribute data is set or connected after wrapping. Raise
    RuntimeError if the node does not exist."""
    if not node_exists(node):
        raise RuntimeError(f"Node \"{node}\" does not exist. wrapping node failed")
    node_class = Node
    if issubclass(type(node), Node):
        if node.type_ == "container":
            node_class = Container
        elif node.type_ == "transform":
            node_class = Transform
    elif isinstance(node, str):
        if cmds.nodeType(node) == "container":
            node_class = Container
        elif cmds.nodeType(node) == "transform":
            node_class = Transform

    node_instance = node_class(node)

    node_instance.set_connect_attr_data_dict(**attr_data_dict)

    return node_instance


def create_node(node_type: str, name: str = None, **attr_data_dict):
    """Create node_type with optional name and return its specialized wrapper.

    Keyword attribute data is set or connected on the created node."""
    if name is None:
        return wrap_node(cmds.createNode(node_type), **attr_data_dict)
    return wrap_node(cmds.createNode(node_type, name=name), **attr_data_dict)


def node_exists(node):
    """Return whether the node name or wrapper exists in the scene."""
    return cmds.objExists(str(node))


def delete_node(node: Node):
    """Delete a node from the current Maya scene.

    Args:
        node: Node wrapper or node name identifying the node to delete.
    """
    cmds.delete(str(node))


def _snake_to_camel(snake_str):
    """Convert underscore-separated words to lower camel case."""
    # Split the string by underscores
    if snake_str.find("fk") > 0:
        snake_str = snake_str.replace("fk", "FK")
    if snake_str.find("ik") > 0:
        snake_str = snake_str.replace("ik", "IK")
    components = snake_str.split("_")
    # Capitalize the first letter of each component except the first one, and join them
    camel_case_str = components[0] + "".join(x.title() for x in components[1:])
    return camel_case_str


def kwargs_to_dict(**kwarg_dict):
    """Return keyword arguments as a dictionary."""
    return kwarg_dict


def make_len(curr_list: list, len_: int, default=0.0):
    """Pad or truncate curr_list to len_ entries.

    Padding extends the original list using default (0.0 by default).
    Truncation returns a slice without shortening the original list."""

    curr_list_len = len(curr_list)
    if curr_list_len < len_:
        ending_list = [default for x in range(len_ - curr_list_len)]
        curr_list.extend(ending_list)
        return curr_list
    elif curr_list_len > len_:
        return curr_list[:len_]
    return curr_list


class AttrTypes(Enum):
    """Supported attribute types and their cmds.addAttr type flags."""
    bool = {"attributeType": "bool"}
    compound = {"attributeType": "compound"}
    double2 = {"attributeType": "double2"}
    double3 = {"attributeType": "double3"}
    double = {"attributeType": "double"}
    enum = {"attributeType": "enum"}
    long = {"attributeType": "long"}
    matrix = {"dataType": "matrix"}
    mesh = {"dataType": "mesh"}
    message = {"attributeType": "message"}
    nurbsCurve = {"dataType": "nurbsCurve"}
    nurbsSurface = {"dataType": "nurbsSurface"}
    short = {"attributeType": "short"}
    string = {"dataType": "string"}

class KeyableAttrs(Enum):
    """Common transform and visibility names for lock_hide_attr()."""
    t = "t"
    tx = "tx"
    ty = "ty"
    tz = "tz"
    r = "r"
    rx = "rx"
    ry = "ry"
    rz = "rz"
    s = "s"
    sx = "sx"
    sy = "sy"
    sz = "sz"
    visibility = "visibility"

def double3_children(name: str, suffixes: str = "XYZ", **add_attr_kwargs) -> dict[str, AttrTypes]:
    """Build three double children for a double3 in ``Node.add_attrs``.

    Child names append each suffix to ``name``, preserving letter case.
    ``suffixes`` must contain exactly three distinct ASCII letters.

    Examples:
        node.add_attrs(offset=double3_children("offset"))
        node.add_attrs(color=double3_children("color", "RGB"))
    """
    if not isinstance(suffixes, str):
        raise TypeError("suffixes must be a string")
    if (
        len(suffixes) != 3
        or not suffixes.isascii()
        or not suffixes.isalpha()
        or len(set(suffixes)) != 3
    ):
        raise ValueError("suffixes must contain exactly three distinct ASCII letters")
    child_dict = {f"{name}{suffix}": AttrTypes.double for suffix in suffixes}
    child_dict.update(**add_attr_kwargs)
    return child_dict



class Node:
    """Wrap a dependency node with cached Attr access and scene helpers.

    Indexing retrieves Attr wrappers; assignment sets their values.
    full_name uses MFnDependencyNode.uniqueName(); name strips DAG parents
    and namespaces, type_ reports the Maya type, and mobject exposes MObject."""

    def __init__(self, node):
        """Initialize from a node name, Node, MObject, MPlug, or MFnDependencyNode."""
        if isinstance(node, str):
            if not node_exists(node):
                cmds.error(f"node {node} does not exist")
                return
        self._dep_node = _OMUtils.get_dep_node(node)
        self.__attr_cache = {}
        self.__full_attr_list = None

    # properties
    @property
    def full_name(self):
        """Return MFnDependencyNode.uniqueName(), possibly including a partial DAG path."""
        return self._dep_node.uniqueName()

    @property
    def name(self):
        """Return the node name without DAG parents or namespace prefixes."""
        if re.search(r"[|:]", self.full_name):
            return re.split(r"[|:]", self.full_name)[-1]
        return self.full_name

    @property
    def type_(self):
        """Return the Maya dependency-node type name as a string."""
        return self._dep_node.typeName

    @property
    def mobject(self):
        """Return the dependency node MObject."""
        return self._dep_node.object()

    def has_attr(self, attr_name):
        """Return whether attr_name resolves to an attribute on this node."""
        try:
            self.__getitem__(attr_name)
            return True
        except RuntimeError:
            return False
        except AttributeError:
            return False

    def add_attrs(
        self, keyable: bool = True, attr_name_camel_case: bool = True, **add_attr_dict
    ):
        """Create attributes from keyword names and nested type specifications.

        Values may be AttrTypes, type names, colon-separated enum labels, or
        dictionaries of children and add_attr options. Two or three double
        children infer double2 or double3; other children infer compound.
        keyable=True makes attributes keyable. attr_name_camel_case=True
        converts specification names and option keys from snake case."""

        def _flatten_validate_dict(
            main_dict: dict,
            sub_dict: dict = {},
            parent_key: str = "",
            attr_name_camel_case: bool = True,
        ):
            """Flatten nested specifications into main_dict and record parent names.

            Normalize names when requested and inherit keyable from add_attrs()."""
            if len(sub_dict.keys()) == 0:
                sub_dict = main_dict
            for key, value in list(sub_dict.items()):
                cast_camel = str
                if attr_name_camel_case:
                    cast_camel = _snake_to_camel
                camel_key = cast_camel(key)
                if key in main_dict.keys():
                    main_dict.pop(key)

                value_dict = {"name": camel_key, "keyable": keyable}
                if parent_key != "":
                    value_dict["parent"] = parent_key

                # if value is a string or AttrType
                if isinstance(value, str) or isinstance(value, AttrTypes):
                    if isinstance(value, str):
                        if hasattr(AttrTypes, value):
                            value = getattr(AttrTypes, value)
                        elif value.find(":") >= 0:
                            value_dict["enumName"] = value
                            value = AttrTypes.enum
                        else:
                            cmds.warning(
                                f'attribute type "{value}" not found... skipping'
                            )
                            continue
                    value_dict["type_"] = value
                    main_dict[camel_key] = value_dict

                elif isinstance(value, dict):
                    child_dict = {
                        sub_key: sub_value
                        for sub_key, sub_value in value.items()
                        if (
                            (
                                isinstance(sub_value, str)
                                and hasattr(AttrTypes, sub_value)
                            )
                            or isinstance(sub_value, AttrTypes)
                            or isinstance(sub_value, dict)
                        )
                        and sub_key != "type_"
                    }
                    args_dict = {
                        cast_camel(sub_key): sub_value
                        for sub_key, sub_value in value.items()
                        if sub_key not in child_dict.keys()
                    }
                    if "type" in args_dict.keys():
                        type_val = args_dict.pop("type")
                        args_dict["type_"] = type_val
                    # get compound type
                    if child_dict != {} and "type_" not in args_dict.keys():
                        if all(
                            child_value is AttrTypes.double or child_value == "double"
                            for child_value in child_dict.values()
                        ):
                            if len(child_dict.keys()) == 3:
                                value_dict["type_"] = AttrTypes.double3
                            elif len(child_dict.keys()) == 2:
                                value_dict["type_"] = AttrTypes.double2
                            else:
                                value_dict["type_"] = AttrTypes.compound
                        else:
                            value_dict["type_"] = AttrTypes.compound

                    value_dict.update(args_dict)
                    main_dict[camel_key] = value_dict

                    if child_dict != {}:
                        _flatten_validate_dict(
                            main_dict,
                            child_dict,
                            camel_key,
                            attr_name_camel_case=attr_name_camel_case,
                        )

        _flatten_validate_dict(add_attr_dict, attr_name_camel_case=attr_name_camel_case)

        # num parents dictionary
        num_parent_dict = {}
        for value in add_attr_dict.values():
            if "parent" in value.keys():
                if value["parent"] not in num_parent_dict:
                    num_parent_dict[value["parent"]] = 1
                else:
                    num_parent_dict[value["parent"]] += 1

        num_parent_dict = {
            key: value
            for key, value in num_parent_dict.items()
            if key in add_attr_dict.keys()
        }

        # adding attributes
        add_attr_keys = deque(add_attr_dict.keys())
        while add_attr_keys:
            attr_name = add_attr_keys.popleft()
            data = add_attr_dict[attr_name]

            if "parent" in data.keys():
                if data["parent"] in add_attr_keys:
                    add_attr_keys.append(attr_name)
                    continue
                elif data["parent"] not in num_parent_dict.keys():
                    cmds.warning(
                        f'{attr_name}\'s parent "{data["parent"]}" not created in add_attrs function. attribute not created'
                    )
                    continue

            if data["type_"] is AttrTypes.compound:
                data["numberOfChildren"] = num_parent_dict[attr_name]

            self.add_attr(**data)

    def add_attr(self, name: str, type_: Union[AttrTypes, str], **kwargs):
        """Create one attribute using AttrTypes and cmds.addAttr keyword options.

        name supplies longName; option keys are converted from snake case.
        String type_ values currently enter the enum-label branch; use AttrTypes
        for non-enum types. Returns None."""
        if "parent" in kwargs.keys():
            if isinstance(kwargs["parent"], Attr):
                kwargs["parent"] = kwargs["parent"].attr_name
            else:
                kwargs["parent"] = str(kwargs["parent"])

        for ln in ["longName", "long_name"]:
            if ln in kwargs.keys():
                kwargs.pop(ln)
        kwargs["longName"] = name

        if isinstance(type_, str):
            if type_.find(":") is not None:
                for enum_name in ["enumName", "enum_name"]:
                    if enum_name in kwargs.keys():
                        kwargs.pop(enum_name)
                kwargs["enumName"] = type_
                type_ = AttrTypes.enum

            elif AttrTypes.hasattr(type_):
                type_ = AttrTypes.getattr(type_)

        kwargs.update(type_.value)

        new_kwargs = {}

        for key in kwargs:
            new_kwargs[_snake_to_camel(key)] = kwargs[key]
        cmds.addAttr(str(self), **new_kwargs)

    def delete_attr(self, attr):
        """Delete the attribute identified by attr using cmds.deleteAttr(at=attr)."""
        cmds.deleteAttr(str(self), at=attr)

    def get_connection_list(self, as_src, as_dest):
        """Return (source Attr, destination Attr) connection pairs.

        as_src currently selects incoming connections; as_dest selects outgoing
        connections. Published container plugs and hyperLayout links are filtered."""
        connections = set()
        if as_src:
            connection_list = cmds.listConnections(
                str(self), connections=True, source=True, destination=False, plugs=True
            )
            if connection_list is not None:
                connection_list = [
                    (Attr(x), Attr(y, self))
                    for x, y in zip(connection_list[1::2], connection_list[::2])
                ]
                connections.update(connection_list)
        if as_dest:
            connection_list = cmds.listConnections(
                str(self), connections=True, source=False, destination=True, plugs=True
            )
            if connection_list is not None:
                connection_list = [
                    (Attr(x, self), Attr(y))
                    for x, y in zip(connection_list[::2], connection_list[1::2])
                ]
                connections.update(connection_list)
        if self.type_ == "container":
            self_container = Container(self)
            published_attrs = self_container.get_published_attrs()

            connections = [
                x
                for x in connections
                if x[0] not in published_attrs and x[1] not in published_attrs
            ]
        connections = [
            x
            for x in connections
            if x[0].node.type_ != "hyperLayout"
            and x[1].node.type_ != "hyperLayout"
        ]
        return connections

    def _check_node_in_attr_list(self, attribute_list):
        """Resolve names on this node and return the matching Attr wrappers."""
        if attribute_list:
            attribute_list = [self[x] for x in attribute_list]
            attribute_list = [x for x in attribute_list if x.node == self]
            return attribute_list
        return []

    def delete_node(self, clean=True):
        """Delete this node with history, publication, and connection cleanup.

        DAG descendants are included. Missing nodes are ignored. clean=True is
        the default; clean=False deletes first but currently still continues
        into the cleanup code."""
        if not node_exists(self):
            return
        if not clean:
            cmds.delete(str(self))

        # delete history
        cmds.delete(str(self), constructionHistory=True)
        children = cmds.listRelatives(str(self), allDescendents=True, fullPath=True)

        all_children = [self]
        if children is not None:
            all_children.extend([wrap_node(x) for x in children])

        # unpublish
        node_container = self.get_container_node()
        if node_container is not None:
            publish_attrs = node_container.get_published_attrs()
            filter_publish_attrs = [x for x in publish_attrs if x.node == self]
            for attr in filter_publish_attrs:
                node_container.unpublish_attr(attr)

        # loop from child to parent
        for node in all_children[::-1]:
            # if container delete outside connections
            if node.type_ == "container":
                self_container = Container(node=node)
                connections = self_container.get_external_connection_list()
                for _, dest in connections:
                    ~dest

            # delete connections
            connections = node.get_connection_list(True, True)
            for _, dest in connections:
                ~dest

            cmds.delete(str(node))

    def get_container_node(self):
        """Return the containing Container, or None if uncontained."""
        container = cmds.container(findContainer=self.full_name, query=True)
        if container is not None:
            return Container(container)
        return container

    def get_top_level_attribute_list(self, re_cache=False):
        """Return cached top-level Attr wrappers, excluding child attributes.

        Pass re_cache=True to rebuild from the dependency node."""

        if self.__full_attr_list is None or re_cache:
            attr_count = self._dep_node.attributeCount()
            attributes = [self._dep_node.attribute(x) for x in range(attr_count)]
            self.__full_attr_list = [
                Attr(self._dep_node.findPlug(x, False), self) for x in attributes
            ]

            for attr in self.__full_attr_list:
                attr_name = attr.attr_name
                self.__attr_cache[attr_name] = attr

        self.__full_attr_list = [
            attr for attr in self.__full_attr_list if attr.parent is None
        ]

        return self.__full_attr_list

    def get_dep_node(self):
        """Return the underlying maya.api.OpenMaya.MFnDependencyNode."""
        return self._dep_node

    def get_attr_cache(self):
        """Return the live dictionary mapping attribute paths to cached Attr wrappers."""
        return self.__attr_cache

    def rename(self, new_name: str):
        """Rename this node and register undo/redo callbacks."""
        curr_name = self.name
        self._dep_node.setName(new_name)
        apiundo.commit(
            undo=lambda: self._dep_node.setName(curr_name),
            redo=lambda: self._dep_node.setName(new_name),
        )

    def set_connect_attr_data_dict(self, **attr_data_dict):
        """Set values or connect Attr sources using keyword attribute paths.

        Nested dictionaries expand into indexed paths. Lists containing Attr
        objects expand into indexed assignments; other lists are set as values."""
        while attr_data_dict != {}:
            key, value = attr_data_dict.popitem()
            if isinstance(value, dict):
                for sub_key in value.keys():
                    new_key = f"{key}[{sub_key}]"
                    new_value = value[sub_key]
                    if new_key in attr_data_dict.keys():
                        cmds.warning(
                            f"{new_key}:{new_value} not added. key already exists"
                        )
                        continue
                    attr_data_dict[new_key] = new_value
            elif isinstance(value, list):
                if any(isinstance(item, Attr) for item in value):
                    for index, item in enumerate(value):
                        new_key = f"{key}[{index}]"
                        if new_key in attr_data_dict.keys():
                            cmds.warning(
                                f"{new_key}:{new_value} not added. key already exists"
                            )
                            continue
                        attr_data_dict[new_key] = item
                else:
                    self.set_connect_attr_data(key, value)

            else:
                self.set_connect_attr_data(key, value)

    def set_connect_attr_data(
        self, attr_name: str, attr_data, set_when_data_is_attr: bool = False
    ):
        """Set or connect attr_data on attr_name; warn if the attribute is absent.

        An Attr connects by default. set_when_data_is_attr=True copies its value."""
        if not self.has_attr(attr_name):
            cmds.warning(f"{self.name}.{attr_name} doesn't not exist.")
            return

        self[attr_name].set_connect(attr_data, set_when_data_is_attr)

    def lock_hide_attr(self, *attrs, lock=True, hide=True):
        """Set lock and keyability for names or KeyableAttrs passed positionally.

        lock and hide default to True. hide controls keyability rather than
        the Channel Box visibility flag."""
        for attr in attrs:
            if isinstance(attr, KeyableAttrs):
                attr = attr.value
            if not isinstance(attr, str):
                raise ValueError(f"attr must be of type KeaybleAttr or str. attr {attr} is of type {type(attr)}")
            attr = self[attr]
            attr.set_locked(lock)
            attr.set_keyable(not hide)
            
    # operator overloads
    def __str__(self):
        """Return the current unique node name."""
        return self.full_name

    def __getitem__(self, attr: str):
        """Return the cached Attr for attr, resolving and caching it if necessary.

        Raise AttributeError when plug resolution raises RuntimeError."""
        attr_instance = None

        error = False
        try:
            attr_instance = self._get_cached_attr(attr)

        except RuntimeError:
            error = True

        if error:
            raise AttributeError(f'{self.name} does not have attribute "{attr}"')

        return attr_instance

    def __setitem__(self, attr: str, new_value):
        """Set attribute attr to new_value through Attr.set()."""
        attr = self.__getitem__(attr)
        attr.set(new_value)

    def _get_cached_attr(self, attr):
        """Resolve and cache attr by its path, then return the Attr wrapper."""
        if attr not in self.__attr_cache.keys():
            self.__attr_cache[attr] = Attr(
                _OMUtils.get_plug(self._dep_node, attr), self
            )
        return self.__attr_cache[attr]

    def __eq__(self, other):
        """Return whether other is a Node with the same current string name."""
        if isinstance(other, Node):
            if str(self) == str(other):
                return True

        return False

    def __hash__(self):
        """Return an integer hash of the current unique name; renaming changes it."""
        return hash(self.full_name)


class Container(Node):
    """Node wrapper with membership, locking, and published-attribute access."""

    def __init__(self, node):
        """Initialize a container wrapper from the same node inputs as Node."""
        super(Container, self).__init__(node)

    def get_nodes(self):
        """Return members as generic Node wrappers, or None for an empty query result."""
        child_nodes = cmds.container(str(self), query=True, nodeList=True)
        if child_nodes:
            return [Node(x) for x in child_nodes]

    def lock(self, proprigate=False):
        """Lock this container and its unpublished attributes.

        proprigate=True also locks enclosing containers, from this container
        outward. The parameter spelling is retained by the API."""
        if proprigate:
            container_list = []
            current_container = self
            while current_container is not None:
                container_list.append(current_container)
                current_container = current_container.get_container_node()
        else:
            container_list = [self]

        for container in container_list:
            cmds.lockNode(str(container), lock=True, lockUnpublished=True)

    def unlock(self, proprigate=False):
        """Unlock this container and its unpublished attributes.

        proprigate=True also unlocks enclosing containers, from the outermost
        inward. The parameter spelling is retained by the API."""

        if proprigate:
            container_list = []
            current_container = self
            while current_container is not None:
                container_list.append(current_container)
                current_container = current_container.get_container_node()

        else:
            container_list = [self]

        container_list = container_list[::-1]
        for container in container_list:
            cmds.lockNode(str(container), lock=False, lockUnpublished=False)

    def __enter__(self):
        """Unlock this container and return it for a with block."""
        self.unlock()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """Lock this container on leaving a with block, including on exceptions."""
        self.lock()

    def add_nodes(
        self,
        *args,
        include_network=False,
        include_hierarchy_above=False,
        include_hierarchy_below=False,
        force=False,
    ):
        """Add positional node names or wrappers and adjacent unitConversion nodes.

        include_network, include_hierarchy_above, include_hierarchy_below, and
        force are forwarded to cmds.container and default to False."""
        args = [str(x) for x in args]
        conversionNodes = []
        for node in args:
            node_conversionNodes = cmds.listConnections(
                node, source=True, destination=True
            )
            node_conversionNodes = cmds.ls(
                node_conversionNodes, type="unitConversion", long=True
            )
            conversionNodes.extend(node_conversionNodes)
        args.extend(conversionNodes)
        cmds.container(
            str(self),
            addNode=args,
            edit=True,
            iha=include_hierarchy_above,
            ihb=include_hierarchy_below,
            inc=include_network,
            force=force,
        )

    def get_container_node(self):
        """Return the parent Container, or None if there is no parent."""
        containers = cmds.container(str(self), query=True, parentContainer=True)
        if containers is not None:
            return Container(containers[0])
        return containers

    def remove_nodes(self, *args, all_descendents=False):
        """Remove positional nodes and their children from this container.

        With no args, use all members. all_descendents=True includes all
        descendants rather than the immediate children queried by default."""
        if len(args) == 0:
            args = self.get_nodes()
        args = [str(x) for x in args]

        remove_list = args.copy()
        for node in args:
            curr_remove_nodes = cmds.listRelatives(
                node, allDescendents=all_descendents, fullPath=True
            )
            if curr_remove_nodes is not None:
                remove_list.extend(curr_remove_nodes)
        cmds.container(str(self), edit=True, removeNode=remove_list, force=True)

    def publish_attr(self, attr: Union["Attr", str], attr_bind_name: str):
        """Publish an Attr or node-qualified path under attr_bind_name.

        Raise RuntimeError when its node is not a container member."""
        if isinstance(attr, Attr):
            node = attr.node
            attr = str(attr)
        else:
            node = wrap_node(attr.split(".", 1)[0])

        if node in self.get_nodes():
            cmds.container(
                str(self), edit=True, publishAndBind=[str(attr), attr_bind_name]
            )
        else:
            raise RuntimeError(f"{node} is not a node of container {str(self)}")

    def unpublish_attr(self, attr):
        """Unbind and unpublish the given Attr or attribute path."""
        cmds.container(str(self), edit=True, unbindAndUnpublish=str(attr))

    def get_published_attr_map(self):
        """Return a dictionary mapping published names to bound Attr wrappers."""

        m_object = self.mobject
        if m_object.hasFn(om2.MFn.kContainer):
            mfn_container = om2.MFnContainerNode(m_object)
            plug_list, attr_list = mfn_container.getPublishedPlugs()
            return {x: Attr(y, None) for x, y in zip(attr_list, plug_list)}
        return {}

    def get_published_attrs(self):
        """Return bound published plugs as a list of Attr wrappers."""
        m_object = self.mobject
        if m_object.hasFn(om2.MFn.kContainer):
            mfn_container = om2.MFnContainerNode(m_object)
            plug_list, _ = mfn_container.getPublishedPlugs()
            return [Attr(x, None) for x in plug_list]
        return []

    def get_external_connection_list(self):
        """Collect (source Attr, destination Attr) boundary-connection pairs.

        Currently calls get_src_connections(), which Attr does not define,
        so this path may raise AttributeError."""
        container_nodes = self.get_nodes()
        connection_list = []

        external_connection_list = cmds.container(
            str(self), query=True, connectionList=True
        )
        if external_connection_list is None:
            external_connection_list = []
        for attr in external_connection_list:
            curr_attr = Attr(attr)

            if (
                curr_attr.type_ not in ["compound", "double3", "double2"]
                and curr_attr.__len__() is not None
            ):
                curr_attr = curr_attr[0]

            input_connections = curr_attr.get_src_connections()
            output_connections = curr_attr.get_dest_connections()
            for input in input_connections:
                if input.node in container_nodes:
                    connection_list.append((input, curr_attr))
            for output in output_connections:
                if output.node in container_nodes:
                    connection_list.append((curr_attr, output))
        return connection_list

    def get_child_containers(self, all=False):
        """Return immediate container members or recursive descendants with all=True.

        The default branch returns generic Node wrappers; the recursive branch
        returns Container wrappers."""
        sub_containers = [x for x in self.get_nodes() if x.type_ == "container"]
        return_child_containers = []
        if not all:
            return sub_containers
        for container in sub_containers:
            container = Container(container)
            return_child_containers.append(container)
            return_child_containers.extend(container.get_child_containers(all=all))
        return return_child_containers

    def __setitem__(self, attr: str, new_value):
        """Set a published attribute by binding name, or a normal node attribute."""
        publish_attr_map = self.get_published_attr_map()
        if attr in publish_attr_map.keys():
            attr = publish_attr_map[attr]
            attr.set(new_value)
        else:
            super().__setitem__(attr, new_value)

    def __getitem__(self, attr: str):
        """Resolve a published or normal attribute, including child/index paths."""
        publish_attr_map = self.get_published_attr_map()
        if attr in publish_attr_map.keys():
            return publish_attr_map[attr]
        if attr.find("[") != -1 or attr.find(".") != -1:
            if attr.find("[") != -1:
                parent_attr, back_attrs = attr.split("[", 1)
                index, back_attrs = back_attrs.split("]", 1)
                if parent_attr in publish_attr_map.keys():
                    return_attr = publish_attr_map[parent_attr][int(index)]
                    if back_attrs != "":
                        return return_attr[back_attrs]
                    return return_attr
            else:
                parent_attr, back_attrs = attr.split(".", 1)
                if parent_attr in publish_attr_map.keys():
                    return publish_attr_map[parent_attr][back_attrs]
        return super().__getitem__(attr)


class Transform(Node):
    """Node wrapper with shape access and transform-freezing helpers."""

    def get_shapes(self):
        """Return wrapped shape nodes, or an empty list when none exist."""
        shapes = cmds.listRelatives(str(self), shapes=True, fullPath=True)
        if shapes is None:
            return []
        return [wrap_node(shape) for shape in shapes]

    def freeze_transforms(self):
        """Apply cmds.makeIdentity while temporarily unlocking common attributes.

        For negative scale, also adjust mesh normals or NURBS surface direction
        and reset opposite. Restore original attribute locks on success."""
        transform_locked_attrs = self.get_transform_locked_attrs()

        for locked_attrs in transform_locked_attrs:
            locked_attrs.set_locked(False)
        scale = self["scale"].value

        cmds.makeIdentity(str(self), apply=True)

        if scale[0] * scale[1] * scale[2] < 0:
            shapes = [
                wrap_node(x)
                for x in cmds.listRelatives(str(self), shapes=True, fullPath=True)
            ]
            for x in shapes:
                if x.type_ == "nurbsSurface":
                    cmds.reverseSurface(str(x))
                    x["opposite"] = False
                elif x.type_ == "mesh":
                    cmds.polyNormal(str(x), normalMode=0, constructionHistory=False)
                    x["opposite"] = False

        for locked_attrs in transform_locked_attrs:
            locked_attrs.set_locked(True)

        # self["rotatePivot"] = [0.0, 0.0, 0.0]
        # self["scalePivot"] = [0.0, 0.0, 0.0]

    def get_transform_locked_attrs(self):
        """Return locked translation, rotation, scale, and visibility Attr wrappers."""
        transform_attrs = [
            "tx",
            "ty",
            "tz",
            "rx",
            "ry",
            "rz",
            "sx",
            "sy",
            "sz",
            "visibility",
        ]

        return [self[attr] for attr in transform_attrs if self[attr].is_locked()]


class Attr:
    """Wrap an MPlug with value access, connections, and compound/array traversal.

    node is a Node wrapper and plug is an MPlug. name includes the node;
    attr_name omits it. short_name uses MPlug.partialName(). value reads
    scene data and type_ reports the Maya type. index is an array logical
    index or compound-child position, or -1 for top-level plugs. parent is
    the containing Attr or None. Arithmetic reads current values; >> and <<
    connect plugs, and ~ disconnects incoming connections."""

    __attr_data_map = {
        "kDoubleAngleAttribute": {
            "get": lambda x: x.asMAngle().asDegrees(),
            "set": lambda x, y: x.setDouble(om2.MAngle(y, 2).asRadians()),
        },
        "kDoubleLinearAttribute": {
            "get": lambda x: x.asDouble(),
            "set": lambda x, y: x.setDouble(y),
        },
        "kEnumAttribute": {"get": lambda x: x.asInt(), "set": lambda x, y: x.setInt(y)},
        "kNumericAttribute": {
            "get": lambda x: x.asDouble(),
            "set": lambda x, y: x.setDouble(y),
        },
    }

    def __init__(self, attr: Union[om2.MPlug, str], node: Node = None):
        """Resolve attr (MPlug or node-qualified path) and its optional Node wrapper."""
        self.node = None
        if node is not None:
            self.node = wrap_node(node)

        self.plug = _OMUtils.get_plug(None, attr)
        if self.plug is None:
            cmds.error(f'{attr} attribute"s plug not found')

        if self.node is None:
            self.node = wrap_node(Node(self.plug))

    @property
    def name(self):
        """Return the node unique name followed by the attribute path."""
        return f"{self.node.full_name}.{self.attr_name}"

    @property
    def attr_name(self):
        """Return the plug path without the node name, including children and indices."""
        return str(self.plug).split(".", 1)[1]

    @property
    def short_name(self):
        """Return the plug partialName() string."""
        return str(self.plug.partialName())

    @property
    def type_(self):
        """Return the Maya attribute type, normalizing TdataCompound to compound."""
        if cmds.getAttr(str(self), type=True) == "TdataCompound":
            return "compound"
        return cmds.getAttr(str(self), type=True)

    @property
    def value(self):
        """Read scene data; double3 values become Vector and matrix values become Matrix.

        Arrays return lists; compounds normally return tuples. Mapped angle
        reads are expressed in degrees."""
        return self._get_value(self.plug)

    @property
    def index(self):
        """Return the array logical index or compound-child position, otherwise -1."""
        if self.plug.isElement:
            return self.plug.logicalIndex()
        elif self.plug.isChild:
            parent_plug = self.plug.parent()
            child_plug_list = [
                parent_plug.child(x) for x in range(parent_plug.numChildren())
            ]
            child_attr_dict = {
                x.name().split(".", 1)[1]: i for i, x in enumerate(child_plug_list)
            }
            return child_attr_dict[self.attr_name]
        return -1

    @property
    def parent(self):
        """Return the containing array/compound Attr, or None for a top-level plug."""
        if self.plug.isElement:
            return Attr(self.plug.array(), self.node)
        elif self.plug.isChild:
            return Attr(self.plug.parent(), self.node)
        else:
            return None

    # helper functions
    @staticmethod
    def _plug_attr_type(plug: om2.MPlug):
        """Return the API type string of the plug attribute definition."""
        return plug.attribute().apiTypeStr

    def set_connect(self, attr_data, set_when_data_is_attr: bool = False):
        """Connect an Attr source, or set attr_data as the value.

        set_when_data_is_attr=True copies an Attr value instead of connecting it."""
        if set_when_data_is_attr and isinstance(attr_data, Attr):
            attr_data = attr_data.value

        if isinstance(attr_data, Attr):
            self << attr_data
        else:
            self.set(attr_data)

    def connect(self, attr: Attr):
        """Connect this source Attr to destination attr and register undo/redo.

        Temporarily unlock plugs and restore their locks on success. The helper
        falls back to a forced cmds connection on RuntimeError."""
        src_locked = self.is_locked()
        dest_locked = attr.is_locked()
        if src_locked:
            self.set_locked(False)
        if dest_locked:
            attr.set_locked(False)
        _OMUtils.connect_plugs(self.plug, attr.plug)
        if src_locked:
            self.set_locked(True)
        if dest_locked:
            attr.set_locked(True)

    def disconnect(
        self, children: bool = False, as_src: bool = False, as_dest: bool = True
    ):
        """Disconnect incoming links by default and register undo/redo.

        as_src=True also removes outgoing links; as_dest=False keeps incoming
        links. children=True attempts child disconnection, but currently calls
        an undefined child get_connection_list() method."""

        def redo(connection_pairs):
            dgMod = om2.MDGModifier()
            for connection in connection_pairs:
                dgMod.disconnect(connection[0], connection[1])
            dgMod.doIt()

        def undo(connection_pairs):
            dgMod = om2.MDGModifier()
            for connection in connection_pairs:
                dgMod.connect(connection[0], connection[1])
            dgMod.doIt()

        connection_pairs = []
        if children and self.has_children():
            for child_attr in self:
                if as_src:
                    for attr in child_attr.get_connection_list(True, False):
                        connection_pairs.append((child_attr.plug, attr.plug))
                if as_dest:
                    for attr in child_attr.get_connection_list(False, True):
                        connection_pairs.append((attr.plug, child_attr.plug))
        if as_src:
            for attr in self.get_connections(True, False):
                connection_pairs.append((self.plug, attr.plug))
        if as_dest:
            for attr in self.get_connections(False, True):
                connection_pairs.append((attr.plug, self.plug))

        if connection_pairs == []:
            cmds.warning(f"nothing to disconnect from {str(self.plug)}")
            return
        locked = self.is_locked()
        if locked:
            self.set_locked(False)
        redo(connection_pairs)
        apiundo.commit(
            redo=lambda: redo(connection_pairs), undo=lambda: undo(connection_pairs)
        )
        if locked:
            self.set_locked(True)

    def has_src_connection(self):
        """Return whether this attribute has an incoming source connection."""
        if self.get_src_connection() is None:
            return False
        return True

    def get_plug(self):
        """Return the underlying maya.api.OpenMaya.MPlug."""
        return self.plug

    def get_connections(self, as_src: bool, as_dest: bool):
        """Return connected plugs as Attr wrappers.

        as_src selects outgoing destinations; as_dest selects incoming sources."""
        return [Attr(x, None) for x in self.plug.connectedTo(as_dest, as_src)]

    def get_src_connection(self):
        """Return the first incoming source Attr, or None when unconnected."""
        connection_list = self.get_connections(False, True)
        if connection_list == []:
            return None
        else:
            return connection_list[0]

    def get_dest_connections(self):
        """Return outgoing destination Attr wrappers as a list."""
        return self.get_connections(True, False)

    # functions
    def set(self, value):
        """Set a value or copy another Attr value, with undo/redo.

        Warn and leave connected destinations unchanged. On ValueError or
        RuntimeError, attempt to restore the previous value and warn."""
        orig_val = self.value

        def do(plug, value):
            if isinstance(value, Attr):
                value = value.value
            self._set_value(plug, value)

        if self.has_src_connection():
            cmds.warning(
                f"{self.plug} is connected to {self.get_src_connection().plug}. cannot be set"
            )
            return

        try:
            do(self.plug, value)
        except ValueError:
            self._set_value(self.plug, orig_val)
            cmds.warning(f"set info, mismatch {str(self.plug)} was not changed")
        except RuntimeError:
            self._set_value(self.plug, orig_val)
            cmds.warning(f"set info, mismatch {str(self.plug)} was not changed")

        apiundo.commit(
            redo=lambda: do(self.plug, value), undo=lambda: do(self.plug, orig_val)
        )

    def set_locked(self, lock):
        """Set the attribute lock state to lock through cmds.setAttr()."""
        cmds.setAttr(str(self), lock=lock)

    def is_locked(self):
        """Return whether the attribute is locked."""

        return cmds.getAttr(str(self), lock=True)

    def set_keyable(self, keyable):
        """Set keyability on this attribute and recursively on its children."""
        cmds.setAttr(str(self), edit=True, keyable=keyable)
        if self.has_children():
            for child in self:
                child.set_keyable(keyable)


    def is_keyable(self):
        """Return whether the attribute is keyable."""
        return cmds.getAttr(str(self), keyable=True)

    def set_alias(self, alias: str):
        """Set the attribute alias to alias."""
        cmds.aliasAttr(alias, self.name)

    def has_attr(self, child_attr: str):
        """Query child_attr through cmds.attributeQuery using the current command call.

        The call passes str(self) as a second positional argument; this method
        does not traverse child plugs."""
        return cmds.attributeQuery(child_attr, str(self), exists=True)

    def _set_value(self, plug: om2.MPlug, value):
        """Recursively write array elements and compound children.

        Short array inputs leave trailing elements intact. Compound length
        mismatches raise ValueError. Restore this Attr lock on success; mapped
        angle writes interpret degrees."""
        attr_type = self.type_
        locked = self.is_locked()
        if locked:
            self.set_locked(False)
        if plug.isArray:
            for index in range(len(value)):
                curr_plug = plug.elementByLogicalIndex(index)
                self._set_value(curr_plug, value[index])
        elif plug.isCompound:
            num_plug_element_list = plug.numChildren()
            if num_plug_element_list != len(value):
                raise ValueError()
            for index in range(num_plug_element_list):
                curr_plug = plug.child(index)
                self._set_value(curr_plug, value[index])
        elif attr_type == "string":
            cmds.setAttr(str(self), value, type="string")
        elif attr_type == "matrix":
            cmds.setAttr(str(self), value, type="matrix")
        elif attr_type == "enum":
            if isinstance(value, str):
                if not hasattr(self, "enum_list"):
                    self.enum_list = cmds.attributeQuery(
                        self.short_name, node=str(self.node), listEnum=True
                    )[0].split(":")
                index = self.enum_list.index(value)
                if index != -1:
                    value = index
            cmds.setAttr(str(self), value)

        elif self._plug_attr_type(plug) in self.__attr_data_map.keys():
            self.__attr_data_map[self._plug_attr_type(plug)]["set"](plug, value)
        else:
            cmds.setAttr(str(self), value)

        if locked:
            self.set_locked(True)

    def _get_value(self, plug: om2.MPlug):
        """Read a plug recursively using API mappings or cmds.getAttr fallback.

        Arrays visit logical indices 0..numElements()-1, rather than existing
        sparse indices. Compounds return tuples before value casting."""

        # try:
        return_value = None
        if plug.isArray:
            plug_list = [
                plug.elementByLogicalIndex(i) for i in range(plug.numElements())
            ]
            return_value = [self._get_value(x) for x in plug_list]
        elif plug.isCompound:
            plug_list = [plug.child(i) for i in range(plug.numChildren())]
            return_value = tuple([self._get_value(x) for x in plug_list])
        elif self._plug_attr_type(plug) in self.__attr_data_map.keys():
            return_value = self.__attr_data_map[self._plug_attr_type(plug)]["get"](plug)
        if return_value is None:
            return_value = cmds.getAttr(str(self))
        # casting it
        if self.type_ == "double3" and isinstance(return_value, tuple):
            return_value = Vector(return_value)
        elif self.type_ == "matrix" and return_value is not None:
            return_value = Matrix(return_value)

        return return_value

    def __eq__(self, other):
        """Return whether other is an Attr with the same node-qualified name."""
        if isinstance(other, Attr):
            return str(self) == str(other)
        return False

    def __hash__(self):
        """Return an integer hash of the current node-qualified name."""
        return hash(str(self))

    # Operator overloads connections and disconnections as well as get item
    def __str__(self):
        """Return the current node-qualified attribute name."""
        return self.name

    def __rshift__(self, other):
        """Connect this Attr to other; return None."""
        if isinstance(other, Attr):
            self.connect(other)
        else:
            cmds.error("{other} not of type Attr")

    def __lshift__(self, other):
        """Connect other to this Attr; return None."""
        if isinstance(other, Attr):
            other.connect(self)
        else:
            cmds.error(f"{other} not of type Attr")

    def __invert__(self):
        """Disconnect incoming connections and return this Attr."""
        self.disconnect()
        return self

    def __getitem__(self, attr):
        """Return a child Attr by compound name/position or logical array index."""
        full_attr_name = self.attr_name
        error_str = None
        error_type = None
        try:
            if self.plug.isArray:
                full_attr_name = f"{full_attr_name}[{attr}]"
            elif self.plug.isCompound:
                full_attr_name = f"{full_attr_name}.{attr}"

            if full_attr_name in self.node.get_attr_cache().keys():
                return self.node.get_attr_cache()[full_attr_name]

            plug = _OMUtils.get_plug(self.plug, attr)
            return Attr(plug, self.node)
        except AttributeError:
            error_str = (
                f'{self.node} does not have attribute "{self.short_name}.{attr}"'
            )
            error_type = AttributeError

        if error_str is not None:
            raise error_type(error_str)

    def __setitem__(self, attr: str, new_value):
        """Set a child by name/index, copying new_value.value when it is an Attr."""
        attr = self.__getitem__(attr)
        if isinstance(new_value, Attr):
            new_value = new_value.value
        attr.set(new_value)

    def has_children(self):
        """Return whether the plug is an array or compound, including empty arrays."""
        return self.plug.isArray or self.plug.isCompound

    def get_all_children_dict(self) -> dict[str, "Attr"]:
        """Return descendant leaf Attr wrappers keyed by relative short names.

        Keys remove occurrences of this attribute short name. Raise TypeError
        for a plug that is neither array nor compound."""
        if not self.has_children():
            raise TypeError(f"{self} does not have children")

        has_children_list = deque()
        has_children_list.append(self)

        attr_dict = {}
        while len(has_children_list):
            curr_attr = has_children_list.pop()
            if curr_attr.has_children():
                for attr in curr_attr:
                    if attr.has_children():
                        has_children_list.append(attr)
                    else:
                        key = attr.short_name.replace(self.short_name, "")
                        attr_dict[key] = attr
            else:
                key = curr_attr.short_name.replace(self.short_name, "")
                attr_dict[key] = curr_attr

        return attr_dict

    def get_indicies(self):
        """Return existing logical array indices as a list; raise TypeError for non-arrays."""
        try:
            return list(self.plug.getExistingArrayAttributeIndices())
        except TypeError:
            raise TypeError(f"{self} does not have indicies")

    def remove_index(self, rem_index: int, shift_down: bool = True):
        """Remove rem_index, shifting later element data down when shift_down=True.

        The default is True; data and connections move into preceding existing
        index slots. Raise IndexError for an absent index. With shift_down=False,
        the current implementation leaves the last existing index untouched."""

        def __reconnect_attr(src_attr: Attr, dest_attr: Attr):
            """Copy a leaf value or source connection and redirect outgoing connections."""
            if src_attr.has_src_connection():
                src_attr.get_src_connection() >> dest_attr
            else:
                dest_attr.set(src_attr.value)
            dest_connections = src_attr.get_dest_connections()
            for dest_conn_attr in dest_connections:
                dest_attr >> ~dest_conn_attr

        attr_indicies = self.get_indicies()
        if rem_index not in attr_indicies:
            raise IndexError(f"Index not found in {self}")

        list_find_index = attr_indicies.index(rem_index)

        for list_index, attr_index in enumerate(attr_indicies[list_find_index:-1]):
            curr_attr = self.__getitem__(attr_index)
            next_attr = self.__getitem__(
                attr_indicies[list_index + list_find_index + 1]
            )

            cmds.removeMultiInstance(str(curr_attr), b=True)
            if not shift_down:
                return
            curr_attr = self.__getitem__(attr_index)

            if next_attr.has_children():
                next_attr_dict = next_attr.get_all_children_dict()

                for key, child_attr in next_attr_dict.items():
                    __reconnect_attr(src_attr=child_attr, dest_attr=curr_attr[key])

            else:
                __reconnect_attr(src_attr=next_attr, dest_attr=curr_attr)

        if shift_down:
            cmds.removeMultiInstance(str(self.__getitem__(attr_indicies[-1])), b=True)

    def next_index(self):
        """Return zero for an empty array, otherwise the highest existing index plus one."""
        if self.__len__() == 0:
            return 0
        return self.get_indicies()[-1] + 1

    def next_index_attr(self):
        """Return an Attr for next_index() without assigning a stored value."""
        return self.__getitem__(self.next_index())

    def __len__(self):
        """Return existing array element count or compound child count.

        For scalar plugs this method returns None, so len(attr) raises TypeError."""
        if self.plug.isArray:
            curr_len = cmds.getAttr(str(self), multiIndices=True)
            if curr_len is None:
                return 0
            return len(curr_len)
            # return self.plug.numElements()
        elif self.plug.isCompound:
            return self.plug.numChildren()

    # Iterator overloads
    def __iter__(self):
        """Yield existing array elements or compound children as Attr wrappers.

        Raise TypeError for scalar plugs."""
        if not self.has_children():
            raise TypeError("attribute is not of type compound or array")
        index_list = range(self.__len__())
        if self.plug.isArray:
            index_list = self.get_indicies()
        for index in index_list:
            yield self.__getitem__(index)

    # Math Operator Overloads
    def _base_math_operators(self, x, y, function):
        """Read Attr operands as current values and return function(x, y)."""
        if isinstance(x, Attr):
            x = x.value
        if isinstance(y, Attr):
            y = y.value
        return function(x, y)

    def __add__(self, other):
        """Return self.value + other, reading other.value if it is an Attr."""
        return self._base_math_operators(self, other, lambda x, y: x + y)

    def __radd__(self, other):
        """Return other + self.value, reading other.value if it is an Attr."""
        return self._base_math_operators(self, other, lambda x, y: y + x)

    def __sub__(self, other):
        """Return self.value - other, reading other.value if it is an Attr."""
        return self._base_math_operators(self, other, lambda x, y: x - y)

    def __rsub__(self, other):
        """Return other - self.value, reading other.value if it is an Attr."""
        return self._base_math_operators(self, other, lambda x, y: y - x)

    def __mul__(self, other):
        """Return self.value * other, reading other.value if it is an Attr."""
        return self._base_math_operators(self, other, lambda x, y: x * y)

    def __rmul__(self, other):
        """Return other * self.value, reading other.value if it is an Attr."""
        return self._base_math_operators(self, other, lambda x, y: y * x)

    def __truediv__(self, other):
        """Return self.value / other, reading other.value if it is an Attr."""
        return self._base_math_operators(self, other, lambda x, y: x / y)

    def __rtruediv__(self, other):
        """Return other / self.value, reading other.value if it is an Attr."""
        return self._base_math_operators(self, other, lambda x, y: y / x)
