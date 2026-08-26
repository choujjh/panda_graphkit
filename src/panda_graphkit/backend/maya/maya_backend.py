"""Maya backend for materializing GraphKit operations and connections."""

from ...core import (
    FLOAT,
    MATRIX4,
    VECTOR2,
    VECTOR3,
    INT,
    Port,
    ConstNode,
    BackendNode,
)
from ..base import Backend, OperationMap, NodeMap
from ...maya import (
    create_node,
    wrap_node,
    exists,
    delete_node,
    Node as MNode,
    Attr as MAttr,
)
from . import maya_constants


class MayaBackend(Backend):
    """Build GraphKit graphs as nodes and attribute connections in Maya."""

    _type_mapping = {
        "matrix": MATRIX4,
        "double3": VECTOR3,
        "double2": VECTOR2,
        "double": FLOAT,
        "doubleLinear": FLOAT,
        "doubleAngle": FLOAT,
        "long": INT,
    }
    _node_mapping = {
        getattr(maya_constants, x).operation: getattr(maya_constants, x)
        for x in maya_constants.__all__
        if isinstance(getattr(maya_constants, x), OperationMap)
    }

    def resolve_attribute_type(self, node, attributes):
        node = node.name
        attributes = [attr.name for attr in attributes]
        if not exists(node):
            raise RuntimeError(f"Node {node} does not exist")
        attr = wrap_node(node)
        try:
            for attribute in attributes:
                attr = attr[attribute]
        except KeyError as e:
            raise RuntimeError(f"attribte {node}.{'.'.join(attributes)} not found")
        attr_type = attr.type_
        if attr_type not in self._type_mapping:
            raise TypeError(f"Unsupported type {attr_type} for expression")
        return self._type_mapping[attr_type]

    def _create_nodes(self, graph):
        node_dict = {}
        for node in graph.get_nodes():
            if isinstance(node, ConstNode):
                continue
            if isinstance(node, BackendNode):
                node_dict[node.name] = {"node": wrap_node(node.name), "map": None}
            if node.operation in self._node_mapping:
                maya_sig_map = self._node_mapping[node.operation].sig_map()
                node_sig = node.get_operation_compatable_signature()
                if node_sig not in maya_sig_map:
                    raise RuntimeError(
                        f"node signature not found for {node_sig} for operation {node.operation.name}"
                    )
                maya_ops = maya_sig_map[node_sig]
                for node_map in maya_ops:
                    maya_node = create_node(
                        node_map.mapped_node_type, node.name, **node_map.node_init
                    )
                    if maya_node.type_ == "unknown":
                        delete_node(maya_node)
                        continue
                    node_dict[node.name] = {"node": maya_node, "map": node_map}
                    break
        return node_dict

    def _create_connections(self, graph, node_dict):
        for connection in graph.connections.values():
            attr_list = []
            for port in [connection.source, connection.destination]:
                port_map = maya_node = node_map = None
                if port.node.name in node_dict:
                    port_map = node_dict[port.node.name]
                    maya_node = port_map["node"]
                    node_map = port_map["map"]
                attr_list.append(self._get_attr(port, maya_node, node_map))

            if not isinstance(attr_list[0], MAttr):
                attr_list[1].set(attr_list[0])
            else:
                attr_list[0].connect(attr_list[1])

    def _get_attr(self, port: Port, maya_node: MNode, node_map: NodeMap) -> MAttr:
        node = port.node

        if isinstance(node, ConstNode):
            return node.value
        if isinstance(node, BackendNode):
            attrs = port.attribute_list
        else:
            attrs = node_map.get_backend_attr_name(port)
        curr_attr = maya_node
        for attr in attrs:
            curr_attr = curr_attr[attr]
        return curr_attr
