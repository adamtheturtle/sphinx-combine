"""
Tests for Sphinx extensions.
"""

from collections.abc import Callable
from pathlib import Path
from textwrap import dedent

import pytest
from bs4 import BeautifulSoup
from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx("html")
def test_combine_code_blocks(
    tmp_path: Path,
    make_app: Callable[..., SphinxTestApp],
) -> None:
    """
    Test that 'combined-code-block' directive merges multiple code blocks into
    one single code block.
    """
    source_directory = tmp_path / "source"
    source_directory.mkdir()

    # Write conf.py
    conf_py = source_directory / "conf.py"
    conf_py_content = dedent(
        text="""\
        extensions = ['sphinx_combine']
        """,
    )
    conf_py.write_text(data=conf_py_content)

    # Write index.rst
    source_file = source_directory / "index.rst"
    index_rst_content = dedent(
        text="""\
        Testing Combined Code Blocks
        ============================

        .. combined-code-block::
           :language: python

           .. code-block:: python

               print("Hello from snippet one")

           .. code-block:: python

               print("Hello from snippet two")
        """
    )
    source_file.write_text(data=index_rst_content)

    app = make_app(srcdir=source_directory)
    app.build()

    html_output = source_directory / "_build" / "html" / "index.html"
    html_content = html_output.read_text(encoding="utf-8")

    soup = BeautifulSoup(markup=html_content, features="html.parser")

    code_divs = soup.find_all(name="div", class_="highlight")

    assert (
        len(code_divs) == 1
    ), f"Expected one code block, found {len(code_divs)}."

    code_block_text = code_divs[0].get_text()
    assert "Hello from snippet one" in code_block_text
    assert "Hello from snippet two" in code_block_text
