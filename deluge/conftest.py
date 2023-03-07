#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
import asyncio
import tempfile
import warnings
from unittest.mock import Mock, patch

import pytest
import pytest_twisted
from twisted.internet import reactor
from twisted.internet.defer import Deferred, maybeDeferred
from twisted.internet.error import CannotListenError
from twisted.python.failure import Failure

import deluge.component as _component
import deluge.configmanager
from deluge.common import get_localhost_auth
from deluge.tests import common
from deluge.ui.client import client as _client

DEFAULT_LISTEN_PORT = 58900


@pytest.fixture
def listen_port(request):
    if request and 'daemon' in request.fixturenames:
        try:
            return request.getfixturevalue('daemon').listen_port
        except Exception:
            pass
    return DEFAULT_LISTEN_PORT


@pytest.fixture
def mock_callback():
    """Returns a `Mock` object which can be registered as a callback to test against.

    If callback was not called within `timeout` seconds, it will raise a TimeoutError.
    The returned Mock instance will have a `deferred` attribute which will complete when the callback has been called.
    """

    def reset():
        if mock.called:
            original_reset_mock()
        deferred = Deferred()
        deferred.addTimeout(0.5, reactor)
        mock.side_effect = lambda *args, **kw: deferred.callback((args, kw))
        mock.deferred = deferred

    mock = Mock()
    original_reset_mock = mock.reset_mock
    mock.reset_mock = reset
    mock.reset_mock()
    return mock


@pytest.fixture
def config_dir(tmp_path):
    config_dir = tmp_path / 'config'
    deluge.configmanager.set_config_dir(config_dir)
    yield config_dir


@pytest_twisted.async_yield_fixture()
async def client(request, config_dir, monkeypatch, listen_port):
    # monkeypatch.setattr(
    #     _client, 'connect', functools.partial(_client.connect, port=listen_port)
    # )
    try:
        username, password = get_localhost_auth()
    except Exception:
        username, password = '', ''
    await _client.connect(
        'localhost',
        port=listen_port,
        username=username,
        password=password,
    )
    yield _client
    if _client.connected():
        await _client.disconnect()


@pytest_twisted.async_yield_fixture
async def daemon(request, config_dir, tmp_path):
    listen_port = DEFAULT_LISTEN_PORT
    logfile = tmp_path / 'daemon.log'

    if hasattr(request.cls, 'daemon_custom_script'):
        custom_script = request.cls.daemon_custom_script
    else:
        custom_script = ''

    for dummy in range(10):
        try:
            d, daemon = common.start_core(
                listen_port=listen_port,
                logfile=logfile,
                timeout=5,
                timeout_msg='Timeout!',
                custom_script=custom_script,
                print_stdout=True,
                print_stderr=True,
                config_directory=config_dir,
            )
            await d
        except CannotListenError as ex:
            exception_error = ex
            listen_port += 1
        except (KeyboardInterrupt, SystemExit):
            raise
        else:
            break
    else:
        raise exception_error
    daemon.listen_port = listen_port
    yield daemon
    await daemon.kill()


@pytest.fixture(autouse=True)
def common_fixture(config_dir, request, monkeypatch, listen_port):
    """Adds some instance attributes to test classes for backwards compatibility with old testing."""

    def fail(self, reason):
        if isinstance(reason, Failure):
            reason = reason.value
        return pytest.fail(str(reason))

    if request.instance:
        request.instance.patch = monkeypatch.setattr
        request.instance.config_dir = config_dir
        request.instance.listen_port = listen_port
        request.instance.id = lambda: request.node.name
        request.cls.fail = fail


@pytest_twisted.async_yield_fixture(scope='function')
async def component():
    """Verify component registry is clean, and clean up after test."""
    if len(_component._ComponentRegistry.components) != 0:
        warnings.warn(
            'The component._ComponentRegistry.components is not empty on test setup.\n'
            'This is probably caused by another test that did not clean up after finishing!: %s'
            % _component._ComponentRegistry.components
        )

    yield _component

    await _component.shutdown()
    _component._ComponentRegistry.components.clear()
    _component._ComponentRegistry.dependents.clear()


@pytest_twisted.async_yield_fixture(scope='function')
async def base_fixture(common_fixture, component, request):
    """This fixture is autoused on all tests that subclass BaseTestCase"""
    self = request.instance

    if hasattr(self, 'set_up'):
        try:
            await maybeDeferred(self.set_up)
        except Exception as exc:
            warnings.warn('Error caught in test setup!\n%s' % exc)
            pytest.fail('Error caught in test setup!\n%s' % exc)

    yield

    if hasattr(self, 'tear_down'):
        try:
            await maybeDeferred(self.tear_down)
        except Exception as exc:
            pytest.fail('Error caught in test teardown!\n%s' % exc)


@pytest.mark.usefixtures('base_fixture')
class BaseTestCase:
    """This is the base class that should be used for all test classes
    that create classes that inherit from deluge.component.Component. It
    ensures that the component registry has been cleaned up when tests
    have finished.

    """


@pytest.fixture
def mock_mkstemp(tmp_path):
    """Return known tempfile location to verify file deleted"""
    tmp_file = tempfile.mkstemp(dir=tmp_path)
    with patch('tempfile.mkstemp', return_value=tmp_file):
        yield tmp_file


def pytest_collection_modifyitems(session, config, items) -> None:
    """
    Automatically runs async tests with pytest_twisted.ensureDeferred
    """
    function_items = (item for item in items if isinstance(item, pytest.Function))
    for function_item in function_items:
        function = function_item.obj
        if hasattr(function, '__func__'):
            # methods need to be unwrapped.
            function = function.__func__
        if asyncio.iscoroutinefunction(function):
            # This is how pytest_twisted marks ensureDeferred tests
            setattr(function, '_pytest_twisted_mark', 'async_test')
