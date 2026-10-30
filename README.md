# Panda GraphKit

Build typed dependency graphs for procedural animation using Python or
expressions. Includes type inference, a Maya backend, an extensible backend
interface, and Maya node/attribute wrappers.

> **Early development:** the API is experimental and subject to change.

## Maya installation

Add the package's `src` directory to `Maya.env`, then restart Maya:

```text
PYTHONPATH=C:/path/to/panda_graphkit/src
```

On Windows, separate multiple paths with `;`. Run these examples inside Maya.

## Nodes and attributes

```python
from panda_graphkit.maya import create_node, wrap_node

source = create_node("transform", t=[0, 10, 0])
target = create_node("transform")
node = wrap_node(str(source))  # None if the node does not exist.

source.translate = [1, 2, 3]       # Same as source["translate"] = [1, 2, 3].
position = source.translate.value  # Same as source["translate"].value.
source.tx >> target.tx            # Connect.
~target.tx                        # Disconnect incoming connections.
target.tx.set(5)

matrix = source.worldMatrix[0]
plug = matrix.plug                # Underlying OpenMaya MPlug.
```

Both `node.attr` and `node["attr"]` return attribute wrappers. Use brackets
for names that conflict with Python members (such as `name`), names starting
with `_`, or paths such as `node["worldMatrix[0]"]`.

Creation keywords set values or connect supplied `Attr` objects. Arrays
support logical indices, iteration over existing elements, and `next_index()`.
Use `node.exists` to check validity; accessing a deleted node's plug raises
`ReferenceError`. `attr.plug` replaces `attr.get_plug()`.

## Maya commands

```python
from panda_graphkit.maya import cmds

cube, history = cmds.polyCube(name="exampleCube")
cmds.setAttr(cube.tx, 3)
cmds.select(cube)
selected = cmds.ls(selection=True)
```

Commands accept wrappers and convert returned scene node/attribute names into
wrappers, including within containers. Ordinary text matching a scene name is
also converted; use `maya.cmds` for unchanged return values.

## Expressions

```python
from panda_graphkit import build_expression
from panda_graphkit.integrations.maya import MayaBackend

result = build_expression(
    "result = speed * scale",
    "example",
    "network",
    backend=MayaBackend(),
    inputs={"speed": source.tx, "scale": 2, "result": target.ty},
)
```

Attribute inputs read scene values; assigning to one connects the result to
that attribute. Constants and unbound names act as local variables. Node
inputs support paths such as `target.ty`. Repeated assignments to a scene
attribute keep the last connection.

Expressions support arithmetic and vector operations:

| Operation | Result |
| --- | --- |
| `dot(a, b)` | Scalar dot product |
| `cross(a, b)` | Right-handed vector cross product |
| `point_mult(matrix, point)` | Position transformed with translation |
| `vector_mult(matrix, vector)` | Direction transformed without translation |
| `normalize(vector)` | Unit direction; zero-length behavior depends on the backend |

`matrix * vector` also transforms a point. Dot and cross products do not
normalize their inputs.
