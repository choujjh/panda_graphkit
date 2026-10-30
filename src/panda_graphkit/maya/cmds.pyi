# Reuse Maya's command declarations for editor completion.
# Override selected commands to describe converted Node results.
from maya.cmds import *
from typing import Any

from .node_wrapper import Node

def listRelatives(*args: Any, **kwargs: Any) -> list[Node] | None: ...
def spaceLocator(*args: Any, **kwargs: Any) -> list[Node]: ...
def circle(*args: Any, **kwargs: Any) -> list[Node]: ...
