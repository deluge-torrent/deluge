import pytest
import twisted.internet.defer as defer
from twisted.trial import unittest

import deluge.component as component
from deluge.common import fsize
from deluge.tests import common as tests_common
from deluge.ui.client import client


def print_totals(totals):
    for name, value in totals.iteritems():
        print(name, fsize(value))

    print("overhead:")
    print("up:", fsize(totals["total_upload"] - totals["total_payload_upload"]))
    print("down:", fsize(totals["total_download"] - totals["total_payload_download"]))


class StatsTestCase(unittest.TestCase):

    def setUp(self):  # NOQA
        defer.setDebugging(True)
        tests_common.set_tmp_config_dir()
        client.start_classic_mode()
        client.core.enable_plugin("Stats")

    def tearDown(self):  # NOQA
        client.stop_classic_mode()

        def on_shutdown(result):
            component._ComponentRegistry.components = {}
        return component.shutdown().addCallback(on_shutdown)

    @pytest.mark.todo
    def test_client_totals(self):
        StatsTestCase.test_client_totals.im_func.todo = "To be fixed"

        def callback(args):
            print_totals(args)
        d = client.stats.get_totals()
        d.addCallback(callback)

    @pytest.mark.todo
    def test_session_totals(self):
        StatsTestCase.test_session_totals.im_func.todo = "To be fixed"

        def callback(args):
            print_totals(args)
        d = client.stats.get_session_totals()
        d.addCallback(callback)
