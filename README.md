# Panda GraphKit

Panda GraphKit is a Python library for building dependency graphs for 
procedural animation.

The goal is to provide a DCC-independent graph and expression system
that can be used to construct animation logic and then translate that
logic into different host applications such as Maya, Blender, Houdini,
and Unreal.

## Status

🚧 **Early development**

The API is currently experimental and subject to change.

## Goals

Panda GraphKit is intended to provide:

- A DCC-independent dependency graph
- A typed node and port system
- An expression language for constructing graphs
- Expression parsing and semantic analysis
- Type inference and backend-assisted type resolution
- Backend implementations for different DCCs
- A common interface for Maya, Blender, Houdini, Unreal, and others
- The ability to use the graph system independently of the expression language

## Architecture

The project is divided into several layers:

```text
Expression Language
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
     Compiler
        │
        ▼
   GraphKit Graph
        │
   ┌────┼────┬──────┐
   ▼    ▼    ▼      ▼
 Maya Blender Houdini Unreal
```
## Instalation
Panda GraphKit is currently under development and is intended to be installed 
directly from the source repository.

### Maya

Panda GraphKit can be installed into Maya's Python environment using pip.

First, clone the repository:

git clone https://github.com/choujjh/panda-graphkit.git
cd panda-graphkit

Then open Maya and use Maya's Python interpreter to install the package.

From Maya's Python console:
```python
import subprocess
import sys

subprocess.check_call([
    sys.executable,
    "-m",
    "pip",
    "install",
    "-e",
    "/path/to/panda-graphkit",
])
```

Replace /path/to/panda-graphkit with the location where you cloned the repository.

After installation, GraphKit can be imported from Maya:

```python
import panda_graphkit

For example:

from panda_graphkit import Graph

graph = Graph()
```