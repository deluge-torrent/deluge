# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Calum Lind <calumlind@gmail.com>
# Copyright (C) 2010 Pedro Algarvio <ufs@ufsoft.org>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging
import warnings

from deluge.log import setup_logger

from .basetest import BaseTestCase


class LogTestCase(BaseTestCase):
    def set_up(self):
        setup_logger(logging.DEBUG)

    def tear_down(self):
        setup_logger('none')

    def test_old_log_deprecation_warning(self):
        from deluge.log import LOG

        with warnings.catch_warnings(record=True) as w:
            # Cause all warnings to always be triggered.
            warnings.simplefilter('always')
            LOG.debug('foo')
            self.assertEqual(w[-1].category, DeprecationWarning)

    # def test_twisted_error_log(self):
    #    from twisted.internet import defer
    #    import deluge.component as component
    #    from deluge.core.eventmanager import EventManager
    #    EventManager()
    #
    #    d = component.start()
    #
    #    @defer.inlineCallbacks
    #    def call(*args):
    #        yield component.pause(["EventManager"])
    #        yield component.start(["EventManager"])
    #
    #    d.addCallback(call)
    #    return d
