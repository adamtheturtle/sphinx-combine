Changelog
=========

.. contents::

.. towncrier release notes start

2026.08.23.1
------------

- Warn when ``combined-code-block`` skips nested non-code content instead of silently dropping it.

2026.08.23
----------

- Only merge nested ``literal_block`` nodes (and empty ``|`` separators), so prose, admonitions, captions, and other non-code content are no longer highlighted as code.

- Do not re-apply an outer ``:dedent:`` to already-merged nested code, which previously stripped characters from each line.

- Document MyST nesting with a longer outer fence so nested code blocks merge correctly.

2026.03.13
----------


2026.01.11
----------


2025.11.15
----------

* Give version in extension metadata.

2024.12.30.1
------------

2024.12.30
----------

2024.12.29
----------
