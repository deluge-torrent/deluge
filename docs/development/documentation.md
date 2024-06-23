# Documentation

## Sphinx
We use Sphinx to create the documentation from docstrings in code.

```
pip install sphinx
pip install sphinxcontrib-napoleon
```

The Sphinx config is located in `docs/conf.py`

If new source files are added, auto-create the new `rst` files:

```
sphinx-apidoc -o docs/source/modules -T deluge deluge/tests
```

The manually updated `rst` files are:
- `index.rst` - The index page for Deluge documentation
- `docs/source/interfaces/` - User info on the different clients
- `docs/source/core/` - Documentation of the DelugeRPC

To build the docs:

```
python setup.py build_docs
```

### Notes
There are two uses of `Mock` classes for catching/ignoring import errors:
- In `conf.py` it is only applied to modules listed in `MOCK_MODULES`.
- In `setup.py` it is used for any other `ImportError` or `Exception`. 

## man pages

Located in `docs/man`
