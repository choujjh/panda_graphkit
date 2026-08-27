# Panda GraphKit

Panda GraphKit is a Python library for building typed dependency graphs for
procedural animation.

The goal is to provide a DCC-independent graph and expression system that can
be translated into different applications such as Maya, Blender, Houdini,
and Unreal.

> 🚧 **Early development**
>
> The API is experimental and subject to change.

## Features

- DCC-independent dependency graph
- Typed nodes and ports
- Expression language
- Expression parsing and semantic analysis
- Type inference
- Backend support for different DCCs
- Graph generation independent of the expression language

## Architecture

```text
Expression
    │
    ▼
  Tokenizer
    │
    ▼
  Parser
    │
    ▼
   AST
    │
    ▼
 Analyzer
    │
    ▼
  Graph
    │
    ├── Maya
    ├── Bifrost
    ├── Blender
    ├── Houdini
    └── Unreal
```

## Known Issues

Panda GraphKit is currently under active development. The following are known
limitations and areas that are still being worked on.

- The API is experimental and may change.
- The analyzer and type system are still under development.
- Number to Vector conversion signatures currently don't work ie 4 * Vector(x, y, z)

## Maya Installation

Panda GraphKit is a standard Python package. Maya does not require a separate
package format.

There are two ways to make Panda GraphKit available in Maya.

### PYTHONPATH

For development, using `PYTHONPATH` is recommended.

Panda GraphKit uses a `src` layout:

```text
panda_graphkit/
├── pyproject.toml
└── src/
    └── panda_graphkit/
        ├── __init__.py
        ├── backend/
        ├── core/
        ├── expression/
        ├── maya/
        └── operations/
```

add `PYTHONPATH=C:/path/to/panda_graphkit/src` to maya.env file. if `PYTHONPATH`
is already in use, add `;` inbetween each path

### Usage
node creation and connection
```
from panda_graphkit.maya import create_node

t1 = create_node("transform", t=[0, 10, 0])
t2 = create_node("transform", t=[3, 5, 0])
t3 = create_node("transform", )
t4 = create_node("transform", )
len1 = create_node("distanceBetween", inMatrix1=t1["worldMatrix"][0], inMatrix2=t2["worldMatrix"][0])
len2 = create_node("distanceBetween", inMatrix1=t2["worldMatrix"][0], inMatrix2=t3["worldMatrix"][0])
len3 = create_node("distanceBetween", inMatrix1=t3["worldMatrix"][0], inMatrix2=t1["worldMatrix"][0])
```

expression
```
from panda_graphkit.expression import build_expression
from panda_graphkit.backend.maya import maya_backend

exp_str = f"""
  c_squared = {len1["distance"]} ** 2
  a_squared = {len2["distance"]} ** 2
  b_squared = {len3["distance"]} ** 2
  numer = c_squared - (a_squared + b_squared)
  denom = 2 * {len2["distance"]} * {len3["distance"]}
  {t4["rx"]} = numer / denom
"""

maya_backend_ = maya_backend.MayaBackend()
graph = build_expression(exp_str, "loc", "network", backend=maya_backend_)
```
