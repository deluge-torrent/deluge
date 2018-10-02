# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 bendikro <bro.devel+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

from twisted.trial import unittest

import deluge.component as component
from deluge.core.core import Core
from deluge.core.rpcserver import RPCServer
from deluge.tests import common
from deluge.tests.basetest import BaseTestCase

common.disable_new_release_check()


class WebUIPluginTestCase(BaseTestCase):
    def set_up(self):
        common.set_tmp_config_dir()
        self.rpcserver = RPCServer(listen=False)
        self.core = Core()
        return component.start()

    def tear_down(self):
        def on_shutdown(result):
            del self.rpcserver
            del self.core

        return component.shutdown().addCallback(on_shutdown)

    def test_enable_webui(self):
        if 'WebUi' not in self.core.get_available_plugins():
            raise unittest.SkipTest('WebUi plugin not available for testing')

        d = self.core.enable_plugin('WebUi')

        def result_cb(result):
            if 'WebUi' not in self.core.get_enabled_plugins():
                self.fail('Failed to enable WebUi plugin')
            self.assertTrue(result)

        d.addBoth(result_cb)
        return d
