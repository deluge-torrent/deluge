# Coding Styles

## Common
* Line length: Maximum of `119` rather than usual `79`. That said, where possible keep it between `79-99` to keep it readable.
* Indent: `4 spaces`, no tabs.
* All code should use `'single quotes'`.

## Python
 Deluge follows [PEP8](http://www.python.org/dev/peps/pep-0008/) and [Python Code Style](http://docs.python-guide.org/en/latest/writing/style/) with line length the only exception.

* Code **must** pass [flake8](https://pypi.python.org/pypi/flake8) (w/[flake8-quotes](https://pypi.python.org/pypi/flake8-quotes)), [isort](https://pypi.python.org/pypi/isort) and [Pylint](http://www.pylint.org/) source code checkers.

```
flake8 deluge
isort -rc -df deluge
pylint deluge
pylint deluge/plugins/*/deluge/
```

* Using the [pre-commit](http://pre-commit.com/) app can aid in picking up issues before creating git commits.

* All byte strings (`str`) should be decoded to strings (unicode strings, `unicode`) on input and encoded back to byte strings on output. [From Stackoverflow:](http://stackoverflow.com/a/606199/175584)

```
>>> b"abcde"
b'abcde'
>>> b"abcde".decode("utf-8")
'abcde'
```
  *Notes:*
* *PyGTK/GTK+ will accept `str` (utf8 encoded) or `unicode` but will only return `str`. See [GTK+ Unicode](http://python-gtk-3-tutorial.readthedocs.org/en/latest/unicode.html) docs. *

* *There is also a `bytearray` type which enables in-place modification of a string. See [Python Bytearrays](http://stackoverflow.com/a/9099337/175584) *

* *For reference Python 3 renames `unicode` to `str` type and byte strings become `bytes` type. *


* All relative path separators used within code should be converted to posix format `/`, so should not contain `\` or `\\`. This is to prevent confusion when dealing with cross-platform clients and servers.

### Docstrings

You will find a mix of the older [reStructuredText](http://docutils.sourceforge.net/docs/user/rst/quickref.html) and newer, easier to read, [Sphinx Napoleon](http://sphinxcontrib-napoleon.readthedocs.org/en/latest/) format.

Going forward the Napoleon [Google Style](http://sphinxcontrib-napoleon.readthedocs.org/en/latest/example_google.html) will be used for all new doctrings and eventually convert over the rest.

Google Style short example:

```
def func(arg):
   """Function purpose.

   Args:
       arg (type): Description.

   Returns:
      type: Description. If the line is too, long indent next
         line with three spaces.

   """
```

Most common sections are `Args` and `Returns`. See complete list of [supported headers](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/#docstring-sections).

Verify that the documentation parses correctly with:

```
python setup.py build_docs
```

### Python References

Useful links to style guides from other projects:

* [CKAN Python coding standards](http://docs.ckan.org/en/latest/contributing/python.html)
* [Google Python Style Guide](http://google-styleguide.googlecode.com/svn/trunk/pyguide.html)
* [Best of the Best Practices Guide for Python](https://gist.github.com/sloria/7001839)

## Javascript

Using [codepainter](https://github.com/jedmao/codepainter) with `hautelook` style will ensure a consistent coding style.

```
codepaint xform -p hautelook "file.js"
```

* Classes should follow the Ext coding style.
* Class names should be in CamelCase
* Instances of classes should use camelCase.
