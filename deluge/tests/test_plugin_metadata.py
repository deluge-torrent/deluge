#
# Copyright (C) 2015 Calum Lind <calumlind@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from deluge.pluginmanagerbase import PluginManagerBase


class TestPluginManagerBase:
    def test_get_plugin_info(self):
        pm = PluginManagerBase('core.conf', 'deluge.plugin.core')
        for p in pm.get_available_plugins():
            for key, value in pm.get_plugin_info(p).items():
                assert isinstance(key, str)
                assert isinstance(value, str)

    def test_get_plugin_info_invalid_name(self):
        pm = PluginManagerBase('core.conf', 'deluge.plugin.core')
        for key, value in pm.get_plugin_info('random').items():
            result = 'not available' if key in ('Name', 'Version') else ''
            assert value == result

    def test_parse_pkg_info_metadata_2_1(self):
        pkg_info = """Metadata-Version: 2.1
Name: AutoAdd
Version: 1.8
Summary: Monitors folders for .torrent files.
Home-page: http://dev.deluge-torrent.org/wiki/Plugins/AutoAdd
Author: Chase Sterling, Pedro Algarvio
Author-email: chase.sterling@gmail.com, pedro@algarvio.me
License: GPLv3
Platform: UNKNOWN

Monitors folders for .torrent files.
        """
        plugin_info = PluginManagerBase.parse_pkg_info(pkg_info)
        for value in plugin_info.values():
            assert value != ''
        result = 'Monitors folders for .torrent files.'
        assert plugin_info['Description'] == result
