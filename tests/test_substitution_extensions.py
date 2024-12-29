"""
Tests for Sphinx extensions.
"""

from collections.abc import Callable
from pathlib import Path
from textwrap import dedent

from sphinx.testing.util import SphinxTestApp


def test_combine_code_blocks(
    tmp_path: Path,
    make_app: Callable[..., SphinxTestApp],
) -> None:
    """
    The ``code-block`` directive replaces the placeholders defined in
    ``conf.py`` as specified.
    """
    source_directory = tmp_path / "source"
    source_directory.mkdir()
    source_file = source_directory / "index.rst"
    conf_py = source_directory / "conf.py"
    conf_py_content = dedent(
        text="""\
        extensions = ['sphinx_conbine']
        """,
    )
    conf_py.write_text(data=conf_py_content)
    source_file_content = dedent(
        text="""\
        .. code-block:: shell
           :substitutions:

           $ PRE-|a|-POST
        """,
    )
    source_file.write_text(data=source_file_content)
    app = make_app(srcdir=source_directory)
    app.build()
    expected = "PRE-example_substitution-POST"
    content_html = app.outdir / "index.html"
    assert expected in content_html.read_text()
