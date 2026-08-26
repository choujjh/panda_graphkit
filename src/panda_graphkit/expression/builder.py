"""Build typed GraphKit graphs from expression source text."""

from . import tokenizer
from . import analyzer
from ..core import Graph
from ..backend import base

from . import compiler
from . import parser


def build_expression(
    expression: str, prefix: str, name: str, backend: base.Backend, **vars
) -> Graph:
    """Parse, analyze, compile, and materialize an expression graph.

    Args:
        expression: Expression-language source text to compile.
        prefix: Prefix used when naming generated graph nodes.
        name: Name used for the generated expression network.
        backend: Backend used for type resolution and graph construction.
        **vars: Optional variables supplied by the caller.

    Returns:
        The compiled and backend-built Graph.
    """
    tokens = tokenizer.Tokenizer(expression).tokenize()
    program = parser.Parser(tokens).parse()
    analyzer_ = analyzer.Analyzer(backend=backend)
    analyzer_.analyze(program)
    compiler_ = compiler.Compiler(backend)
    compiler_.compile(program, prefix, name)

    backend.build_graph(compiler_.graph_)

    return compiler_.graph_
