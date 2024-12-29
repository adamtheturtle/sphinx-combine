"""
Sphinx extension to combine multiple nested code-blocks into a single one.
"""

from collections.abc import Callable
from typing import Any, ClassVar

from docutils import nodes
from docutils.nodes import Node
from docutils.parsers.rst import directives
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective
from sphinx.util.typing import ExtensionMetadata


class CombinedCodeBlock(SphinxDirective):
    """
    A Sphinx directive that merges multiple nested code blocks into a single
    literal block.
    """

    has_content: ClassVar[bool] = True
    required_arguments: ClassVar[int] = 0
    optional_arguments: ClassVar[int] = 1
    final_argument_whitespace: ClassVar[bool] = True

    option_spec: ClassVar[dict[str, Callable[[str], Any]] | None] = {
        "language": directives.unchanged_required,
    }

    def run(self) -> list[Node]:
        """
        Parse the directive content (which may contain multiple code-blocks)
        and return a single merged code-block node.
        """
        container = nodes.container()
        self.state.nested_parse(  # pyright: ignore[reportUnknownMemberType]
            block=self.content,
            input_offset=self.content_offset,
            node=container,
        )

        traversed_nodes = container.findall(condition=nodes.literal_block)
        code_snippets = [literal.astext() for literal in traversed_nodes]

        combined_text = "\n".join(code_snippets)
        language = self.options.get("language", "none")

        combined_node = nodes.literal_block(
            combined_text,
            combined_text,
            language=language,
        )
        return [combined_node]


def setup(app: Sphinx) -> ExtensionMetadata:
    """
    Register the 'combined-code-block' directive with Sphinx.
    """
    app.add_directive(name="combined-code-block", cls=CombinedCodeBlock)
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
