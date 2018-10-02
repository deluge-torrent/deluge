# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Calum Lind <calumlind@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

from deluge.pluginmanagerbase import PluginManagerBase

from . import common
from .basetest import BaseTestCase


class PluginManagerBaseTestCase(BaseTestCase):
    def set_up(self):
        common.set_tmp_config_dir()

    def test_get_plugin_info(self):
        pm = PluginManagerBase('core.conf', 'deluge.plugin.core')
        for p in pm.get_available_plugins():
            for key, value in pm.get_plugin_info(p).items():
                self.assertTrue(isinstance('%s: %s' % (key, value), ''.__class__))

    def test_get_plugin_info_invalid_name(self):
        pm = PluginManagerBase('core.conf', 'deluge.plugin.core')
        for key, value in pm.get_plugin_info('random').items():
            self.assertEqual(value, 'not available')
