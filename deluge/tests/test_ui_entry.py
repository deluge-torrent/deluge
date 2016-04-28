# -*- coding: utf-8 -*-
import mock
import pytest

import deluge.component as component
from deluge.ui import ui_entry

from . import common
from .basetest import BaseTestCase


@pytest.mark.gtkui
class UIEntryTestCase(BaseTestCase):

    def set_up(self):
        common.set_tmp_config_dir()
        return component.start()

    def tear_down(self):
        return component.shutdown()

    def test_start_gtkui(self):
        import deluge.ui.gtkui.gtkui
        import sys
        self.patch(sys, "argv", ['./deluge', "--ui", 'gtk'])

        with mock.patch.object(deluge.ui.gtkui.gtkui.GtkUI, 'start', autospec=True):
            ui_entry.start_ui()

    def test_start_console(self):
        import sys
        self.patch(sys, "argv", ['./deluge', "--ui", 'console'])
        with mock.patch('deluge.ui.console.main.ConsoleUI'):
            ui_entry.start_ui()

    def test_start_webserver(self):
        import sys
        from deluge.ui.web.server import DelugeWeb

        self.patch(sys, "argv", ['./deluge', "--ui", 'web', '--do-not-daemonize'])

        class DelugeWebMock(DelugeWeb):
            def __init__(self, *args, **kwargs):
                kwargs["daemon"] = False
                DelugeWeb.__init__(self, *args, **kwargs)

        import deluge.ui.web.server
        self.patch(deluge.ui.web.server, 'DelugeWeb', DelugeWebMock)
        ui_entry.start_ui()
