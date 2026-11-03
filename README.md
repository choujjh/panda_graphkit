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

## Color palette widget

`PaletteWidget` is a single-selection color grid with six columns by
default. Its default 32 colors are queried from a temporary Maya `palettePort`.
Pass `columns=8` for eight columns, or `colors=["#ff0000", "#00ff00"]` for
custom swatches. RGB tuples with components from 0 to 1 are also accepted.

```python
from panda_graphkit.maya import PaletteWidget

# In your UI's create_widget / create_layout / create_connections methods:
self.palette = PaletteWidget(parent=self)
self.layout().addWidget(self.palette)
self.palette.selection_changed.connect(lambda index: print("Selected:", index))

self.palette.set_selection(6)
index = self.palette.get_selection()  # Zero-based index; -1 when cleared.
color = self.palette.selected_color()  # QColor, or None when cleared.
self.palette.set_selection(-1)  # Clear selection.

# Keep a reference to a reusable popup, e.g. on your UI instance:
self.palette_popup = PaletteWidget(parent=self, popup=True)
self.palette_popup.selection_changed.connect(lambda index: print(index))
self.palette_popup.show_popup()  # At cursor, or pass a global QPoint.
```

The signal fires for both user and programmatic selection changes, but not
when the same cell is selected again. Popups retain selection when hidden;
choosing a cell, pressing Escape, or clicking outside dismisses them.

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
