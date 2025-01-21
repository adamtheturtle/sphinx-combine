"""
Tests for Sphinx extensions.
"""

from collections.abc import Callable
from pathlib import Path
from textwrap import dedent

import pytest
from sphinx.errors import SphinxWarning
from sphinx.testing.util import SphinxTestApp


@pytest.mark.parametrize(
    argnames="language_arguments",
    argvalues=[(("python",), ())],
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

    conf_py = source_directory / "conf.py"
    conf_py_content = dedent(
        text="""\
        extensions = ['sphinx_combine']
        """,
    )
    conf_py.write_text(data=conf_py_content)

    source_file = source_directory / "index.rst"
    joined_language_arguments = " ".join(language_arguments)
    index_rst_content = dedent(
        text=f"""\
        Testing Combined Code Blocks
        ============================

        .. combined-code-block:: {joined_language_arguments}

           .. code-block::

               print("Hello from snippet one")

           .. code-block::

               print("Hello from snippet two")
        """
    )
    source_file.write_text(data=index_rst_content)

    app = make_app(srcdir=source_directory, exception_on_warning=True)
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

    conf_py = source_directory / "conf.py"
    conf_py_content = dedent(
        text="""\
        extensions = ['sphinx_combine']
        """,
    )
    conf_py.write_text(data=conf_py_content)

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

    app = make_app(srcdir=source_directory, exception_on_warning=True)
    expected_error = (
        'Error in "combined-code-block" directive:\n'
        "maximum 1 argument(s) allowed, 2 supplied."
    )
    with pytest.raises(expected_exception=SphinxWarning) as exc:
        app.build()
    assert expected_error in str(object=exc.value)
