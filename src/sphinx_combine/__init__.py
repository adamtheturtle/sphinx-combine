"""
Sphinx extension to combine multiple nested code-blocks into a single
one.
"""

from importlib.metadata import version

from docutils import nodes
from docutils.nodes import Element, Node
from docutils.statemachine import StringList
from sphinx.application import Sphinx
from sphinx.directives.code import CodeBlock
from sphinx.util.typing import ExtensionMetadata


def _literal_blocks_from(*, node: Element) -> list[nodes.literal_block]:
    """
    Return literal_block nodes to merge from a top-level nested-parse
    child.

    Caption wrappers are ``container`` nodes with ``literal_block=True``
    that contain a caption plus the real ``literal_block``. Only the
    inner literal content should be merged.
    """
    if isinstance(node, nodes.literal_block):
        return [node]
    if isinstance(node, nodes.container) and node.get(key="literal_block"):
        return list(node.findall(condition=nodes.literal_block))
    return []


def _is_blank_separator(*, node: Node) -> bool:
    """
    Return whether ``node`` is an empty ``|`` line-block used to insert
    a blank line between merged snippets.
    """
    return isinstance(node, nodes.line_block) and not node.astext().strip()


class CombinedCodeBlock(CodeBlock):
    """
    A Sphinx directive that merges multiple nested code blocks into a
    single
    literal block.
    """

    def run(self) -> list[Node]:
        """
        Parse the directive content (which may contain multiple code-
        blocks)
        and return a single merged code-block node.
        """
        container = nodes.container()
        self.state.nested_parse(
            block=self.content,
            input_offset=self.content_offset,
            node=container,
        )

        new_content = StringList()
        for child in container:
            if _is_blank_separator(node=child):
                new_content.extend(other=StringList(initlist=[""]))
                continue

            # Nested parse yields element nodes as top-level children.
            assert isinstance(child, Element)
            for literal in _literal_blocks_from(node=child):
                code_snippet = literal.astext()
                stripped = code_snippet.rstrip("\n")
                lines = stripped.split(sep="\n")
                new_item_string_list = StringList(initlist=lines)
                new_content.extend(other=new_item_string_list)

        # Nested blocks are already parsed; applying the outer ``:dedent:``
        # again would strip characters from the merged code text.
        self.options.pop("dedent", None)

        self.content = new_content
        return super().run()


def setup(app: Sphinx) -> ExtensionMetadata:
    """Register the 'combined-code-block' directive with Sphinx."""
    app.add_directive(name="combined-code-block", cls=CombinedCodeBlock)
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
        "version": version(distribution_name="sphinx-combine"),
    }
