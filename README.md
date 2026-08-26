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
  Lexer
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

### Option 1: PYTHONPATH

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