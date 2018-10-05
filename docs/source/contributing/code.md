# Contributing code

## Basic requirements and standards

- A [new ticket](http://dev.deluge-torrent.org/newticket) is required for bugs
  or features. Search the ticket system first, to avoid filing a duplicate.
- Ensure code follows the [syntax and conventions](#syntax-and-conventions).
- Code must pass tests. See [testing.md] for
  information on how to run and write unit tests.
- Commit messages are informative.

## Pull request process:

- Fork us on [github](https://github.com/deluge-torrent/deluge).
- Clone your repository.
- Create a feature branch for your issue.
- Apply your changes:
  - Add them, and then commit them to your branch.
  - Run the tests until they pass.
  - When you feel you are finished, rebase your commits to ensure a simple
    and informative commit log.
- Create a pull request on github from your forked repository.
  - Verify that the tests run by [Travis-ci](https://travis-ci.org/deluge-torrent/deluge)
    are passing.

## Syntax and conventions

### Code formatters

We use two applications to automatically format the code to save development
time. They are both run with pre-commit.

#### Black

- Python

#### Prettier

- Javascript
- CSS
- YAML
- Markdown

### Common

- Line length: `79` chars.
- Indent: `4 spaces`, no tabs.
- All code should use `'single quotes'`.

### Python

We follow [PEP8](http://www.python.org/dev/peps/pep-0008/) and
[Python Code Style](http://docs.python-guide.org/en/latest/writing/style/)
which is adhered to with Black formatter.

- Code '''must''' pass [flake8](https://pypi.python.org/pypi/flake8) (w/[https://pypi.python.org/pypi/flake8-quotes flake8-quotes]), [https://pypi.python.org/pypi/isort isort] and [http://www.pylint.org/ Pylint] source code checkers.

  flake8 deluge
  isort -rc -df deluge
  pylint deluge
  pylint deluge/plugins/\*/deluge/

- Using the [http://pre-commit.com/ pre-commit] app can aid in picking up
  issues before creating git commits.

#### Strings and bytes

To prevent bugs or errors in the code byte strings (`str`) must be decoded to
strings (unicode strings, `unicode`) on input and then encoded on output.

_Notes:_

- PyGTK/GTK+ will accept `str` (utf8 encoded) or `unicode` but will only return
  `str`. See [http://python-gtk-3-tutorial.readthedocs.org/en/latest/unicode.html GTK+ Unicode] docs.
- There is a `bytearray` type which enables in-place modification of a string.
  See [Python Bytearrays](http://stackoverflow.com/a/9099337/175584)
- Python 3 renames `unicode` to `str` type and byte strings become `bytes` type.

### Javascript

- Classes should follow the Ext coding style.
- Class names should be in !CamelCase
- Instances of classes should use camelCase.

### Path separators

- All relative path separators used within code should be converted to posix
  format `/`, so should not contain `\` or `\\`. This is to prevent confusion
  when dealing with cross-platform clients and servers.

### Docstrings

All new docstrings must use Napoleon
[Google Style](http://www.sphinx-doc.org/en/stable/ext/napoleon.html)
with old docstrings eventually converted over.

Google Style example:

    def func(arg):
       """Function purpose.

       Args:
           arg (type): Description.

       Returns:
          type: Description. If the line is too, long indent next
             line with three spaces.
       """
       return

See complete list of [http://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html#docstring-sections supported headers].

Verify that the documentation parses correctly with:

    python setup.py build_docs
