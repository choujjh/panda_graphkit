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
    @classmethod
    def try_int(cls, s):
        try:
            return int(s)
        except (TypeError, ValueError):
            return None

    @classmethod
    def get_dep_node(cls, node: Union[om2.MObject, om2.MPlug, str]):
        """Converts to dependency node using input. if none found None
        will be returned

        Args:
            node (Union[om2.MObject, om2.MPlug, str]): input to convert
            to dependency node

        Returns:
            Union[None, om2.MFnDependencyNode]:
        """
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
        """Returns the child plug of "plug" given a child attribute.
        returns all child plugs in a dict{attribute:plug} if "attr" is None

        Args:
            plug (om2.MPlug): parent plug of attr
            attr (str): attribute to find

        Returns:
            Union[om2.MPlug, dict{str, om2.MPlug}: child MPlug
        """
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
        """Returns the given attribute as a plug. If attr_parent is
        provided it finds the attribute under that parent (either a
        dependency node or another plug) as a plug

        Args:
            attr (Union[om2.MPlug, str]):
            attr_parent (Union[om2.MPlug, om2.MFnDependencyNode, str],
            optional): parent of attribute. Defaults to None. When none
            find"s dependency node of attr

        Returns:
            om2.MPlug:
        """

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
        """Connects source plug to destination plug

        Args:
            src_plug (om2.MPlug):
            dest_plug (om2.MPlug):
        """

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
    """Class for matrix operations derived from MMatrix"""

    def __init__(self, *args):
        """Initializes with list of values up to 16

        Args:
            args: list of values to add, if first one is nw.Attr gets values
            from that

        """
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
        """Gets value in cell

        Args:
            r (int): row
            c (int): column

        Returns:
            float:
        """
        return self[r * 4 + c]

    def setT(self, t):
        """Sets transform matrix

        Args:
            t (list): sets x,y,z transform values
        """
        self[12] = t[0]
        self[13] = t[1]
        self[14] = t[2]

    def __str__(self):
        """Returns string of translate, rotate, and scale values

        Returns:
            str:
        """
        return (
            f"Translate: {self.translate} | Rotate: {self.rotate} | Scale: {self.scale}"
        )

    @property
    def rotate(self):
        """Gets rotation values

        Returns:
            list:
        """
        return self.as_degrees

    @property
    def translate(self):
        """Gets translate values

        Returns:
            list:
        """
        return self[12], self[13], self[14]

    @property
    def scale(self):
        """Gets Scale values

        Returns:
            list:
        """
        z_scalar = 1
        if self.det4x4() < 0:
            z_scalar = -1
        return (
            om2.MVector(self.column(0)).length(),
            om2.MVector(self.column(1)).length(),
            om2.MVector(self.column(2)).length() * z_scalar,
        )

    def column(self, index):
        """returns a value column of the matrix

        Args:
            index (int):

        Returns:
            list: matrix column
        """
        i = index * 4
        return self[i], self[i + 1], self[i + 2]

    @property
    def as_radians(self):
        """Gets rotation as radians

        Returns:
            list:
        """
        rx, ry, rz, ro = om2.MTransformationMatrix(self).rotationComponents(
            asQuaternion=False
        )
        return rx, ry, rz

    @property
    def as_degrees(self):
        """Gets rotation as degrees

        Returns:
            list:
        """
        rx, ry, rz, ro = om2.MTransformationMatrix(self).rotationComponents(
            asQuaternion=False
        )
        return math.degrees(rx), math.degrees(ry), math.degrees(rz)

    @property
    def quaternion(self):
        """Gets quaternion values

        Returns:
            list:
        """
        return om2.QuaternionOrPoint().setValue(self)

    def set_transform(self, transform: "Transform", world_space: bool = False):
        """Sets tranform with it's contained matrix

        Args:
            transform (nw.Transform):
            world_space (bool, optional): Defaults to False.
        """
        cmds.xform(str(transform), worldSpace=world_space, matrix=list(self))

    @classmethod
    def identity_matrix(cls):
        """Returns identity matrix in an array

        Returns:
            list:
        """
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
        """Returns zero matrix in an array

        Returns:
            list:
        """
        return cls([0.0 for x in range(16)])

    @classmethod
    def translate_matrix(cls, *translation):
        """Returns translation matrix in an array

        Args:
            translation (list): list of values for translation x, y, z

        Returns:
            list:
        """
        matrix = cls.identity_matrix()
        translation = make_len(list(translation), len_=3, default=0)
        matrix[12] = translation[0]
        matrix[13] = translation[1]
        matrix[14] = translation[2]

        return cls(matrix)

    @classmethod
    def scale_matrix(cls, *scale):
        """Returns translation matrix in an array

        Args:
            translation (list): list of values for translation x, y, z

        Returns:
            list:
        """
        matrix = cls.identity_matrix()
        scale = make_len(list(scale), len_=3, default=1)
        matrix[0] = scale[0]
        matrix[5] = scale[1]
        matrix[10] = scale[2]

        return matrix


class Vector(om2.MVector):
    """Vector inherited from om2.Vector"""

    def __add__(self, other):
        return Vector(super().__add__(other))

    def __iadd__(self, other):
        return Vector(super().__iadd__(other))

    def __imul__(self, other):
        return Vector(super().__imul__(other))

    def __isub__(self, other):
        return Vector(super().__isub__(other))

    def __itruediv__(self, other):
        return Vector(super().__itruediv__(other))

    def __mul__(self, other):
        return Vector(super().__mul__(other))

    def __neg__(self):
        return Vector(super().__neg__())

    def __radd__(self, other):
        return Vector(super().__radd__(other))

    def __rmul__(self, other):
        return Vector(super().__rmul__(other))

    def __rsub__(self, other):
        return Vector(super().__rsub__(other))

    def __rtruediv__(self, other):
        return Vector(super().__rtruediv__(other))

    def __rxor__(self, other):
        """crosses the vector with another

        Args:
            other (any):

        Returns:
            Vector:
        """
        return Vector(super().__rxor__(other))

    def __sub__(self, other):
        return Vector(super().__sub__(other))

    def __truediv__(self, other):
        return Vector(super().__truediv__(other))

    def __xor__(self, other):
        """crosses the vector with another

        Args:
            other (any):

        Returns:
            Vector:
        """
        return Vector(super().__xor__(other))


def wrap_node(node, **attr_data_dict):
    """Gets the most specific node type ie. Node, Container

    Args:
        Node (str, Node): sets the right class for given class

    Returns:
        Node: The most spicific node type
    """
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
    """Creates node with given name

    Args:
        node_type (str): type of node to create
        name (str): name to be given to created node

    Returns:
        Node: node that was created wrapped by Node class
    """
    if name is None:
        return wrap_node(cmds.createNode(node_type), **attr_data_dict)
    return wrap_node(cmds.createNode(node_type, name=name), **attr_data_dict)


def exists(node):
    """Checks to see if node still exists in the scene

    Args:
        node (Node, str): node to check

    Returns:
        bool: if node still exists
    """
    return cmds.objExists(str(node))


def delete_node(node: Node):
    """Delete a node from the current Maya scene.

    Args:
        node: Node wrapper or node name identifying the node to delete.
    """
    cmds.delete(str(node))


def _snake_to_camel(snake_str):
    """Snake case to camel case

    Args:
        snake_str (str):

    Returns:
        str:
    """
    # Split the string by underscores
    if snake_str.find("fk") > 0:
        snake_str = snake_str.replace("fk", "FK")
    if snake_str.find("ik") > 0:
        snake_str = snake_str.replace("ik", "IK")
    components = snake_str.split("_")
    # Capitalize the first letter of each component except the first one, and join them
    camel_case_str = components[0] + "".join(x.title() for x in components[1:])
    return camel_case_str


def kwarg_to_dict(**kwarg_dict):
    return kwarg_dict


def make_len(curr_list: list, len_: int, default=0.0):
    """Makes a list a certain len

    Args:
        curr_list (list):
        len_ (int):
        default (float, optional): . Defaults to 0.0.

    Returns:
        list:
    """

    curr_list_len = len(curr_list)
    if curr_list_len < len_:
        ending_list = [default for x in range(len_ - curr_list_len)]
        curr_list.extend(ending_list)
        return curr_list
    elif curr_list_len > len_:
        return curr_list[:len_]
    return curr_list


class AttrTypes(Enum):
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


class Node:
    """A class to wrap around OpenMaya objects (MObject, MFnDependencyNode) and
    provides useful functionality such as getting attributes, and other
    data not simply extracted from said OpenMaya objects

    Attributes:
        full_name (str): returns full name of node ie. parent2|parent1|name
        name (str): returns node name ie. name
        type_ (str): node type
        mobject (maya.api.OpenMaya.MObject): MObject
    """

    def __init__(self, node):
        """Initializes wrapped node getting the MFnDependencyNode

        Args:
            Node (Node, str, OpenMaya.MObject, OpenMaya.MPlug): input to get MFnDependencyNode

        Returns:
            Node: built node
        """
        if isinstance(node, str):
            if not exists(node):
                cmds.error(f"node {node} does not exist")
                return
        self._dep_node = _OMUtils.get_dep_node(node)
        self.__attr_cache = {}
        self.__full_attr_list = None

    # properties
    @property
    def full_name(self):
        """Full name of node including all parents with |

        Returns:
            str: full name
        """
        # return self._dep_node_.absoluteName()
        return self._dep_node.uniqueName()

    @property
    def name(self):
        """Returns full name of node with no parent names included

        Returns:
            str: name of node
        """
        if self.full_name.find("|") != -1:
            return self.full_name.rsplit("|", 1)[1]
        return self.full_name

    @property
    def type_(self):
        """Returns type of node

        Returns:
            str: node type
        """
        return self._dep_node.typeName

    @property
    def mobject(self):
        """Returns MObject of this node using the MFnDependencyNode

        Returns:
            maya.api.OpenMaya.MObject:
        """
        return self._dep_node.object()

    def has_attr(self, attr_name):
        """Checks if node has attribute

        Returns:
            bool:
        """
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
        """add_attributes to node. sorts and uses adds attribute

        Args:
            keyable_ (bool, optional): Defaults to True.
            attr_name_camel_case(bool, optional): Defaults to True.
        """

        def _flatten_validate_dict(
            main_dict: dict,
            sub_dict: dict = {},
            parent_key: str = "",
            attr_name_camel_case: bool = True,
        ):
            """Flattens the dictionary with it's appropriate parent as well as
            makes things into camel case when specified

            Args:
                main_dict (_type_): main dictionary that everything is saved to
                sub_dict (dict, optional): sub dictionary to get recurssively. Defaults to {}. at default is set to main_dict
                parent_key (str, optional): parent string. Defaults to "".
                attr_name_camel_case (bool, optional): Defaults to True.
            """
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
                        if any(
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
        """Adds attribute to node with given kwargs (kwargs from cmds.addAttr).
        also handles type instead of needing to use \"dataType\" or \"attributeType\"

        Args:
            name (str): name of attribute to be added
            type_ (AttrTypes, str): the type of attribute
            kwarg: added cmds.addAttr arguments

        Returns:
            Node: built node
        """
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
        """Deletes attribute on node

        Args:
            attr (Attr, str): attribute to delete
        """
        cmds.deleteAttr(str(self), at=attr)

    def get_connection_list(self, as_src, as_dest):
        """Gets connection list from node

        Args:
            as_src (bool): get list of connections when node is source
            as_dest (bool): get list of connections when node is destination

        Returns:
            list(Attr): list of connected attributes in touples where the first is the source attr and the secound is the destination attr
        """
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
            if x[0].node.node_type != "hyperLayout"
            and x[1].node.node_type != "hyperLayout"
        ]
        return connections

    def _check_node_in_attr_list(self, attribute_list):
        """Check to see if all attrs in attribute list is in node

        Args:
            attribute_list (list(str)): attribute list to check

        Returns:
            list: list of attributes now converted to Attr objects
        """
        if attribute_list:
            attribute_list = [self[x] for x in attribute_list]
            attribute_list = [x for x in attribute_list if x.node == self]
            return attribute_list
        return []

    def delete_node(self, clean=True):
        """Delete node

        Args:
            clean: only delete node and no connections or children
        """
        if not exists(self):
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
        """Gets container of node

        Returns:
            Node: container node. if no container, returns None
        """
        container = cmds.container(findContainer=self.full_name, query=True)
        if container is not None:
            return Container(container)
        return container

    def get_top_level_attribute_list(self, re_cache=False):
        """Gets a list of top level attr for the node (no child attributes included)

        Args:
            re_cache (int): reCaches Attributes. Defaults to False

        Returns:
            list(Attr): the list of attributes that are the top level
        """

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
        """Returns Dependency Node

        Returns:
            OpenMaya.MFnDependencyNode:
        """
        return self._dep_node

    def get_attr_cache(self):
        """Returns attribute cache

        Returns:
            dict:
        """
        return self.__attr_cache

    def rename(self, new_name: str):
        """Renames wrapped node

        Args:
            new_name (str):
        """
        curr_name = self.name
        self._dep_node.setName(new_name)
        apiundo.commit(
            undo=lambda: self._dep_node.setName(curr_name),
            redo=lambda: self._dep_node.setName(new_name),
        )

    def set_connect_attr_data_dict(self, **attr_data_dict):
        """
        Connect to attribute if it can, but sets data otherwise.
        does it for every element of the dictionary
        """
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
        """Connect to attribute if it can, but sets data otherwise

        Args:
            attr_name (str):
            data (Any):
            set_when_data_is_attr (bool):
        """
        if not self.has_attr(attr_name):
            cmds.warning(f"{self.name}.{attr_name} doesn't not exist.")
            return

        self[attr_name].set_connect(attr_data, set_when_data_is_attr)

    # operator overloads
    def __str__(self):
        """String representation of node. returns self.full_name

        Returns:
            str:
        """
        return self.full_name

    def __getitem__(self, attr: str):
        """Gets the attr of a node wrapped in the Attr class

        Args:
            attr (str): attribute name

        Returns:
            Attr: returns Attr class of node's attribute
        """
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
        """Sets the attribute"s value of a given node

        Args:
            attr (str): attribute name
            new_value (Any): value to set attribute to
        """
        attr = self.__getitem__(attr)
        attr.set(new_value)

    def _get_cached_attr(self, attr):
        """Gets and caches the attr locally

        Args:
            attr (str): attribute name

        Returns:
            Attr: returns Attr class of nodes attribute
        """
        if attr not in self.__attr_cache.keys():
            self.__attr_cache[attr] = Attr(
                _OMUtils.get_plug(self._dep_node, attr), self
            )
        return self.__attr_cache[attr]

    def __eq__(self, other):
        """Returns True if the other object is of type Node and the
        other's plug matches self's plug

        Args:
            other (Any):

        Returns:
            bool:
        """
        if isinstance(other, Node):
            if str(self) == str(other):
                return True

        return False

    def __hash__(self):
        """Hash value using objects full name"""
        return hash(self.full_name)


class Container(Node):
    """A class to wrap around OpenMaya objects (MObject, MFnDependencyNode)
    specifically for container objects and provides useful functionality
    such as getting attributes, and other data not simply extracted from
    said OpenMaya objects. Derived from Node

    Attributes:
        full_name (str): returns full name of node ie. parent2|parent1|name
        name (str): returns node name ie. name
        type (str): node type
        mobject (maya.api.OpenMaya.MObject): MObject
    """

    def __init__(self, node):
        """Initializes wrapped node getting the MFnDependencyNode

        Args:
            Node (Node, str, OpenMaya.MObject, OpenMaya.MPlug): input to get MFnDependencyNode

        Returns:
            Node: built container node
        """
        super(Container, self).__init__(node)

    def get_nodes(self):
        """Gets all nodes inside container

        Returns:
            list(Node): list of wrapped nodes of all nodes inside container
        """
        child_nodes = cmds.container(str(self), query=True, nodeList=True)
        if child_nodes:
            return [Node(x) for x in child_nodes]

    def lock(self, proprigate=False):
        """Locks container

        Args:
            propigate (bool): if True, locks all containers that are the parents of this container
            y (int): The second number.
        """
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
        """Unlocks container

        Args:
            propigate (bool): if True, unlocks all containers that are the parents of this container
            y (int): The second number.
        """

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
        """Unlocks when keyword with is used"""
        self.unlock()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """Locked when exited"""
        self.lock()

    def add_nodes(
        self,
        *args,
        include_network=False,
        include_hierarchy_above=False,
        include_hierarchy_below=False,
        force=False,
    ):
        """Adds nodes to container

        Args:
            args (list(Node)): the nodes to be added
            include_network (bool): include network of nodes to be added
            include_hierarchy_above (bool): include above hierarchy of nodes to be added
            include_hierarchy_below (bool): includes child hierarchy of nodes to be added
            force (bool): forces adding of nodes
        """
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
        """Overidden get container command

        Returns:
            Node: parent Container. None if no container found
        """
        containers = cmds.container(str(self), query=True, parentContainer=True)
        if containers is not None:
            return Container(containers[0])
        return containers

    def remove_nodes(self, *args, all_descendents=False):
        """Removes specified nodes from container. removes all nodes if no args
        are given

        Args:
            args (list): nodes to be removed from container
        """
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
        """Publish attributes to container

        Args:
            attr (Attr): Attribute to be published
            attr_bind_name (str): Attribute published name
        """
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
        """Unpublish attr

        Args:
            attr (Attr): attribute to be unpublished
        """
        cmds.container(str(self), edit=True, unbindAndUnpublish=str(attr))

    def get_published_attr_map(self):
        """Get published attributes in a map with the key being the attribute name
        and value being the Attrs

        Returns:
            dict(str:Attr): dict where the attribute name is the key and Attr is the value
        """

        m_object = self.mobject
        if m_object.hasFn(om2.MFn.kContainer):
            mfn_container = om2.MFnContainerNode(m_object)
            plug_list, attr_list = mfn_container.getPublishedPlugs()
            return {x: Attr(y, None) for x, y in zip(attr_list, plug_list)}
        return {}

    def get_published_attrs(self):
        """Get published attributes

        Returns:
            list(Attr): list of attrs that are published
        """
        m_object = self.mobject
        if m_object.hasFn(om2.MFn.kContainer):
            mfn_container = om2.MFnContainerNode(m_object)
            plug_list, _ = mfn_container.getPublishedPlugs()
            return [Attr(x, None) for x in plug_list]
        return []

    def get_external_connection_list(self):
        """Gets all connections that are from outside the container to inside the container

        Returns:
            list(Attr): gets connection list touple where first attr is the source and second is the destination
        """
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
        """Gets children containers all goes through the hierarchy of containers

        Args:
            all (bool): gets all children in hierarchy not just top level

        Returns:
            list(Container): list of child containers
        """
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
        """Sets attribute on container. overriden so that values could be set on published attributes

        Args:
            attr (str): Attribute name to search for.
            new_value (_value_): new value to set.
        """
        publish_attr_map = self.get_published_attr_map()
        if attr in publish_attr_map.keys():
            attr = publish_attr_map[attr]
            attr.set(new_value)
        else:
            super().__setitem__(attr, new_value)

    def __getitem__(self, attr: str):
        """Gets attribute on container. overriden so that attributes found can be published attributes

        Args:
            attr (str): Attribute name to search for.

        Returns:
            Attr: attribute found with attr as the key
        """
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
    """Node wrapper for transform node. has some functions only used by transform"""

    def get_shapes(self):
        """Get object shapes

        Returns:
            list(Node): list of shapes wrapped by Node
        """
        shapes = cmds.listRelatives(str(self), shapes=True, fullPath=True)
        if shapes is None:
            return []
        return [wrap_node(shape) for shape in shapes]

    def freeze_transforms(self):
        """Freezes the transforms of the given node"""
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
        """Get's the transforms important attributes. Filtered by if the attribute
        is locked

        Returns:
            list(Attr): Returns list of all attrs that are locked
        """
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
    """A class to wrap around MPlug object and
    provides useful functionality such as getting child attributes, and other
    data not simply extracted from said OpenMaya objects

    Attributes:
        __attr_data_map__ (dict): map to get or set the attribute
        dep_node (Node): node that"s the node of this plug
        plug (str): plug of the given attribute
        name(str): attr name with node name ie. node.attr
        attr_name(str): attr name ie. attr
        short_name(str): short name of attribute
        type_(str): plug"s attribute type
        value(Any): value that is stored in attribute
        index(int): the index of the attribute. returns -1 if not a child of
        another attribute
        parent(Attr): returns the parent of the attribute. returns None if
        not a child of another attribute
    """

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
        """Initializes Attr data by getting MPlug and setting it's Node

        Args:
            attr (Union[om2.MPlug, str]):
            node (Node): plug's node
        """
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
        """Name of the attribute with its node name ie. {node}.{attr}

        Returns:
            str:
        """
        return f"{self.node.full_name}.{self.attr_name}"

    @property
    def attr_name(self):
        """Name of the attribute without its node name ie. {attr}

        Returns:
            str:
        """
        return str(self.plug).split(".", 1)[1]

    @property
    def short_name(self):
        """Attribute's short name

        Returns:
            str:
        """
        return str(self.plug.partialName())

    @property
    def type_(self):
        """Returns attribute type name

        Returns:
            str:
        """
        if cmds.getAttr(str(self), type=True) == "TdataCompound":
            return "compound"
        return cmds.getAttr(str(self), type=True)

    @property
    def value(self):
        """Gets value stored in attribute

        Returns:
            Any:
        """
        return self._get_value(self.plug)

    @property
    def index(self):
        """Returns index of attribute. -1 if not a child attribute

        Returns:
            int: index, returns -1 if no index found
        """
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
        """Gets parent attribute. None if no parent found

        Returns:
            Attr:
        """
        if self.plug.isElement:
            return Attr(self.plug.array(), self.node)
        elif self.plug.isChild:
            return Attr(self.plug.parent(), self.node)
        else:
            return None

    # helper functions
    @staticmethod
    def _plug_attr_type(plug: om2.MPlug):
        """Get"s a plug"s attribute type

        Args:
            plug (om2.MPlug):

        Returns:
            str:
        """
        return plug.attribute().apiTypeStr

    def set_connect(self, attr_data, set_when_data_is_attr: bool = False):
        """Connect to attribute if it can, but sets data otherwise

        Args:
            attr_name (str):
            data (Any):
            set_when_data_is_attr (bool):
        """
        if set_when_data_is_attr and isinstance(attr_data, Attr):
            attr_data = attr_data.value

        if isinstance(attr_data, Attr):
            self << attr_data
        else:
            self.set(attr_data)

    def connect(self, attr: Attr):
        """Connect this attribute to a destination attribute.

        Temporarily unlocks either attribute when necessary, creates an
        undoable Maya API connection, and restores the original lock states.

        Args:
            attr: Destination attribute for this source attribute.
        """
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
        """Disconnects attributes

        Args:
            children (bool, optional): if true disconnects children. Defaults to False.
            asSource (bool, optional): if true disconnects everything it's connected to. Defaults to False.
            asDestination (bool, optional): if true disconnects everything connected to it. Defaults to True.
        """

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
        """Returns if attribute has source connection

        Returns:
            bool:
        """
        if self.get_src_connection() is None:
            return False
        return True

    def get_plug(self):
        """Gets MPlug of attribute

        Returns:
            OpenMaya.MPlug:
        """
        return self.plug

    def get_connections(self, as_src: bool, as_dest: bool):
        """Get connections of attr

        Args:
            source (bool): get connections with attr as source
            destination (bool): get connections with attr as destination

        Returns:
            om2.MPlug:
        """
        return [Attr(x, None) for x in self.plug.connectedTo(as_dest, as_src)]

    def get_src_connection(self):
        """Gets a list of all the Attr that are connected to this Attr

        Returns:
            list(Attr):
        """
        connection_list = self.get_connections(False, True)
        if connection_list == []:
            return None
        else:
            return connection_list[0]

    def get_dest_connections(self):
        """Gets a list of all the Attr that this Attr is connected to (this
        Attr being the source)

        Returns:
            list(Attr):
        """
        return self.get_connections(True, False)

    # functions
    def set(self, value):
        """Tries to set value of plug but resets to previous values if
        unsuccessful

        Args:
            value (any):
        """
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
        """Sets attribute lock

        Args:
            lock (bool):
        """
        cmds.setAttr(str(self), lock=lock)

    def is_locked(self):
        """Returns if attribute is locked

        Returns:
            bool:
        """

        return cmds.getAttr(str(self), lock=True)

    def set_keyable(self, keyable):
        """Sets attribute's keyable

        Args:
            keyable (bool):
        """
        cmds.setAttr(str(self), edit=True, keyable=keyable)

    def is_keyable(self):
        """Returns if attribute is keyable

        Returns:
            bool:
        """
        return cmds.getAttr(str(self), keyable=True)

    def set_alias(self, alias: str):
        """Sets attribute's alias

        Args:
            alias (str): new alias for the attribute
        """
        cmds.aliasAttr(alias, self.name)

    def has_attr(self, child_attr: str):
        """Returns if it has attribute

        Args:
            sub_attr (str): child attribute's name

        Returns:
            bool:
        """
        return cmds.attributeQuery(child_attr, str(self), exists=True)

    def _set_value(self, plug: om2.MPlug, value):
        """Sets value on plug. is recurrsive when plug is has children or
        elements.
        Limitation if a list if given that's smaller than the
        number of values in the node's array then it won't be resized and
        the old values stay

        Args:
            plug (om2.MPlug): plug to get value from
            value ():

        Raises:
            ValueError: if number of children is mismatched by length of
            value
        """
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
        """Gets value on plug. is recurrsive when plug is has children or
        elements

        Args:
            plug (om2.MPlug): plug to get value(s) from

        Returns:
        """

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
        """Returns True if the other object is of type Attr and the
        other's plug matches self's plug

        Args:
            other (Any):

        Returns:
            bool:
        """
        if isinstance(other, Attr):
            return str(self) == str(other)
        return False

    def __hash__(self):
        """Hash of attribute

        Returns:
            str:
        """
        return hash(str(self))

    # Operator overloads connections and disconnections as well as get item
    def __str__(self):
        """Return self.name

        Returns:
            str:
        """
        return self.name

    def __rshift__(self, other):
        """Tries to connect this attr to the other. connects to locked attributes

        ie. this[attr] >> other[attr]

        Args:
            other ():
        """
        if isinstance(other, Attr):
            self.connect(other)
        else:
            cmds.error("{other} not of type Attr")

    def __lshift__(self, other):
        """Tries to connect the other attr to this attr. connects to locked attributes

        ie. this[attr] << other[attr]

        Args:
            other ():
        """
        if isinstance(other, Attr):
            other.connect(self)
        else:
            cmds.error(f"{other} not of type Attr")

    def __invert__(self):
        """Disconnects anything to this attribute with this attribute
        as the destination

        Returns:
            Attr: returns self
        """
        self.disconnect()
        return self

    def __getitem__(self, attr):
        """Get a child attribute of this attr

        Args:
            attr (str): child attr name

        Returns:
            Attr:
        """
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
        """Gets the new attribute and sets a child attribute"s value to new value

        Args:
            attr (str): child attr name
            new_value (): value to set attr to
        """
        attr = self.__getitem__(attr)
        if isinstance(new_value, Attr):
            new_value = new_value.value
        attr.set(new_value)

    def has_children(self):
        """Returns if attribute has children"""
        return self.plug.isArray or self.plug.isCompound

    def get_all_children_dict(self) -> dict[str, "Attr"]:
        """Gets all children in a dictionary"""
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
        """Get Indicies of attribute. throws TypeError if not an array

        Raises:
            TypeError: no indicies

        Returns:
            list(int): indicies list
        """
        try:
            return list(self.plug.getExistingArrayAttributeIndices())
        except TypeError:
            raise TypeError(f"{self} does not have indicies")

    def remove_index(self, rem_index: int, shift_down: bool = True):
        """remove index and shifts down if applied

        Args:
            index (int):
            shift_down (bool, optional): _description_. Defaults to False
        """

        def __reconnect_attr(src_attr: "Attr", dest_attr: "Attr"):
            """given a src attr and dest attr transfer all connections and data to dest attr

            Args:
                src_attr (Attr):
                dest_attr (Attr):
            """
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
        """gets next index

        Raises:
            TypeError: no indicie

        Returns:
            int:
        """
        if self.__len__() == 0:
            return 0
        return self.get_indicies()[-1] + 1

    def next_index_attr(self):
        """Gets next index as an attribute

        Returns: Attr
        """
        return self.__getitem__(self.next_index())

    def __len__(self):
        """Gets length of child attributes, returns -1 if there are no children

        Returns:
            int:
        """
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
        """Gets the iterator object

        Raises:
            TypeError: if attribute is not a compound or array

        Returns:
            AttrIter:
        """
        if not self.has_children():
            raise TypeError("attribute is not of type compound or array")
        index_list = range(self.__len__())
        if self.plug.isArray:
            index_list = self.get_indicies()
        for index in index_list:
            yield self.__getitem__(index)

    # Math Operator Overloads
    def _base_math_operators(self, x, y, function):
        """Takes 2 inputs, extracts the values and preforms the given
        function on those 2 values

        Args:
            x (Any): value
            y (Any): value
            function (func): function to compute value

        Returns:
            Any:
        """
        if isinstance(x, Attr):
            x = x.value
        if isinstance(y, Attr):
            y = y.value
        return function(x, y)

    def __add__(self, other):
        """Add the value of the object with the object on the right
        side of the operator

        Returns:
            value: calculated value
        """
        return self._base_math_operators(self, other, lambda x, y: x + y)

    def __radd__(self, other):
        """Add the value of the object with the object on the left
        side of the operator

        Returns:
            value: calculated value
        """
        return self._base_math_operators(self, other, lambda x, y: y + x)

    def __sub__(self, other):
        """Subtract the value of the object with the object on the right
        side of the operator

        Returns:
            value: calculated value
        """
        return self._base_math_operators(self, other, lambda x, y: x - y)

    def __rsub__(self, other):
        """Subtract the value of the object with the object on the left
        side of the operator

        Returns:
            value: calculated value
        """
        return self._base_math_operators(self, other, lambda x, y: y - x)

    def __mul__(self, other):
        """Multiply the value of the object with the object on the right
        side of the operator

        Returns:
            value: calculated value
        """
        return self._base_math_operators(self, other, lambda x, y: x * y)

    def __rmul__(self, other):
        """Multiply the value of the object with the object on the left
        side of the operator

        Returns:
            value: calculated value
        """
        return self._base_math_operators(self, other, lambda x, y: y * x)

    def __truediv__(self, other):
        """Divides the value of the object with the object on the left
        side of the operator

        Returns:
            value: calculated value
        """
        return self._base_math_operators(self, other, lambda x, y: x / y)

    def __rtruediv__(self, other):
        """Divides the value of the object with the object on the right
        side of the operator

        Returns:
            value: calculated value
        """
        return self._base_math_operators(self, other, lambda x, y: y / x)
