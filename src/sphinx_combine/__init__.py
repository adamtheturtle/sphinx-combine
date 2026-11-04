"""
Sphinx extension to combine multiple nested code-blocks into a single
one.
"""

import subprocess
from importlib.metadata import version
from typing import TypeGuard

from docutils import nodes
from docutils.nodes import Element, Node
from docutils.statemachine import StringList
from sphinx.application import Sphinx
from sphinx.directives.code import CodeBlock
from sphinx.util import logging
from sphinx.util.typing import ExtensionMetadata
from typing_extensions import override

LOGGER = logging.getLogger(name=__name__)


def _literal_blocks_from(*, node: Element) -> list[nodes.literal_block]:
    """
    Return literal_block nodes to merge from a top-level nested-parse
    child.

    Caption wrappers are ``container`` nodes with ``literal_block=True``
    that contain a caption plus the real ``literal_block``. Only the
    inner literal content should be merged.
    """
    match node:
        case nodes.literal_block():
            return [node]
        case nodes.container() if bool(node.get(key="literal_block")):
            return list(node.findall(condition=nodes.literal_block))
        case _:
            return []


def _is_blank_separator(*, node: Node) -> bool:
    """
    Return whether ``node`` is an empty ``|`` line-block used to insert
    a blank line between merged snippets.
    """
    return isinstance(node, nodes.line_block) and node.astext().strip() == ""


def _is_argument_list(value: object, /) -> TypeGuard[list[object]]:
    """Narrow external Sphinx configuration without asserting its
    shape.
    """
    return isinstance(value, list)


def _is_string_list(value: object, /) -> TypeGuard[list[str]]:
    """Validate configuration before passing arguments to a process."""
    return _is_argument_list(value) and all(
        isinstance(argument, str) for argument in value
    )


class CombinedCodeBlock(CodeBlock):
    """
    A Sphinx directive that merges multiple nested code blocks into a
    single
    literal block.
    """

    @override
    def run(self) -> list[Node]:
        """
        Parse the directive content (which may contain multiple code-
        blocks)
        and return a single merged code-block node.
        """
        container = nodes.container()
        _ = self.state.nested_parse(
            block=self.content,
            input_offset=self.content_offset,
            node=container,
        )

        new_content = StringList()
        location = self.state_machine.get_source_and_line(lineno=self.lineno)
        for child in container:
            if _is_blank_separator(node=child):
                new_content.extend(other=StringList(initlist=[""]))
                continue

            # Nested parse yields element nodes as top-level children.
            assert isinstance(child, Element)
            literals = _literal_blocks_from(node=child)
            if len(literals) == 0:
                LOGGER.warning(
                    "combined-code-block skipped non-code content of type %s",
                    child.__class__.__name__,
                    type="sphinx_combine",
                    subtype="skipped_non_code",
                    location=location,
                )
                continue

            for literal in literals:
                code_snippet = literal.astext()
                stripped = code_snippet.rstrip("\n")
                lines = stripped.split(sep="\n")
                new_item_string_list = StringList(initlist=lines)
                new_content.extend(other=new_item_string_list)

        # Nested blocks are already parsed; applying the outer ``:dedent:``
        # again would strip characters from the merged code text.
        self.options.pop("dedent", None)

        self.content: StringList = self._format_content(content=new_content)
        return super().run()

    def _format_content(self, *, content: StringList) -> StringList:
        """Format the complete program only for configured languages."""
        language = self.arguments[0] if len(self.arguments) > 0 else "none"
        formatters = self.config.sphinx_combine_formatters
        if language not in formatters:
            return content
        dependencies = self.config.sphinx_combine_formatter_dependencies
        if not _is_string_list(dependencies):
            msg = (
                "sphinx_combine_formatter_dependencies must be "
                "a list of paths."
            )
            raise self.error(message=msg)
        for dependency in dependencies:
            self.env.note_dependency(filename=dependency)
        command = formatters[language]
        if not _is_string_list(command) or len(command) == 0:
            msg = (
                f"sphinx_combine_formatters[{language!r}] must be a "
                "nonempty list of command arguments."
            )
            raise self.error(message=msg)
        code = "\n".join(content) + "\n"
        try:
            result = subprocess.run(  # noqa: S603 - trusted configuration arguments
                args=command,
                input=code,
                capture_output=True,
                encoding="utf-8",
                check=True,
                cwd=self.env.srcdir,
                timeout=30,
            )
        except (
            OSError,
            subprocess.SubprocessError,
            ValueError,
        ) as error:
            detail = (
                f"exit status {error.returncode}: {error.stderr}"
                if isinstance(error, subprocess.CalledProcessError)
                else str(object=error)
            )
            msg = (
                f"combined-code-block formatter for {language!r} "
                f"failed: {detail}"
            )
            raise self.error(message=msg) from error
        if code.strip() != "" and result.stdout.strip() == "":
            msg = (
                f"combined-code-block formatter for {language!r} "
                "discarded the code."
            )
            raise self.error(message=msg)
        return StringList(initlist=result.stdout.splitlines())


def setup(app: Sphinx) -> ExtensionMetadata:
    """Register the 'combined-code-block' directive with Sphinx."""
    app.add_directive(name="combined-code-block", cls=CombinedCodeBlock)
    app.add_config_value(
        name="sphinx_combine_formatters",
        default={},
        rebuild="env",
        types={dict},
    )
    app.add_config_value(
        name="sphinx_combine_formatter_dependencies",
        default=[],
        rebuild="env",
        types={list},
    )
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
        "version": version(distribution_name="sphinx-combine"),
    }
