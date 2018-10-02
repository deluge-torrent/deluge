# -*- coding: utf-8 -*-
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import deluge.component as component
from deluge.core.core import Core

from .basetest import BaseTestCase


class AlertManagerTestCase(BaseTestCase):
    def set_up(self):
        self.core = Core()
        self.core.config.config['lsd'] = False
        self.am = component.get('AlertManager')
        return component.start(['AlertManager'])

    def tear_down(self):
        return component.shutdown()

    def test_register_handler(self):
        def handler(alert):
            return

        self.am.register_handler('dummy_alert', handler)
        self.assertEqual(self.am.handlers['dummy_alert'], [handler])

    def test_deregister_handler(self):
        def handler(alert):
            return

        self.am.register_handler('dummy_alert', handler)
        self.am.deregister_handler(handler)
        self.assertEqual(self.am.handlers['dummy_alert'], [])
