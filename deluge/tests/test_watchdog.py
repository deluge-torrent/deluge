#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

"""Tests for the add_watchdog helper in deluge.tests.common."""

import pytest
import pytest_twisted
from twisted.internet import defer, reactor

from . import common


@pytest_twisted.inlineCallbacks
def test_watchdog_cancels_a_deferred_that_never_fires():
    d = defer.Deferred()
    common.add_watchdog(d, timeout=0.05)
    # Bound the wait so a broken watchdog fails the test rather than hanging it.
    d.addTimeout(2, reactor)

    with pytest.raises(defer.CancelledError):
        yield d


@pytest_twisted.inlineCallbacks
def test_watchdog_prints_its_message_on_timeout(capsys):
    d = defer.Deferred()
    common.add_watchdog(d, timeout=0.05, message='Timeout!')
    d.addTimeout(2, reactor)

    with pytest.raises(defer.CancelledError):
        yield d

    assert 'Timeout!' in capsys.readouterr().out


def test_watchdog_is_cancelled_when_the_deferred_fires():
    d = defer.Deferred()
    watchdog = common.add_watchdog(d, timeout=30)

    d.callback('done')

    assert watchdog.cancelled, 'a fired deferred must not leave a pending watchdog'
