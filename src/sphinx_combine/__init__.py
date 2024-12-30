"""
Sphinx extension to combine multiple nested code-blocks into a single one.
"""

from typing import ClassVar

from docutils import nodes
from docutils.nodes import Node
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective
from sphinx.util.typing import ExtensionMetadata


class CombinedCodeBlock(SphinxDirective):
    """
    A Sphinx directive that merges multiple nested code blocks into a single
    literal block.
    """

    has_content: ClassVar[bool] = True

    # The language is an optional argument for the directive.
    required_arguments: ClassVar[int] = 0
    optional_arguments: ClassVar[int] = 1

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

        try:
            language = self.arguments[0]
        except IndexError:
            language = "none"

        combined_node = nodes.literal_block(
            rawsource=combined_text,
            text=combined_text,
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
