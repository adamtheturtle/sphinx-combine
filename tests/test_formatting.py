"""Exercise configured formatters against complete combined blocks."""

import os
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from unittest.mock import patch

import pytest
from docutils.nodes import literal_block
from sphinx.errors import SphinxWarning
from sphinx.testing.util import SphinxTestApp


def _source(directory: Path, /) -> None:
    """Create a document with two fragments and an outer option."""
    directory.mkdir()
    (directory / "conf.py").touch()
    _ = (directory / "index.rst").write_text(
        data=""".. combined-code-block:: objective-c
   :linenos:

   .. code-block:: text

      first

   |

   .. code-block:: text

      second
""",
        encoding="utf-8",
    )


def test_formatter_receives_joined_code(
    *, tmp_path: Path, make_app: Callable[..., SphinxTestApp]
) -> None:
    """Use standard input, literal arguments, UTF-8, and the source
    directory.
    """
    source = tmp_path / "source"
    _source(source)
    with (source / "index.rst").open(mode="a", encoding="utf-8") as document:
        _ = document.write(
            "\n.. combined-code-block:: python\n\n"
            "   .. code-block:: python\n\n      unchanged = 1\n"
        )
    script = source / "formatter with spaces.py"
    _ = script.write_text(
        data="""import pathlib
import sys
assert sys.stdin.read() == 'first\\n\\nsecond\\n'
assert pathlib.Path.cwd() == pathlib.Path(__file__).parent
assert sys.argv[1] == 'literal $(argument);'
print('formatted café')
""",
        encoding="utf-8",
    )
    app = make_app(
        srcdir=source,
        exception_on_warning=True,
        confoverrides={
            "extensions": ["sphinx_combine"],
            "sphinx_combine_formatters": {
                "objective-c": [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(object=script),
                    "literal $(argument);",
                ],
            },
        },
    )
    app.build()
    blocks = list(
        app.env.get_doctree(docname="index").findall(condition=literal_block)
    )
    assert [block.astext() for block in blocks] == [
        "formatted café",
        "unchanged = 1",
    ]
    assert blocks[0]["linenos"] is True


@pytest.mark.parametrize(
    argnames=("command", "message"),
    argvalues=[
        ([], "nonempty list"),
        ("not-an-argument-list", "nonempty list"),
        ([123], "nonempty list"),
        (["missing-combine-formatter-executable"], "failed"),
        ([sys.executable, "\0"], "failed"),
        ([sys.executable, "-c", "import sys; sys.exit(7)"], "exit status 7"),
        (
            [
                sys.executable,
                "-c",
                "import sys; sys.stderr.write('broken formatter');sys.exit(2)",
            ],
            "broken formatter",
        ),
        ([sys.executable, "-c", "pass"], "discarded the code"),
        (
            [
                sys.executable,
                "-c",
                "import sys; sys.stdout.buffer.write(bytes([255]))",
            ],
            "failed",
        ),
    ],
)
def test_formatter_failures(
    *,
    tmp_path: Path,
    make_app: Callable[..., SphinxTestApp],
    command: object,
    message: str,
) -> None:
    """Failure must name the directive location rather than hide code."""
    source = tmp_path / "source"
    _source(source)
    app = make_app(
        srcdir=source,
        exception_on_warning=True,
        confoverrides={
            "extensions": ["sphinx_combine"],
            "sphinx_combine_formatters": {"objective-c": command},
        },
    )
    with pytest.raises(
        expected_exception=SphinxWarning, match=message
    ) as caught:
        app.build()
    assert f"{source / 'index.rst'}:1:" in str(object=caught.value)


def test_formatter_timeout(
    *, tmp_path: Path, make_app: Callable[..., SphinxTestApp]
) -> None:
    """A hung formatter reports a source-located build failure."""
    source = tmp_path / "source"
    _source(source)
    app = make_app(
        srcdir=source,
        exception_on_warning=True,
        confoverrides={
            "extensions": ["sphinx_combine"],
            "sphinx_combine_formatters": {"objective-c": ["formatter"]},
        },
    )
    with (
        patch(
            target="sphinx_combine.subprocess.run",
            side_effect=subprocess.TimeoutExpired(
                cmd=["formatter"], timeout=30
            ),
        ),
        pytest.raises(expected_exception=SphinxWarning, match="timed out"),
    ):
        app.build()


def test_formatter_configuration_rebuilds_environment(
    *, tmp_path: Path, make_app: Callable[..., SphinxTestApp]
) -> None:
    """Changing formatter arguments must invalidate cached documents."""
    source = tmp_path / "source"
    _source(source)
    for output in ["first version", "second version"]:
        app = make_app(
            srcdir=source,
            freshenv=False,
            exception_on_warning=True,
            confoverrides={
                "extensions": ["sphinx_combine"],
                "sphinx_combine_formatters": {
                    "objective-c": [sys.executable, "-c", f"print({output!r})"]
                },
            },
        )
        app.build()
        blocks = list(
            app.env.get_doctree(docname="index").findall(
                condition=literal_block
            )
        )
        assert blocks[0].astext() == output
        app.cleanup()


def test_formatter_dependency_rebuilds_document(
    *, tmp_path: Path, make_app: Callable[..., SphinxTestApp]
) -> None:
    """Style changes rebuild formatted documents without editing their
    source.
    """
    source = tmp_path / "source"
    _source(source)
    style = tmp_path / "style"
    _ = style.write_text(data="first style", encoding="utf-8")
    overrides = {
        "extensions": ["sphinx_combine"],
        "sphinx_combine_formatters": {
            "objective-c": [
                sys.executable,
                "-c",
                "import pathlib;print(pathlib.Path('../style').read_text())",
            ]
        },
        "sphinx_combine_formatter_dependencies": ["../style"],
    }
    for output in ["first style", "second style"]:
        if output == "second style":
            _ = style.write_text(data=output, encoding="utf-8")
            changed = time.time() + 1
            os.utime(path=style, times=(changed, changed))
        app = make_app(
            srcdir=source,
            freshenv=False,
            exception_on_warning=True,
            confoverrides=overrides,
        )
        app.build()
        blocks = list(
            app.env.get_doctree(docname="index").findall(
                condition=literal_block
            )
        )
        assert blocks[0].astext() == output
        assert style.resolve() in {
            (Path(app.srcdir) / item).resolve()
            for item in app.env.dependencies["index"]
        }
        app.cleanup()


def test_invalid_formatter_dependencies(
    *, tmp_path: Path, make_app: Callable[..., SphinxTestApp]
) -> None:
    """Reject dependency entries which are not file paths."""
    source = tmp_path / "source"
    _source(source)
    app = make_app(
        srcdir=source,
        exception_on_warning=True,
        confoverrides={
            "extensions": ["sphinx_combine"],
            "sphinx_combine_formatters": {
                "objective-c": [sys.executable, "-c", "pass"]
            },
            "sphinx_combine_formatter_dependencies": [123],
        },
    )
    with pytest.raises(
        expected_exception=SphinxWarning, match="list of paths"
    ):
        app.build()
