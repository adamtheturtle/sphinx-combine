|Build Status| |codecov| |PyPI|

Sphinx Combine
==============

Extension for Sphinx which enables combining code blocks.

.. contents::

Installation
------------

``sphinx-combine`` is compatible with Sphinx 7.2.0+ using Python 3.10+.

.. code-block:: console

   $ pip install sphinx-combine

Setup
-----

Add the following to ``conf.py`` to enable the extension:

.. code-block:: python

   """Configuration for Sphinx."""

   extensions = ["sphinxcontrib.spelling"]  # Example existing extensions

   extensions += ["sphinx_combine"]

Contributing
------------

See `CONTRIBUTING.rst <./CONTRIBUTING.rst>`_.

.. |Build Status| image:: https://github.com/adamtheturtle/sphinx-combine/actions/workflows/ci.yml/badge.svg?branch=main
   :target: https://github.com/adamtheturtle/sphinx-combine/actions
.. _code-block: http://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-code-block
.. |codecov| image:: https://codecov.io/gh/adamtheturtle/sphinx-combine/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/adamtheturtle/sphinx-combine
.. |PyPI| image:: https://badge.fury.io/py/sphinx-combine.svg
   :target: https://badge.fury.io/py/sphinx-combine
