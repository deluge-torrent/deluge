# Running tests

Deluge testing is implemented using Trial which is Twisted's testing framework
and an extension of Python's unittest.

See Twisted website for documentation on [Twisted Trial](http://twistedmatrix.com/trac/wiki/TwistedTrial)
and [Writing tests using Trial](http://twistedmatrix.com/documents/current/core/howto/testing.html).

## Testing

The tests are located in the source folder under `deluge/tests`.
The tests are run from the project root directory.
View the unit test coverage at: [deluge-torrent.github.io](http://deluge-torrent.github.io)

### Trial

Here are some examples that show running all the test through to selecting an
individual test.

    trial deluge
    trial deluge.tests.test_client
    trial deluge.tests.test_client.ClientTestCase
    trial deluge.tests.test_client.ClientTestCase.test_connect_localclient

### Pytest

    pytest deluge/tests
    pytest deluge/tests/test_client.py
    pytest deluge/tests/test_client.py -k test_connect_localclient

### Plugin

Running the tests for a specific plugin (requires [pytest](https://pypi.python.org/pypi/pytest)):

    pytest deluge/plugins/<name-of-plugin>

## Tox

All the tests for Deluge can be run using [tox](https://pypi.python.org/pypi/tox)

#### See available targets:

    tox -l
    py27
    py3
    lint
    docs

#### Run specific test:

    tox -e py3

#### Verify code with pre-commit:

    tox -e lint

## Travis-ci

Deluge develop branch is tested automatically by [Travis].
When creating a pull request (PR) on [github], Travis will be automatically run
the unit tests with the code in the PR.

[travis]: https://travis-ci.org/deluge-torrent/deluge
[github]: https://github.com/deluge-torrent/deluge/pulls
