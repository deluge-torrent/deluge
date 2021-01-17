# -*- coding: utf-8 -*-
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
from __future__ import print_function, unicode_literals

import pytest
from twisted.internet import defer
from twisted.trial import unittest

import deluge.component as component
from deluge.common import fsize, fspeed
from deluge.tests import common as tests_common
from deluge.tests.basetest import BaseTestCase
from deluge.ui.client import client


def print_totals(totals):
    for name, value in totals.items():
        print(name, fsize(value))

    print('overhead:')
    print('up:', fsize(totals['total_upload'] - totals['total_payload_upload']))
    print('down:', fsize(totals['total_download'] - totals['total_payload_download']))


class StatsTestCase(BaseTestCase):
    def set_up(self):
        defer.setDebugging(True)
        tests_common.set_tmp_config_dir()
        client.start_standalone()
        client.core.enable_plugin('Stats')
        return component.start()

    def tear_down(self):
        client.stop_standalone()
        return component.shutdown()

    @defer.inlineCallbacks
    def test_client_totals(self):
        plugins = yield client.core.get_available_plugins()
        if 'Stats' not in plugins:
            raise unittest.SkipTest('WebUi plugin not available for testing')

        totals = yield client.stats.get_totals()
        self.assertEqual(totals['total_upload'], 0)
        self.assertEqual(totals['total_payload_upload'], 0)
        self.assertEqual(totals['total_payload_download'], 0)
        self.assertEqual(totals['total_download'], 0)
        # print_totals(totals)

    @defer.inlineCallbacks
    def test_session_totals(self):
        plugins = yield client.core.get_available_plugins()
        if 'Stats' not in plugins:
            raise unittest.SkipTest('WebUi plugin not available for testing')

        totals = yield client.stats.get_session_totals()
        self.assertEqual(totals['total_upload'], 0)
        self.assertEqual(totals['total_payload_upload'], 0)
        self.assertEqual(totals['total_payload_download'], 0)
        self.assertEqual(totals['total_download'], 0)
        # print_totals(totals)

    @pytest.mark.gtkui
    @defer.inlineCallbacks
    def test_write(self):
        """
        writing to a file-like object; need this for webui.

        Not strictly a unit test, but tests if calls do not fail...
        """
        from deluge_stats import graph, gtkui

        from deluge.configmanager import ConfigManager
        from deluge.ui.gtkui.gtkui import DEFAULT_PREFS
        from deluge.ui.gtkui.mainwindow import MainWindow
        from deluge.ui.gtkui.pluginmanager import PluginManager
        from deluge.ui.gtkui.preferences import Preferences
        from deluge.ui.gtkui.torrentdetails import TorrentDetails
        from deluge.ui.gtkui.torrentview import TorrentView

        ConfigManager('gtkui.conf', defaults=DEFAULT_PREFS)

        self.plugins = PluginManager()
        MainWindow()
        TorrentView()
        TorrentDetails()
        Preferences()

        class FakeFile(object):
            def __init__(self):
                self.data = []

            def write(self, data):
                self.data.append(data)

        stats_gtkui = gtkui.GtkUI('test_stats')
        stats_gtkui.enable()
        yield stats_gtkui.graphs_tab.update()

        g = stats_gtkui.graphs_tab.graph
        g.add_stat('download_rate', color=graph.green)
        g.add_stat('upload_rate', color=graph.blue)
        g.set_left_axis(formatter=fspeed, min=10240)

        surface = g.draw(900, 150)
        file_like = FakeFile()
        surface.write_to_png(file_like)
        data = b''.join(file_like.data)
        with open('file_like.png', 'wb') as _file:
            _file.write(data)
