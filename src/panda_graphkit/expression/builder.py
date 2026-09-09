"""Build typed GraphKit graphs from expression source text."""

from dataclasses import dataclass, field
from collections.abc import Mapping
from typing import Any
from . import tokenizer
from . import analyzer
from ..core import Graph
from ..backend import base

from . import compiler
from . import parser


@dataclass
class ExpressionResult:
    graph: Graph
    nodes: list = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)


def build_expression(
    expression: str,
    prefix: str,
    name: str,
    backend: base.Backend,
    inputs: Mapping[str, Any] | None = None,
) -> ExpressionResult:
    """Parse, analyze, compile, and materialize an expression graph.

    Args:
        expression: Expression-language source text to compile.
        prefix: Prefix used when naming generated graph nodes.
        name: Name used for the generated expression network.
        backend: Backend used for type resolution and graph construction.
        inputs: Named constants or live backend attributes. Binding conversion
            is not implemented yet; nonempty inputs raise NotImplementedError.

    Returns:
        An ExpressionResult containing the built graph, graph nodes, and variable ports.
    """
    tokens = tokenizer.Tokenizer(expression).tokenize()
    program = parser.Parser(tokens).parse()

    analyzer_ = analyzer.Analyzer(backend=backend, backend_variables=inputs)
    analyzer_.analyze(program)

    compiler_ = compiler.Compiler(backend)
    compiler_.bind_inputs(analyzer_.variables, prefix)
    compiler_.compile(program, prefix, name)
    nodes, variables = backend.build_graph(compiler_.graph, compiler_.variables)

    return ExpressionResult(
        graph=compiler_.graph,
        nodes=nodes,
        variables=variables,
    )
