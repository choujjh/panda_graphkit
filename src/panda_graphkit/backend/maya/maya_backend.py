"""Maya backend for materializing GraphKit operations and connections."""

from collections.abc import Iterable
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
from ...operations import math as ops_math
from ...signatures import math as sig_math
from ..base import Backend, NodeMap, OperationMap, BackendNodeOptimization

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
    optimize_operations = [
        BackendNodeOptimization(
            checked_ops=[ops_math.ADD, ops_math.SUM],
            operand=ops_math.SUM,
            identity_value=0,
        ),
        BackendNodeOptimization(
            checked_ops=[ops_math.MULTIPLY, ops_math.PRODUCT],
            operand=ops_math.PRODUCT.without_signatures(sig_math.NUVV_O_V_SIG),
            identity_value=1,
        ),
    ]
    def __init__(self):
        super().__init__()
        self.supported_operations_map[ops_math.PRODUCT.name] = ops_math.PRODUCT.without_signatures(sig_math.NUVV_O_V_SIG)

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
            raise RuntimeError(
                f"attribte {node}.{'.'.join(filtered_attributes)} not found"
            )
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
            # Getting source and attribute
            attr_list = []
            skip_connection = False
            for port_index, port in enumerate(
                [connection.source, connection.destination]
            ):
                port_map = maya_node = node_map = None
                # If node mapping does exist
                if port.node.name in node_dict:
                    port_map = node_dict[port.node.name]
                    maya_node = port_map["node"]
                    node_map = port_map["map"]
                # If no node mapping exists
                elif not isinstance(port.node, (BackendNode, ConstNode)):
                    if port_index == 1:
                        skip_connection = True
                        continue
                    else:
                        source_attr_list = []
                        for src_port in graph.input_src_ports(port.node):
                            if src_port.node.name in node_dict:
                                port_map = node_dict[src_port.node.name]
                                maya_node = port_map["node"]
                                node_map = port_map["map"]
                            source_attr_list.append(
                                self._get_attr(src_port, maya_node, node_map)
                            )
                        attr_list.append(source_attr_list)
                        continue
                attr_list.append(self._get_attr(port, maya_node, node_map))

            if skip_connection:
                continue
            source_attr = attr_list[0]
            dest_attr = attr_list[1]

            # Connectin source and attribute
            # if source_attr returns a list
            if not isinstance(source_attr, MAttr) and isinstance(source_attr, list):
                src_dict = nested_to_dict(source_attr)
                for key, value in src_dict.items():
                    dest_chld_attr = dest_attr
                    for index in key:
                        dest_chld_attr = dest_chld_attr[index]

                    dest_chld_attr.set_connect(value)

            # if dest has children and source attr does not
            elif dest_attr.has_children() and (
                not isinstance(source_attr, Iterable)
                or (isinstance(source_attr, MAttr) and not source_attr.has_children())
            ):
                for dest_chld_attr in dest_attr:
                    dest_chld_attr.set_connect(source_attr)

            # if both have children
            elif (isinstance(source_attr, MAttr) and source_attr.has_children()) and (dest_attr.has_children()):
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

            else:
                dest_attr.set_connect(source_attr)

    def _get_attr(self, port: Port, maya_node: MNode, node_map: NodeMap) -> MAttr:
        """Gets attribute from mapped maya node

        Args:
            port (Port):
            maya_node (MNode):
            node_map (NodeMap):

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


def nested_to_dict(data, indexes=(), depth=0, max_depth=300):
    result = {}
    if depth >= max_depth:
        return {}
    for i, value in enumerate(data):
        current_index = indexes + (i,)

        if isinstance(value, list):
            result.update(nested_to_dict(value, current_index, depth + 1))
        else:
            result[current_index] = value

    return result
