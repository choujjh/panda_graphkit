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
from ...expression.ast import Identifier, Literal
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
        """Resolve the attribute type for a Maya node attribute chain.

        Args:
            node: Node object whose attribute is being inspected.
            attributes: Sequence of attribute identifiers along the access path.

        Returns:
            The matching `AttributeType` for the final attribute.
        """
        node = node.name
        filtered_attributes = []

        for attribute in attributes:
            if hasattr(attribute, "name"):
                filtered_attributes.append(attribute.name)
            if hasattr(attribute, "value"):
                filtered_attributes.append(attribute.value)

        if not exists(node):
            raise RuntimeError(f"Node {node} does not exist")
        attr = wrap_node(node)
        try:
            for attribute in filtered_attributes:
                attr = attr[attribute]
        except KeyError as e:
            raise RuntimeError(f"attribte {node}.{'.'.join(filtered_attributes)} not found")
        attr_type = attr.type_
        if attr_type not in self._type_mapping:
            raise TypeError(f"Unsupported type {attr_type} for expression")
        return self._type_mapping[attr_type]

    def _create_nodes(self, graph):
        """Create Maya nodes for each backend-capable graph node.

        Args:
            graph: Graph to materialize into Maya dependencies.

        Returns:
            Mapping of node names to the created Maya node and its node map.
        """
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
        """Connect the generated Maya nodes according to the graph topology."""
        for connection in graph.connections.values():
            attr_list = []
            for port in [connection.source, connection.destination]:
                port_map = maya_node = node_map = None
                if port.node.name in node_dict:
                    port_map = node_dict[port.node.name]
                    maya_node = port_map["node"]
                    node_map = port_map["map"]
                attr_list.append(self._get_attr(port, maya_node, node_map))
            source_attr = attr_list[0]
            dest_attr = attr_list[1]

            if (
                not isinstance(source_attr, MAttr)
                or source_attr.type_ == dest_attr.type_
            ):
                dest_attr.set_connect(source_attr)

            elif source_attr.has_children() and dest_attr.has_children():
                source_len = len(source_attr)
                dest_len = len(dest_attr)
                if source_len == dest_len:
                    dest_attr.set_connect(source_attr)
                else:
                    min_len = min(source_len, dest_len)
                    source_list = [x for x in source_attr][:min_len]
                    dest_list = [x for x in dest_attr][:min_len]

                    for source_chld_attr, dest_chld_attr in zip(source_list, dest_list):
                        dest_chld_attr.set_connect(source_chld_attr)

            elif dest_attr.has_children() and not source_attr.has_children():
                for dest_chld_attr in dest_attr:
                    dest_chld_attr.set_connect(source_attr)

    def _get_attr(self, port: Port, maya_node: MNode, node_map: NodeMap) -> MAttr:
        """Gets attribute from mapped maya node

        Args:
            port (Port): _description_
            maya_node (MNode): _description_
            node_map (NodeMap): _description_

        Returns:
            MAttr:
        """
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
