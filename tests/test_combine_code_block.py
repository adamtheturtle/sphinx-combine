"""Tests for Sphinx extensions."""

from collections.abc import Callable
from importlib.metadata import version
from io import StringIO
from pathlib import Path
from textwrap import dedent

import pytest
from sphinx.errors import SphinxWarning
from sphinx.testing.util import SphinxTestApp
from sphinx.util.console import nocolor

import sphinx_combine


@pytest.mark.parametrize(
    argnames="language_arguments",
    argvalues=[("python",), ()],
)
def test_combine_code_blocks(
    *,
    tmp_path: Path,
    make_app: Callable[..., SphinxTestApp],
    language_arguments: tuple[str, ...],
) -> None:
    """
    Test that 'combined-code-block' directive merges multiple code
    blocks into
    one single code block.
    """
    source_directory = tmp_path / "source"
    source_directory.mkdir()
    (source_directory / "conf.py").touch()

    source_file = source_directory / "index.rst"
    joined_language_arguments = " ".join(language_arguments)
    index_rst_content = dedent(
        text=f"""\
        Testing Combined Code Blocks
        ============================

        .. combined-code-block:: {joined_language_arguments}

           .. code-block::

               print("Hello from snippet one")

           .. code-block:: python

               print("Hello from snippet two")
        """
    )
    source_file.write_text(data=index_rst_content)

    app = make_app(
        srcdir=source_directory,
        exception_on_warning=True,
        confoverrides={"extensions": ["sphinx_combine"]},
    )
    app.build()
    assert app.statuscode == 0
    content_html = (app.outdir / "index.html").read_text()
    app.cleanup()

    equivalent_source = dedent(
        text=f"""\
        Testing Combined Code Blocks
        ============================

        .. code-block:: {joined_language_arguments}

            print("Hello from snippet one")
            print("Hello from snippet two")
        """,
    )

    source_file.write_text(data=equivalent_source)
    app_expected = make_app(
        srcdir=source_directory,
        exception_on_warning=True,
    )
    app_expected.build()
    assert app_expected.statuscode == 0

    expected_content_html = (app_expected.outdir / "index.html").read_text()
    assert content_html == expected_content_html


def test_combine_code_blocks_multiple_arguments(
    *,
    tmp_path: Path,
    make_app: Callable[..., SphinxTestApp],
) -> None:
    """
    Test that 'combined-code-block' directive raises an error if
    multiple
    language arguments are supplied.
    """
    source_directory = tmp_path / "source"
    source_directory.mkdir()

    (source_directory / "conf.py").touch()

    source_file = source_directory / "index.rst"
    index_rst_content = dedent(
        text="""\
        Testing Combined Code Blocks
        ============================

        .. combined-code-block:: python css

            .. code-block::

                print("Hello from snippet one")

            .. code-block::

                print("Hello from snippet two")
        """
    )
    source_file.write_text(data=index_rst_content)

    app = make_app(
        srcdir=source_directory,
        exception_on_warning=True,
        confoverrides={"extensions": ["sphinx_combine"]},
    )
    expected_error = f"{source_file.resolve()}:4:" + dedent(
        text="""\
        Error in "combined-code-block" directive:
        maximum 1 argument(s) allowed, 2 supplied.

        .. combined-code-block:: python css

            .. code-block::

                print("Hello from snippet one")

            .. code-block::

                print("Hello from snippet two")""",
    )
    with pytest.raises(expected_exception=SphinxWarning) as exc:
        app.build()
    assert str(object=exc.value) == expected_error


def test_emphasize_lines_with_multiline_code_blocks(
    *,
    tmp_path: Path,
    make_app: Callable[..., SphinxTestApp],
) -> None:
    """Test that 'combined-code-block' directive correctly handles
    :emphasize-
    lines: when code blocks contain multiple lines.

    This is a regression test for:
    https://github.com/adamtheturtle/sphinx-combine/issues/280

    The issue is that multi-line code snippets are stored as single
    StringList elements rather than being split by line. This causes
    :emphasize-lines: to fail because line numbers don't match.
    """
    source_directory = tmp_path / "source"
    source_directory.mkdir()
    (source_directory / "conf.py").touch()

    source_file = source_directory / "index.rst"
    # The combined block has 4 lines total (2 from each code-block).
    # We emphasize line 4, which should work if lines are split correctly.
    index_rst_content = dedent(
        text="""\
        Testing Emphasize Lines
        =======================

        .. combined-code-block:: python
           :emphasize-lines: 4

           .. code-block::

               line1 = "first"
               line2 = "second"

           .. code-block::

               line3 = "third"
               line4 = "fourth"
        """
    )
    source_file.write_text(data=index_rst_content)

    app = make_app(
        srcdir=source_directory,
        exception_on_warning=True,
        confoverrides={"extensions": ["sphinx_combine"]},
    )
    app.build()
    assert app.statuscode == 0
    content_html = (app.outdir / "index.html").read_text()
    app.cleanup()

    # The equivalent code-block with all lines combined should produce
    # the same HTML output.
    equivalent_source = dedent(
        text="""\
        Testing Emphasize Lines
        =======================

        .. code-block:: python
           :emphasize-lines: 4

           line1 = "first"
           line2 = "second"
           line3 = "third"
           line4 = "fourth"
        """,
    )

    source_file.write_text(data=equivalent_source)
    app_expected = make_app(
        srcdir=source_directory,
        exception_on_warning=True,
    )
    app_expected.build()
    assert app_expected.statuscode == 0

    expected_content_html = (app_expected.outdir / "index.html").read_text()
    assert content_html == expected_content_html


def test_no_spurious_blank_lines_between_blocks(
    *,
    tmp_path: Path,
    make_app: Callable[..., SphinxTestApp],
) -> None:
    """Test that no spurious blank lines appear between concatenated
    blocks.

    This is a regression test for:
    https://github.com/adamtheturtle/sphinx-combine/issues/371
    """
    source_directory = tmp_path / "source"
    source_directory.mkdir()
    (source_directory / "conf.py").touch()

    data_file = source_directory / "data.json"
    data_file.write_text(data='["a", "b"]')

    source_file = source_directory / "index.rst"
    index_rst_content = dedent(
        text="""\
        Testing No Spurious Blank Lines
        ===============================

        .. combined-code-block:: text

           .. code-block:: text

              items = [

           .. literalinclude:: data.json

           .. code-block:: text

              ]
        """
    )
    source_file.write_text(data=index_rst_content)

    app = make_app(
        srcdir=source_directory,
        exception_on_warning=True,
        confoverrides={"extensions": ["sphinx_combine"]},
    )
    app.build()
    assert app.statuscode == 0
    content_html = (app.outdir / "index.html").read_text()
    app.cleanup()

    equivalent_source = dedent(
        text="""\
        Testing No Spurious Blank Lines
        ===============================

        .. code-block:: text

            items = [
            ["a", "b"]
            ]
        """,
    )

    source_file.write_text(data=equivalent_source)
    app_expected = make_app(
        srcdir=source_directory,
        exception_on_warning=True,
    )
    app_expected.build()
    assert app_expected.statuscode == 0

    expected_content_html = (app_expected.outdir / "index.html").read_text()
    assert content_html == expected_content_html


def test_non_code_content_not_merged(
    *,
    tmp_path: Path,
    make_app: Callable[..., SphinxTestApp],
) -> None:
    """Test that prose and other non-code nodes are not merged into the
    output.

    This is a regression test for:
    https://github.com/adamtheturtle/sphinx-combine/issues/585
    """
    source_directory = tmp_path / "source"
    source_directory.mkdir()
    (source_directory / "conf.py").touch()

    source_file = source_directory / "index.rst"
    index_rst_content = dedent(
        text="""\
        Testing Non-Code Content
        ========================

        .. combined-code-block:: python

           .. code-block:: python

               x = 1

           This is regular text between code blocks.

           .. note::

              A note that must not appear in the code.

           .. code-block:: python

               y = 2
        """
    )
    source_file.write_text(data=index_rst_content)

    nocolor()
    warning_stream = StringIO()
    app = make_app(
        srcdir=source_directory,
        warning=warning_stream,
        confoverrides={"extensions": ["sphinx_combine"]},
    )
    app.build()
    assert app.statuscode == 0
    content_html = (app.outdir / "index.html").read_text()
    warning_path = f"{source_file.resolve()}.rst"
    expected_warning_text = (
        f"{warning_path}:4: WARNING: combined-code-block skipped non-code "
        "content of type paragraph [sphinx_combine.skipped_non_code]\n"
        f"{warning_path}:4: WARNING: combined-code-block skipped non-code "
        "content of type note [sphinx_combine.skipped_non_code]\n"
    )
    assert warning_stream.getvalue() == expected_warning_text
    app.cleanup()

    equivalent_source = dedent(
        text="""\
        Testing Non-Code Content
        ========================

        .. code-block:: python

            x = 1
            y = 2
        """,
    )

    source_file.write_text(data=equivalent_source)
    app_expected = make_app(
        srcdir=source_directory,
        exception_on_warning=True,
    )
    app_expected.build()
    assert app_expected.statuscode == 0

    expected_content_html = (app_expected.outdir / "index.html").read_text()
    assert content_html == expected_content_html


def test_skipped_non_code_content_raises_with_warningiserror(
    *,
    tmp_path: Path,
    make_app: Callable[..., SphinxTestApp],
) -> None:
    """Test that skipped non-code content becomes an error with -W.

    This is a regression test for:
    https://github.com/adamtheturtle/sphinx-combine/issues/666
    """
    source_directory = tmp_path / "source"
    source_directory.mkdir()
    (source_directory / "conf.py").touch()

    source_file = source_directory / "index.rst"
    index_rst_content = dedent(
        text="""\
        Testing Skipped Content Warning
        ===============================

        .. combined-code-block:: python

           .. code-block:: python

               x = 1

           This prose must warn.

           .. code-block:: python

               y = 2
        """
    )
    source_file.write_text(data=index_rst_content)

    app = make_app(
        srcdir=source_directory,
        exception_on_warning=True,
        confoverrides={"extensions": ["sphinx_combine"]},
    )
    with pytest.raises(expected_exception=SphinxWarning) as exc:
        app.build()
    expected_error = (
        f"({str(object=source_file.resolve())!r}, 4):"
        "combined-code-block skipped non-code content of type paragraph"
    )
    assert str(object=exc.value) == expected_error


def test_nested_caption_not_leaked_into_code(
    *,
    tmp_path: Path,
    make_app: Callable[..., SphinxTestApp],
) -> None:
    """Test that nested code-block captions are not merged into the code
    body.

    This is a regression test for:
    https://github.com/adamtheturtle/sphinx-combine/issues/652
    """
    source_directory = tmp_path / "source"
    source_directory.mkdir()
    (source_directory / "conf.py").touch()

    data_file = source_directory / "data.txt"
    data_file.write_text(data="from file\n")

    source_file = source_directory / "index.rst"
    index_rst_content = dedent(
        text="""\
        Testing Nested Captions
        =======================

        .. combined-code-block:: python

           .. code-block:: python
              :caption: First caption

              x = 1

           .. literalinclude:: data.txt
              :caption: Include caption
        """
    )
    source_file.write_text(data=index_rst_content)

    app = make_app(
        srcdir=source_directory,
        exception_on_warning=True,
        confoverrides={"extensions": ["sphinx_combine"]},
    )
    app.build()
    assert app.statuscode == 0
    content_html = (app.outdir / "index.html").read_text()
    app.cleanup()

    equivalent_source = dedent(
        text="""\
        Testing Nested Captions
        =======================

        .. code-block:: python

            x = 1
            from file
        """,
    )

    source_file.write_text(data=equivalent_source)
    app_expected = make_app(
        srcdir=source_directory,
        exception_on_warning=True,
    )
    app_expected.build()
    assert app_expected.statuscode == 0

    expected_content_html = (app_expected.outdir / "index.html").read_text()
    assert content_html == expected_content_html


def test_pipe_blank_line_separator_preserved(
    *,
    tmp_path: Path,
    make_app: Callable[..., SphinxTestApp],
) -> None:
    """Test that an empty ``|`` line-block still inserts a blank line
    between merged snippets.
    """
    source_directory = tmp_path / "source"
    source_directory.mkdir()
    (source_directory / "conf.py").touch()

    source_file = source_directory / "index.rst"
    index_rst_content = dedent(
        text="""\
        Testing Blank Separator
        =======================

        .. combined-code-block:: python

           .. code-block:: python

               a = 1

           |

           .. code-block:: python

               b = 2
        """
    )
    source_file.write_text(data=index_rst_content)

    app = make_app(
        srcdir=source_directory,
        exception_on_warning=True,
        confoverrides={"extensions": ["sphinx_combine"]},
    )
    app.build()
    assert app.statuscode == 0
    content_html = (app.outdir / "index.html").read_text()
    app.cleanup()

    equivalent_source = dedent(
        text="""\
        Testing Blank Separator
        =======================

        .. code-block:: python

            a = 1

            b = 2
        """,
    )

    source_file.write_text(data=equivalent_source)
    app_expected = make_app(
        srcdir=source_directory,
        exception_on_warning=True,
    )
    app_expected.build()
    assert app_expected.statuscode == 0

    expected_content_html = (app_expected.outdir / "index.html").read_text()
    assert content_html == expected_content_html


def test_non_empty_line_block_not_merged(
    *,
    tmp_path: Path,
    make_app: Callable[..., SphinxTestApp],
) -> None:
    """Test that a non-empty line-block is skipped (unlike empty ``|``).

    This is a regression test for:
    https://github.com/adamtheturtle/sphinx-combine/issues/633
    """
    source_directory = tmp_path / "source"
    source_directory.mkdir()
    (source_directory / "conf.py").touch()

    source_file = source_directory / "index.rst"
    index_rst_content = dedent(
        text="""\
        Testing Line Blocks
        ===================

        .. combined-code-block:: python

           .. code-block:: python

               a = 1

           | keep out
           | of the code

           .. code-block:: python

               b = 2
        """
    )
    source_file.write_text(data=index_rst_content)

    nocolor()
    warning_stream = StringIO()
    app = make_app(
        srcdir=source_directory,
        warning=warning_stream,
        confoverrides={"extensions": ["sphinx_combine"]},
    )
    app.build()
    assert app.statuscode == 0
    content_html = (app.outdir / "index.html").read_text()
    warning_path = f"{source_file.resolve()}.rst"
    expected_warning_text = (
        f"{warning_path}:4: WARNING: combined-code-block skipped non-code "
        "content of type line_block [sphinx_combine.skipped_non_code]\n"
    )
    assert warning_stream.getvalue() == expected_warning_text
    app.cleanup()

    equivalent_source = dedent(
        text="""\
        Testing Line Blocks
        ===================

        .. code-block:: python

            a = 1
            b = 2
        """,
    )

    source_file.write_text(data=equivalent_source)
    app_expected = make_app(
        srcdir=source_directory,
        exception_on_warning=True,
    )
    app_expected.build()
    assert app_expected.statuscode == 0

    expected_content_html = (app_expected.outdir / "index.html").read_text()
    assert content_html == expected_content_html


def test_outer_dedent_does_not_mangle_merged_code(
    *,
    tmp_path: Path,
    make_app: Callable[..., SphinxTestApp],
) -> None:
    """Test that an outer ``:dedent:`` does not strip merged code text.

    Nested snippets are already normalized by nested parsing. Re-applying
    ``:dedent:`` in ``CodeBlock.run`` previously deleted leading characters
    from each line (and broke ``:emphasize-lines:`` / ``:caption:``).

    This is a regression test for:
    https://github.com/adamtheturtle/sphinx-combine/issues/657
    """
    source_directory = tmp_path / "source"
    source_directory.mkdir()
    (source_directory / "conf.py").touch()

    source_file = source_directory / "index.rst"
    index_rst_content = dedent(
        text="""\
        Testing Outer Dedent
        ====================

        .. combined-code-block:: python
           :dedent: 4
           :emphasize-lines: 2
           :caption: Combined

           .. code-block:: python

                   x = 1

           .. code-block:: python

                   y = 2
        """
    )
    source_file.write_text(data=index_rst_content)

    app = make_app(
        srcdir=source_directory,
        exception_on_warning=True,
        confoverrides={"extensions": ["sphinx_combine"]},
    )
    app.build()
    assert app.statuscode == 0
    content_html = (app.outdir / "index.html").read_text()
    app.cleanup()

    equivalent_source = dedent(
        text="""\
        Testing Outer Dedent
        ====================

        .. code-block:: python
           :emphasize-lines: 2
           :caption: Combined

           x = 1
           y = 2
        """,
    )

    source_file.write_text(data=equivalent_source)
    app_expected = make_app(
        srcdir=source_directory,
        exception_on_warning=True,
    )
    app_expected.build()
    assert app_expected.statuscode == 0

    expected_content_html = (app_expected.outdir / "index.html").read_text()
    assert content_html == expected_content_html


def test_myst_nested_combined_code_block(
    *,
    tmp_path: Path,
    make_app: Callable[..., SphinxTestApp],
) -> None:
    """Test MyST nested fences merge when the outer fence is longer.

    This is a regression test for:
    https://github.com/adamtheturtle/sphinx-combine/issues/660
    """
    source_directory = tmp_path / "source"
    source_directory.mkdir()
    (source_directory / "conf.py").touch()

    source_file = source_directory / "index.md"
    index_md_content = dedent(
        text="""\
        # Testing MyST Combined Code Blocks

        ````{combined-code-block} python
        ```{code-block} python
        x = 1
        ```

        ```{literalinclude} data.txt
        ```
        ````
        """
    )
    source_file.write_text(data=index_md_content)
    (source_directory / "data.txt").write_text(data="y = 2\n")

    app = make_app(
        srcdir=source_directory,
        exception_on_warning=True,
        confoverrides={
            "extensions": ["myst_parser", "sphinx_combine"],
            "source_suffix": {
                ".md": "markdown",
                ".rst": "restructuredtext",
            },
        },
    )
    app.build()
    assert app.statuscode == 0
    content_html = (app.outdir / "index.html").read_text()
    app.cleanup()

    equivalent_source = dedent(
        text="""\
        # Testing MyST Combined Code Blocks

        ```{code-block} python
        x = 1
        y = 2
        ```
        """,
    )

    source_file.write_text(data=equivalent_source)
    app_expected = make_app(
        srcdir=source_directory,
        exception_on_warning=True,
        confoverrides={
            "extensions": ["myst_parser"],
            "source_suffix": {
                ".md": "markdown",
                ".rst": "restructuredtext",
            },
        },
    )
    app_expected.build()
    assert app_expected.statuscode == 0

    expected_content_html = (app_expected.outdir / "index.html").read_text()
    assert content_html == expected_content_html


def test_setup(
    *,
    tmp_path: Path,
    make_app: Callable[..., SphinxTestApp],
) -> None:
    """Test that the setup function returns the expected metadata."""
    source_directory = tmp_path / "source"
    source_directory.mkdir()
    (source_directory / "conf.py").touch()

    app = make_app(
        srcdir=source_directory,
        confoverrides={"extensions": ["sphinx_combine"]},
    )
    setup_result = sphinx_combine.setup(app=app)
    pkg_version = version(distribution_name="sphinx-combine")
    assert setup_result == {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
        "version": pkg_version,
    }
