# -*- coding: utf-8 -*-
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
from __future__ import print_function

from twisted.internet import defer
from twisted.trial import unittest

import deluge.component as component
from deluge.common import fsize
from deluge.tests import common as tests_common
from deluge.tests.basetest import BaseTestCase
from deluge.ui.client import client


def print_totals(totals):
    for name, value in totals.iteritems():
        print(name, fsize(value))

    print("overhead:")
    print("up:", fsize(totals["total_upload"] - totals["total_payload_upload"]))
    print("down:", fsize(totals["total_download"] - totals["total_payload_download"]))


class StatsTestCase(BaseTestCase):

    def set_up(self):
        defer.setDebugging(True)
        tests_common.set_tmp_config_dir()
        client.start_classic_mode()
        client.core.enable_plugin("Stats")
        return component.start()

    def tear_down(self):
        client.stop_classic_mode()
        return component.shutdown()

    @defer.inlineCallbacks
    def test_client_totals(self):
        plugins = yield client.core.get_available_plugins()
        if "Stats" not in plugins:
            raise unittest.SkipTest("WebUi plugin not available for testing")

        totals = yield client.stats.get_totals()
        self.assertEquals(totals['total_upload'], 0)
        self.assertEquals(totals['total_payload_upload'], 0)
        self.assertEquals(totals['total_payload_download'], 0)
        self.assertEquals(totals['total_download'], 0)
        # print_totals(totals)

    @defer.inlineCallbacks
    def test_session_totals(self):
        plugins = yield client.core.get_available_plugins()
        if "Stats" not in plugins:
            raise unittest.SkipTest("WebUi plugin not available for testing")

        totals = yield client.stats.get_session_totals()
        self.assertEquals(totals['total_upload'], 0)
        self.assertEquals(totals['total_payload_upload'], 0)
        self.assertEquals(totals['total_payload_download'], 0)
        self.assertEquals(totals['total_download'], 0)
        # print_totals(totals)
