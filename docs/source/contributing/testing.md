# Running tests

Testing uses [PyTest] framework and [PyTest-Twisted] to handle Twisted framework.

## Testing

The tests are located in the source folder under `deluge/tests`.
The tests are run from the project root directory.
View the unit test coverage at: [deluge-torrent.github.io](http://deluge-torrent.github.io)

### Pytest

    pytest deluge/tests
    pytest deluge/tests/test_client.py
    pytest deluge/tests/test_client.py -k test_connect_localclient

### Plugin

Running the tests for a specific plugin (requires [pytest](https://pypi.python.org/pypi/pytest)):

    pytest deluge/plugins/<name-of-plugin>

## Tox

All the tests for Deluge can be run using [Tox](https://pypi.python.org/pypi/tox)

### See available targets:

    tox -l
    py3
    lint
    docs

### Run specific test:

    tox -e py3

### Verify code with pre-commit:

    tox -e lint

## CI

Deluge develop branch is tested automatically by GitHub actions.

When creating a pull request (PR) on [github], units tests will be automatically be run.

[github]: https://github.com/deluge-torrent/deluge/pulls
[pytest]: https://docs.pytest.org/en/
[pytest-twisted]: https://github.com/pytest-dev/pytest-twisted
