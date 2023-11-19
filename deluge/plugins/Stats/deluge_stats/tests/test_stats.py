#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
import pytest
import pytest_twisted
from twisted.internet import defer

from deluge.common import fsize, fspeed
from deluge.ui.client import client


def print_totals(totals):
    for name, value in totals.items():
        print(name, fsize(value))

    print('overhead:')
    print('up:', fsize(totals['total_upload'] - totals['total_payload_upload']))
    print('down:', fsize(totals['total_download'] - totals['total_payload_download']))


class TestStatsPlugin:
    @pytest_twisted.async_yield_fixture(autouse=True)
    async def set_up(self, component):
        defer.setDebugging(True)
        client.start_standalone()
        client.core.enable_plugin('Stats')
        await component.start()
        yield
        client.stop_standalone()

    @defer.inlineCallbacks
    def test_client_totals(self):
        plugins = yield client.core.get_available_plugins()
        if 'Stats' not in plugins:
            pytest.skip('Stats plugin not available for testing')

        totals = yield client.stats.get_totals()
        assert totals['total_upload'] == 0
        assert totals['total_payload_upload'] == 0
        assert totals['total_payload_download'] == 0
        assert totals['total_download'] == 0
        # print_totals(totals)

    @defer.inlineCallbacks
    def test_session_totals(self):
        plugins = yield client.core.get_available_plugins()
        if 'Stats' not in plugins:
            pytest.skip('Stats plugin not available for testing')

        totals = yield client.stats.get_session_totals()
        assert totals['total_upload'] == 0
        assert totals['total_payload_upload'] == 0
        assert totals['total_payload_download'] == 0
        assert totals['total_download'] == 0
        # print_totals(totals)

    @pytest.mark.gtkui
    @defer.inlineCallbacks
    def test_write(self, tmp_path):
        """
        writing to a file-like object; need this for webui.

        Not strictly a unit test, but tests if calls do not fail...
        """
        from deluge_stats import graph, gtkui

        from deluge.configmanager import ConfigManager
        from deluge.ui.gtk3.gtkui import DEFAULT_PREFS
        from deluge.ui.gtk3.mainwindow import MainWindow
        from deluge.ui.gtk3.pluginmanager import PluginManager
        from deluge.ui.gtk3.preferences import Preferences
        from deluge.ui.gtk3.torrentdetails import TorrentDetails
        from deluge.ui.gtk3.torrentview import TorrentView

        ConfigManager('gtk3ui.conf', defaults=DEFAULT_PREFS)

        self.plugins = PluginManager()
        MainWindow()
        TorrentView()
        TorrentDetails()
        Preferences()

        class FakeFile:
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
        with open(tmp_path / 'file_like.png', 'wb') as _file:
            _file.write(data)
