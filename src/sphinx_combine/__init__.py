from collections.abc import Callable

from docutils import nodes
from docutils.nodes import Node
from docutils.parsers.rst import Directive, directives
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective


class CombinedCodeBlock(SphinxDirective):
    """A Sphinx directive that merges multiple nested code blocks into a single
    literal block.

    This works across all builders (HTML, PDF, etc.).
    """

    has_content: bool = True
    required_arguments: int = 0
    optional_arguments: int = 1
    final_argument_whitespace: bool = True

    #: Maps directive option names to callables that parse their values.
    #: For example, ':language: python'.
    option_spec: dict[str, Callable[[str], str]] = {
        "language": directives.unchanged_required,
    }

    def run(self) -> list[Node]:
        """
        Parse the directive content (which may contain multiple code-blocks)
        and return a single merged code-block node.
        """
        container = nodes.container()
        self.state.nested_parse(self.content, self.content_offset, container)

        code_snippets: list[str] = []
        for literal in container.traverse(nodes.literal_block):
            code_snippets.append(literal.astext())

        combined_text: str = "\n".join(code_snippets)
        language: str = self.options.get("language", "none")

        combined_node: Node = nodes.literal_block(
            combined_text,
            combined_text,
            language=language,
        )
        return [combined_node]


def setup(app: Sphinx) -> dict[str, bool | str]:
    """Register the 'combined-code-block' directive with Sphinx.

    :param app: The Sphinx application object.
    :return: Metadata for Sphinx indicating this extension’s version and
        parallel read/write status.
    """
    app.add_directive("combined-code-block", CombinedCodeBlock)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
