#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
import pytest
import pytest_twisted
import twisted.python.failure
from twisted.internet import defer, reactor, task
from twisted.internet.defer import maybeDeferred

from deluge.decorators import maybe_coroutine


@defer.inlineCallbacks
def inline_func():
    result = yield task.deferLater(reactor, 0, lambda: 'function_result')
    return result


@defer.inlineCallbacks
def inline_error():
    raise Exception('function_error')
    yield


@maybe_coroutine
async def coro_func():
    result = await task.deferLater(reactor, 0, lambda: 'function_result')
    return result


@maybe_coroutine
async def coro_error():
    raise Exception('function_error')


@defer.inlineCallbacks
def coro_func_from_inline():
    result = yield coro_func()
    return result


@defer.inlineCallbacks
def coro_error_from_inline():
    result = yield coro_error()
    return result


@maybe_coroutine
async def coro_func_from_coro():
    return await coro_func()


@maybe_coroutine
async def coro_error_from_coro():
    return await coro_error()


@maybe_coroutine
async def inline_func_from_coro():
    return await inline_func()


@maybe_coroutine
async def inline_error_from_coro():
    return await inline_error()


@pytest_twisted.inlineCallbacks
def test_standard_twisted():
    """Sanity check that twisted tests work how we expect.

    Not really testing deluge code at all.
    """
    result = yield inline_func()
    assert result == 'function_result'

    with pytest.raises(Exception, match='function_error'):
        yield inline_error()


@pytest.mark.parametrize(
    'function',
    [
        inline_func,
        coro_func,
        coro_func_from_coro,
        coro_func_from_inline,
        inline_func_from_coro,
    ],
)
@pytest_twisted.inlineCallbacks
def test_from_inline(function):
    """Test our coroutines wrapped with maybe_coroutine as if they returned plain twisted deferreds."""
    result = yield function()
    assert result == 'function_result'

    def cb(result):
        assert result == 'function_result'

    d = function()
    d.addCallback(cb)
    yield d


@pytest.mark.parametrize(
    'function',
    [
        inline_error,
        coro_error,
        coro_error_from_coro,
        coro_error_from_inline,
        inline_error_from_coro,
    ],
)
@pytest_twisted.inlineCallbacks
def test_error_from_inline(function):
    """Test our coroutines wrapped with maybe_coroutine as if they returned plain twisted deferreds that raise."""
    with pytest.raises(Exception, match='function_error'):
        yield function()

    def eb(result):
        assert isinstance(result, twisted.python.failure.Failure)
        assert result.getErrorMessage() == 'function_error'

    d = function()
    d.addErrback(eb)
    yield d


@pytest.mark.parametrize(
    'function',
    [
        inline_func,
        coro_func,
        coro_func_from_coro,
        coro_func_from_inline,
        inline_func_from_coro,
    ],
)
async def test_from_coro(function):
    """Test our coroutines wrapped with maybe_coroutine work from another coroutine."""
    result = await function()
    assert result == 'function_result'


@pytest.mark.parametrize(
    'function',
    [
        inline_error,
        coro_error,
        coro_error_from_coro,
        coro_error_from_inline,
        inline_error_from_coro,
    ],
)
async def test_error_from_coro(function):
    """Test our coroutines wrapped with maybe_coroutine work from another coroutine with errors."""
    with pytest.raises(Exception, match='function_error'):
        await function()


async def test_tracebacks_preserved():
    with pytest.raises(Exception) as exc:
        await coro_error_from_coro()
    traceback_lines = [
        'await coro_error_from_coro()',
        'return await coro_error()',
        "raise Exception('function_error')",
    ]
    # If each coroutine got wrapped with ensureDeferred, the traceback will be mangled
    # verify the coroutines passed through by checking the traceback.
    for expected, actual in zip(traceback_lines, exc.traceback):
        assert expected in str(actual)


async def test_maybe_deferred_coroutine():
    result = await maybeDeferred(coro_func)
    assert result == 'function_result'


async def test_callback_before_await():
    def cb(res):
        assert res == 'function_result'
        return res

    d = coro_func()
    d.addCallback(cb)
    result = await d
    assert result == 'function_result'


async def test_callback_after_await():
    """If it has already been used as a coroutine, can't be retroactively turned into a Deferred.
    This limitation could be fixed, but the extra complication doesn't feel worth it.
    """

    def cb(res):
        pass

    d = coro_func()
    await d
    with pytest.raises(
        Exception, match='Cannot add callbacks to an already awaited coroutine'
    ):
        d.addCallback(cb)
