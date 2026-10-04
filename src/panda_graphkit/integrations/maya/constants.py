from ...graph import NodeMap, OperationMap
from ...graph import operations as ops_math
from ...graph import signatures as sig_math

__all__ = [
    "SIN",
    "ACOS",
    "COS",
    "REMAP",
    "DIST",
    "DOT",
    "CROSS",
    "POINT_MULTIPLY",
    "VECTOR_MULTIPLY",
    "NORMALIZE",
    "LENGTH",
    "CLAMP",
    "TRANSLATE_MATRIX",
    "MATRIX_TO_TRANSLATE",
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
DOT = OperationMap(
    operation=ops_math.DOT,
    node_maps=[
        NodeMap(
            operation_name=ops_math.DOT.name,
            signature=sig_math.V_V_O_N_SIG,
            mapped_node_type="dotProduct",
            input_attributes=("input1", "input2"),
            output_attributes=("output",),
        ),
        NodeMap(
            operation_name=ops_math.DOT.name,
            signature=sig_math.V_V_O_N_SIG,
            mapped_node_type="vectorProduct",
            input_attributes=("input1", "input2"),
            output_attributes=("outputX",),
            node_init={"operation": 1, "normalizeOutput": False},
        ),
    ],
)
CROSS = OperationMap(
    operation=ops_math.CROSS,
    node_maps=[
        NodeMap(
            operation_name=ops_math.CROSS.name,
            signature=sig_math.V_V_O_V_SIG,
            mapped_node_type="crossProduct",
            input_attributes=("input1", "input2"),
            output_attributes=("output",),
        ),
        NodeMap(
            operation_name=ops_math.CROSS.name,
            signature=sig_math.V_V_O_V_SIG,
            mapped_node_type="vectorProduct",
            input_attributes=("input1", "input2"),
            output_attributes=("output",),
            node_init={"operation": 2, "normalizeOutput": False},
        ),
    ],
)
POINT_MULTIPLY = OperationMap(
    operation=ops_math.POINT_MULTIPLY,
    node_maps=[
        NodeMap(
            operation_name=ops_math.POINT_MULTIPLY.name,
            signature=sig_math.M_V_O_V_SIG,
            mapped_node_type="pointMatrixMult",
            input_attributes=("inMatrix", "inPoint"),
            output_attributes=("output",),
            node_init={"vectorMultiply": False},
        ),
    ],
)
VECTOR_MULTIPLY = OperationMap(
    operation=ops_math.VECTOR_MULTIPLY,
    node_maps=[
        NodeMap(
            operation_name=ops_math.VECTOR_MULTIPLY.name,
            signature=sig_math.M_V_O_V_SIG,
            mapped_node_type="pointMatrixMult",
            input_attributes=("inMatrix", "inPoint"),
            output_attributes=("output",),
            node_init={"vectorMultiply": True},
        ),
    ],
)
NORMALIZE = OperationMap(
    operation=ops_math.NORMALIZE,
    node_maps=[
        NodeMap(
            operation_name=ops_math.NORMALIZE.name,
            signature=sig_math.V_O_V_SIG,
            mapped_node_type="normalize",
            input_attributes=("input",),
            output_attributes=("output",),
        ),
        NodeMap(
            operation_name=ops_math.NORMALIZE.name,
            signature=sig_math.V_O_V_SIG,
            mapped_node_type="vectorProduct",
            input_attributes=("input1",),
            output_attributes=("output",),
            node_init={"operation": 0, "normalizeOutput": True},
        ),
    ],
)
LENGTH = OperationMap(
    operation=ops_math.LENGTH,
    node_maps=[
        NodeMap(
            operation_name=ops_math.LENGTH.name,
            signature=sig_math.V_O_N_SIG,
            mapped_node_type="length",
            input_attributes=("input",),
            output_attributes=("output",),
        ),
    ],
)
CLAMP = OperationMap(
    operation=ops_math.CLAMP,
    node_maps=[
        NodeMap(
            operation_name=ops_math.CLAMP.name,
            signature=sig_math.N_N_N_O_N_SIG,
            mapped_node_type="clampRange",
            input_attributes=("input", "minimum", "maximum"),
            output_attributes=("output",),
        ),
    ],
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
            node_init={"vectorMultiply": True},
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


TRANSLATE_MATRIX = OperationMap(
    operation=ops_math.TRANSLATE_MATRIX,
    node_maps=[
        NodeMap(
            operation_name=ops_math.TRANSLATE_MATRIX.name,
            signature=sig_math.V_O_M_SIG,
            mapped_node_type="fourByFourMatrix",
            input_attributes=(("in30", "in31", "in32"),),
            output_attributes=("output",),
        ),
    ],
)


MATRIX_TO_TRANSLATE = OperationMap(
    operation=ops_math.MATRIX_TO_TRANSLATE,
    node_maps=[
        NodeMap(
            operation_name=ops_math.MATRIX_TO_TRANSLATE.name,
            signature=sig_math.M_O_V_SIG,
            mapped_node_type="rowFromMatrix",
            input_attributes=("matrix",),
            output_attributes=(("outputX", "outputY", "outputZ"),),
            node_init={"input": 3},
        ),
        NodeMap(
            operation_name=ops_math.MATRIX_TO_TRANSLATE.name,
            signature=sig_math.M_O_V_SIG,
            mapped_node_type="pointMatrixMult",
            input_attributes=("inMatrix",),
            output_attributes=("output",),
            node_init={"inPoint": (0, 0, 0), "vectorMultiply": False},
        ),
    ],
)
