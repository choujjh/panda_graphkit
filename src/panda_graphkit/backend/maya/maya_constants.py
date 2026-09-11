from ...operations import math as ops_math
from ..base import NodeMap, OperationMap
from ...signatures import math as sig_math

__all__ = [
    "SIN",
    "ACOS",
    "COS",
    "REMAP",
    "DIST",
    "ADD",
    "SUM",
    "SUBTRACT",
    "MULTIPLY",
    "PRODUCT",
    "DIVIDE",
    "POWER",
    "MATRIX",
]

SIN = OperationMap(
    operation=ops_math.SIN,
    node_maps=[
        NodeMap(
            operation_name=ops_math.SIN.name,
            signature=sig_math.N_O_F_SIG,
            mapped_node_type="sin",
            input_attributes=("input",),
            output_attributes=("output",),
        ),
    ],
)

ACOS = OperationMap(
    operation=ops_math.ACOS,
    node_maps=[
        NodeMap(
            operation_name=ops_math.ACOS.name,
            signature=sig_math.N_O_F_SIG,
            mapped_node_type="acos",
            input_attributes=("input",),
            output_attributes=("output",),
        ),
    ],
)

COS = OperationMap(
    operation=ops_math.COS,
    node_maps=[
        NodeMap(
            operation_name=ops_math.COS.name,
            signature=sig_math.N_O_F_SIG,
            mapped_node_type="cos",
            input_attributes=("input",),
            output_attributes=("output",),
        ),
    ],
)
REMAP = OperationMap(
    operation=ops_math.REMAP,
    node_maps=[
        NodeMap(
            operation_name=ops_math.REMAP.name,
            signature=sig_math.N5_O_N_SIG,
            mapped_node_type="remapValue",
            input_attributes=(
                "inputMin",
                "inputMax",
                "outputMin",
                "outputVal",
                "inputValue",
            ),
            output_attributes=("outValue",),
        ),
    ],
)
DIST = OperationMap(
    operation=ops_math.DIST,
    node_maps=[
        NodeMap(
            operation_name=ops_math.DIST.name,
            signature=sig_math.M_M_O_N_SIG,
            mapped_node_type="distanceBetween",
            input_attributes=(
                "inMatrix1",
                "inMatrix2",
            ),
            output_attributes=("distance",),
        ),
        NodeMap(
            operation_name=ops_math.DIST.name,
            signature=sig_math.V_V_O_N_SIG,
            mapped_node_type="distanceBetween",
            input_attributes=(
                "point1",
                "point2",
            ),
            output_attributes=("distance",),
        ),
    ]
)
ADD = OperationMap(
    operation=ops_math.ADD,
    node_maps=[
        NodeMap(
            operation_name=ops_math.ADD.name,
            signature=sig_math.N_N_O_N_SIG,
            mapped_node_type="addDoubleLinear",
            input_attributes=("input1", "input2"),
            output_attributes=("output",),
        ),
        NodeMap(
            operation_name=ops_math.ADD.name,
            signature=sig_math.N_N_O_N_SIG,
            mapped_node_type="plusMinusAverage",
            input_attributes=("input1D[0]", "input1D[1]"),
            output_attributes=("output1D",),
        ),
        NodeMap(
            operation_name=ops_math.ADD.name,
            signature=sig_math.V_V_O_V_SIG,
            mapped_node_type="plusMinusAverage",
            input_attributes=("input3D[0]", "input3D[1]"),
            output_attributes=("output3D",),
        ),
        NodeMap(
            operation_name=ops_math.ADD.name,
            signature=sig_math.N_V_O_V_SIG,
            mapped_node_type="plusMinusAverage",
            input_attributes=("input3D[0]", "input3D[1]"),
            output_attributes=("output3D",),
        ),
        NodeMap(
            operation_name=ops_math.ADD.name,
            signature=sig_math.V_N_O_V_SIG,
            mapped_node_type="plusMinusAverage",
            input_attributes=("input3D[0]", "input3D[1]"),
            output_attributes=("output3D",),
        ),
    ],
)
SUM = OperationMap(
    operation=ops_math.SUM,
    node_maps=[
        NodeMap(
            operation_name=ops_math.SUM.name,
            signature=sig_math.NV_O_N_SIG,
            mapped_node_type="sum",
            input_attributes=("input",),
            output_attributes=("output",),
        ),
        NodeMap(
            operation_name=ops_math.SUM.name,
            signature=sig_math.NV_O_N_SIG,
            mapped_node_type="plusMinusAverage",
            input_attributes=("input1D",),
            output_attributes=("output1D",),
        ),
        NodeMap(
            operation_name=ops_math.SUM.name,
            signature=sig_math.NUVV_O_V_SIG,
            mapped_node_type="plusMinusAverage",
            input_attributes=("input3D",),
            output_attributes=("output3D",),
        ),
        NodeMap(
            operation_name=ops_math.SUM.name,
            signature=sig_math.MV_O_M_SIG,
            mapped_node_type="addMatrix",
            input_attributes=("matrixIn",),
            output_attributes=("matrixSum",),
        ),
    ],
)
SUBTRACT = OperationMap(
    operation=ops_math.SUBTRACT,
    node_maps=[
        NodeMap(
            operation_name=ops_math.SUBTRACT.name,
            signature=sig_math.N_N_O_N_SIG,
            mapped_node_type="subtract",
            input_attributes=("input1", "input2"),
            output_attributes=("output",),
        ),
        NodeMap(
            operation_name=ops_math.SUBTRACT.name,
            signature=sig_math.N_N_O_N_SIG,
            mapped_node_type="plusMinusAverage",
            input_attributes=("input1D[0]", "input1D[1]"),
            output_attributes=("output1D",),
            node_init={"operation": 2},
        ),
        NodeMap(
            operation_name=ops_math.SUBTRACT.name,
            signature=sig_math.V_V_O_V_SIG,
            mapped_node_type="plusMinusAverage",
            input_attributes=("input3D[0]", "input3D[1]"),
            output_attributes=("output3D",),
            node_init={"operation": 2},
        ),
        NodeMap(
            operation_name=ops_math.SUBTRACT.name,
            signature=sig_math.N_V_O_V_SIG,
            mapped_node_type="plusMinusAverage",
            input_attributes=("input3D[0]", "input3D[1]"),
            output_attributes=("output3D",),
            node_init={"operation": 2},
        ),
        NodeMap(
            operation_name=ops_math.SUBTRACT.name,
            signature=sig_math.V_N_O_V_SIG,
            mapped_node_type="plusMinusAverage",
            input_attributes=("input3D[0]", "input3D[1]"),
            output_attributes=("output3D",),
            node_init={"operation": 2},
        ),
    ],
)
MULTIPLY = OperationMap(
    operation=ops_math.MULTIPLY,
    node_maps=[
        NodeMap(
            operation_name=ops_math.MULTIPLY.name,
            signature=sig_math.N_N_O_N_SIG,
            mapped_node_type="multDoubleLinear",
            input_attributes=("input1", "input2"),
            output_attributes=("output",),
        ),
        NodeMap(
            operation_name=ops_math.MULTIPLY.name,
            signature=sig_math.N_N_O_N_SIG,
            mapped_node_type="multiply",
            input_attributes=("input[0]", "input[1]"),
            output_attributes=("output",),
        ),
        NodeMap(
            operation_name=ops_math.MULTIPLY.name,
            signature=sig_math.N_N_O_N_SIG,
            mapped_node_type="multiplyDivide",
            input_attributes=("input1X", "input2X"),
            output_attributes=("outputX",),
        ),
        NodeMap(
            operation_name=ops_math.MULTIPLY.name,
            signature=sig_math.N_V_O_V_SIG,
            mapped_node_type="multiplyDivide",
            input_attributes=("input1", "input2"),
            output_attributes=("output",),
        ),
        NodeMap(
            operation_name=ops_math.MULTIPLY.name,
            signature=sig_math.V_N_O_V_SIG,
            mapped_node_type="multiplyDivide",
            input_attributes=("input1", "input2"),
            output_attributes=("output",),
        ),
        NodeMap(
            operation_name=ops_math.MULTIPLY.name,
            signature=sig_math.V_V_O_V_SIG,
            mapped_node_type="multiplyDivide",
            input_attributes=("input1", "input2"),
            output_attributes=("output",),
        ),
        NodeMap(
            operation_name=ops_math.MULTIPLY.name,
            signature=sig_math.M_M_O_M_SIG,
            mapped_node_type="multMatrix",
            input_attributes=("matrixIn[0]", "matrixIn[1]"),
            output_attributes=("matrixSum",),
            invert_input_indicies=True,
        ),
        NodeMap(
            operation_name=ops_math.MULTIPLY.name,
            signature=sig_math.M_V_O_V_SIG,
            mapped_node_type="pointMatrixMult",
            input_attributes=("inMatrix", "inPoint"),
            output_attributes=("output",),
        ),
    ],
)
PRODUCT = OperationMap(
    operation=ops_math.PRODUCT,
    node_maps=[
        NodeMap(
            operation_name=ops_math.PRODUCT.name,
            signature=sig_math.NV_O_N_SIG,
            mapped_node_type="multiply",
            input_attributes=("input",),
            output_attributes=("output",),
        ),
        NodeMap(
            operation_name=ops_math.PRODUCT.name,
            signature=sig_math.MV_O_M_SIG,
            mapped_node_type="multMatrix",
            input_attributes=("matrixIn",),
            output_attributes=("matrixSum",),
            invert_input_indicies=True,
        ),
    ],
)
DIVIDE = OperationMap(
    operation=ops_math.DIVIDE,
    node_maps=[
        NodeMap(
            operation_name=ops_math.DIVIDE.name,
            signature=sig_math.N_N_O_N_SIG,
            mapped_node_type="divide",
            input_attributes=("input1", "input2"),
            output_attributes=("output",),
        ),
        NodeMap(
            operation_name=ops_math.DIVIDE.name,
            signature=sig_math.N_N_O_N_SIG,
            mapped_node_type="multiplyDivide",
            input_attributes=("input1X", "input2X"),
            output_attributes=("outputX",),
            node_init={"operation": 2},
        ),
        NodeMap(
            operation_name=ops_math.DIVIDE.name,
            signature=sig_math.V_V_O_V_SIG,
            mapped_node_type="multiplyDivide",
            input_attributes=("input1", "input2"),
            output_attributes=("output",),
            node_init={"operation": 2},
        ),
    ],
)
POWER = OperationMap(
    operation=ops_math.POWER,
    node_maps=[
        NodeMap(
            operation_name=ops_math.POWER.name,
            signature=sig_math.N_N_O_N_SIG,
            mapped_node_type="power",
            input_attributes=("input", "exponent"),
            output_attributes=("output",),
        ),
        NodeMap(
            operation_name=ops_math.POWER.name,
            signature=sig_math.N_N_O_N_SIG,
            mapped_node_type="multiplyDivide",
            input_attributes=("input1X", "input2X"),
            output_attributes=("outputX",),
            node_init={"operation": 3},
        ),
        NodeMap(
            operation_name=ops_math.POWER.name,
            signature=sig_math.V_V_O_V_SIG,
            mapped_node_type="multiplyDivide",
            input_attributes=("input1", "input2"),
            output_attributes=("output",),
            node_init={"operation": 3},
        ),
    ],
)
MATRIX = OperationMap(
    operation=ops_math.MATRIX,
    node_maps=[
        NodeMap(
            operation_name=ops_math.MATRIX.name,
            signature=sig_math.N16_O_M_SIG,
            mapped_node_type="fourByFourMatrix",
            input_attributes=tuple(f"in{index // 4}{index % 4}" for index in range(16)),
            output_attributes=("output",),
        ),
    ],
)
