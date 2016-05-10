# -*- coding: utf-8 -*-
from __future__ import print_function

import argparse
import exceptions
import StringIO
import sys

import mock
import pytest

import deluge.component as component
import deluge.ui.console
import deluge.ui.web.server
from deluge.ui import ui_entry
from deluge.ui.web.server import DelugeWeb

from . import common
from .basetest import BaseTestCase

sys_stdout = sys.stdout


class TestStdout(object):

    def __init__(self, fd):
        self.out = StringIO.StringIO()
        self.fd = fd
        for a in ["encoding"]:
            setattr(self, a, getattr(sys_stdout, a))

    def write(self, *data, **kwargs):
        print(data, file=self.out)

    def flush(self):
        self.out.flush()


class DelugeEntryTestCase(BaseTestCase):

    def set_up(self):
        common.set_tmp_config_dir()
        return component.start()

    def tear_down(self):
        return component.shutdown()

    def test_deluge_help(self):
        self.patch(sys, "argv", ["./deluge", "-h"])
        config = deluge.configmanager.ConfigManager("ui.conf", ui_entry.DEFAULT_PREFS)
        config.config["default_ui"] = "console"
        config.save()

        fd = TestStdout(sys.stdout)
        self.patch(argparse._sys, "stdout", fd)

        with mock.patch("deluge.ui.console.main.ConsoleUI"):
            self.assertRaises(exceptions.SystemExit, ui_entry.start_ui)
            self.assertTrue("usage: deluge" in fd.out.getvalue())
            self.assertTrue("UI Options:" in fd.out.getvalue())
            self.assertTrue("* console" in fd.out.getvalue())

    def test_start_default(self):
        self.patch(sys, "argv", ["./deluge"])
        config = deluge.configmanager.ConfigManager("ui.conf", ui_entry.DEFAULT_PREFS)
        config.config["default_ui"] = "console"
        config.save()

        with mock.patch("deluge.ui.console.main.ConsoleUI"):
            # Just test that no exception is raised
            ui_entry.start_ui()


@pytest.mark.gtkui
class GtkUIEntryTestCase(BaseTestCase):

    def set_up(self):
        common.set_tmp_config_dir()
        return component.start()

    def tear_down(self):
        return component.shutdown()

    def test_start_gtkui(self):
        self.patch(sys, "argv", ["./deluge", "gtk"])

        from deluge.ui.gtkui import gtkui
        with mock.patch.object(gtkui.GtkUI, "start", autospec=True):
            ui_entry.start_ui()


class WebUIEntryTestCase(BaseTestCase):

    def set_up(self):
        common.set_tmp_config_dir()
        return component.start()

    def tear_down(self):
        return component.shutdown()

    def test_start_webserver(self):
        self.patch(sys, "argv", ["./deluge", "web", "--do-not-daemonize"])

        class DelugeWebMock(DelugeWeb):
            def __init__(self, *args, **kwargs):
                kwargs["daemon"] = False
                DelugeWeb.__init__(self, *args, **kwargs)

        self.patch(deluge.ui.web.server, "DelugeWeb", DelugeWebMock)
        ui_entry.start_ui()


class ConsoleUIBaseTestCase(object):

    def __init__(self):
        self.var = dict()

    def set_up(self):
        common.set_tmp_config_dir()
        return component.start()

    def tear_down(self):
        return component.shutdown()

    def test_start_console(self):
        self.patch(sys, "argv", self.var["sys_arg_cmd"])
        with mock.patch("deluge.ui.console.main.ConsoleUI"):
            self.var["start_cmd"]()

    def test_console_help(self):
        self.patch(sys, "argv", self.var["sys_arg_cmd"] + ["-h"])
        fd = TestStdout(sys.stdout)
        self.patch(argparse._sys, "stdout", fd)

        with mock.patch("deluge.ui.console.main.ConsoleUI"):
            self.assertRaises(exceptions.SystemExit, self.var["start_cmd"])
            std_output = fd.out.getvalue()
            self.assertTrue(("usage: %s" % self.var["cmd_name"]) in std_output)  # Check command name
            self.assertTrue("Common Options:" in std_output)
            self.assertTrue("Console Options:" in std_output)
            self.assertTrue(r"Console commands:\n  The following console commands are available:" in std_output)
            self.assertTrue("The following console commands are available:" in std_output)

    def test_console_command_info(self):
        self.patch(sys, "argv", self.var["sys_arg_cmd"] + ["info"])
        fd = TestStdout(sys.stdout)
        self.patch(argparse._sys, "stdout", fd)

        with mock.patch("deluge.ui.console.main.ConsoleUI"):
            self.var["start_cmd"]()

    def test_console_command_info_help(self):
        self.patch(sys, "argv", self.var["sys_arg_cmd"] + ["info", "-h"])
        fd = TestStdout(sys.stdout)
        self.patch(argparse._sys, "stdout", fd)

        with mock.patch("deluge.ui.console.main.ConsoleUI"):
            self.assertRaises(exceptions.SystemExit, self.var["start_cmd"])
            std_output = fd.out.getvalue()
            self.assertTrue("usage: info" in std_output)
            self.assertTrue("Show information about the torrents" in std_output)

    def test_console_unrecognized_arguments(self):
        self.patch(sys, "argv", ["./deluge", "--ui", "console"])  # --ui is not longer supported
        fd = TestStdout(sys.stdout)
        self.patch(argparse._sys, "stderr", fd)
        with mock.patch("deluge.ui.console.main.ConsoleUI"):
            self.assertRaises(exceptions.SystemExit, self.var["start_cmd"])
            self.assertTrue("unrecognized arguments: --ui" in fd.out.getvalue())


class ConsoleUIEntryTestCase(BaseTestCase, ConsoleUIBaseTestCase):

    def __init__(self, testname):
        BaseTestCase.__init__(self, testname)
        ConsoleUIBaseTestCase.__init__(self)
        self.var["cmd_name"] = "deluge console"
        self.var["start_cmd"] = ui_entry.start_ui
        self.var["sys_arg_cmd"] = ["./deluge", "console"]


class ConsoleUIScriptTestCase(BaseTestCase, ConsoleUIBaseTestCase):

    def __init__(self, testname):
        BaseTestCase.__init__(self, testname)
        ConsoleUIBaseTestCase.__init__(self)
        self.var["cmd_name"] = "deluge-console"
        self.var["start_cmd"] = deluge.ui.console.start
        self.var["sys_arg_cmd"] = ["./deluge-console"]
