"""
Tests for Sphinx extensions.
"""

from collections.abc import Callable
from importlib.metadata import version
from pathlib import Path
from textwrap import dedent

import pytest
from sphinx.errors import SphinxWarning
from sphinx.testing.util import SphinxTestApp

import sphinx_combine


@pytest.mark.parametrize(
    argnames="language_arguments",
    argvalues=[("python",), ()],
)
def test_combine_code_blocks(
    tmp_path: Path,
    make_app: Callable[..., SphinxTestApp],
    language_arguments: tuple[str, ...],
) -> None:
    """
    Test that 'combined-code-block' directive merges multiple code blocks into
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
    tmp_path: Path,
    make_app: Callable[..., SphinxTestApp],
) -> None:
    """
    Test that 'combined-code-block' directive raises an error if multiple
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
    expected_error = (
        'Error in "combined-code-block" directive:\n'
        "maximum 1 argument(s) allowed, 2 supplied."
    )
    with pytest.raises(expected_exception=SphinxWarning) as exc:
        app.build()
    assert expected_error in str(object=exc.value)


def test_emphasize_lines_with_multiline_code_blocks(
    tmp_path: Path,
    make_app: Callable[..., SphinxTestApp],
) -> None:
    """Test that 'combined-code-block' directive correctly handles :emphasize-
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


def test_setup(
    tmp_path: Path,
    make_app: Callable[..., SphinxTestApp],
) -> None:
    """
    Test that the setup function returns the expected metadata.
    """
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
