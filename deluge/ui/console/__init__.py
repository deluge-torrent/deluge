#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from deluge.ui.console.console import Console

UI_PATH = __path__[0]


def start():
    Console().start()


def test_start():
    """Entry point for tests

    A workaround for unit tests which require a deferred object to be
    returned to run properly due to mocking the Twisted reactor.
    """
    return Console().start()
