# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 bendikro <bro.devel+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import print_function

import argparse
import exceptions
import StringIO
import sys

import mock
import pytest
from twisted.internet import defer
from twisted.logger import Logger

import deluge
import deluge.component as component
import deluge.ui.console
import deluge.ui.console.commands.quit
import deluge.ui.console.main
import deluge.ui.web.server
from deluge.ui import ui_entry
from deluge.ui.web.server import DelugeWeb

from . import common
from .basetest import BaseTestCase
from .daemon_base import DaemonBase

log = Logger()

DEBUG_COMMAND = False

sys_stdout = sys.stdout
# To catch output to stdout/stderr while running unit tests, we patch
# the file descriptors in sys and argparse._sys with StringFileDescriptor.
# Regular print statements from such tests will therefore write to the
# StringFileDescriptor object instead of the terminal.
# To print to terminal from the tests, use: print("Message...", file=sys_stdout)


class StringFileDescriptor(object):
    """File descriptor that writes to string buffer"""
    def __init__(self, fd):
        self.out = StringIO.StringIO()
        self.fd = fd
        for a in ["encoding"]:
            setattr(self, a, getattr(sys_stdout, a))

    def write(self, *data, **kwargs):
        print(*data, file=self.out, end="")

    def flush(self):
        self.out.flush()


class UIBaseTestCase(object):

    def __init__(self):
        self.var = dict()

    def set_up(self):
        common.set_tmp_config_dir()
        common.setup_test_logger(level="info", prefix=self.id())
        return component.start()

    def tear_down(self):
        return component.shutdown()

    def exec_command(self):
        if DEBUG_COMMAND:
            print("Executing: '%s'\n" % sys.argv, file=sys_stdout)
        return self.var["start_cmd"]()


class UIWithDaemonBaseTestCase(UIBaseTestCase, DaemonBase):
    """Subclass for test that require a deluged daemon"""

    def __init__(self):
        UIBaseTestCase.__init__(self)

    def set_up(self):
        d = self.common_set_up()
        common.setup_test_logger(level="info", prefix=self.id())
        d.addCallback(self.start_core)
        return d

    def tear_down(self):
        d = UIBaseTestCase.tear_down(self)
        d.addCallback(self.terminate_core)
        return d


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

        fd = StringFileDescriptor(sys.stdout)
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

    def test_start_with_log_level(self):
        _level = []

        def setup_logger(level="error", filename=None, filemode="w", logrotate=None, output_stream=sys.stdout):
            _level.append(level)

        self.patch(deluge.log, "setup_logger", setup_logger)
        self.patch(sys, "argv", ["./deluge", "-L", "info"])

        config = deluge.configmanager.ConfigManager("ui.conf", ui_entry.DEFAULT_PREFS)
        config.config["default_ui"] = "console"
        config.save()

        with mock.patch("deluge.ui.console.main.ConsoleUI"):
            # Just test that no exception is raised
            ui_entry.start_ui()

        self.assertEqual(_level[0], "info")


class GtkUIBaseTestCase(UIBaseTestCase):
    """Implement all GtkUI tests here"""

    def test_start_gtkui(self):
        self.patch(sys, "argv", self.var["sys_arg_cmd"])

        from deluge.ui.gtkui import gtkui
        with mock.patch.object(gtkui.GtkUI, "start", autospec=True):
            self.exec_command()


@pytest.mark.gtkui
class GtkUIDelugeScriptEntryTestCase(BaseTestCase, GtkUIBaseTestCase):

    def __init__(self, testname):
        BaseTestCase.__init__(self, testname)
        GtkUIBaseTestCase.__init__(self)
        self.var["cmd_name"] = "deluge gtk"
        self.var["start_cmd"] = ui_entry.start_ui
        self.var["sys_arg_cmd"] = ["./deluge", "gtk"]

    def set_up(self):
        return GtkUIBaseTestCase.set_up(self)

    def tear_down(self):
        return GtkUIBaseTestCase.tear_down(self)


@pytest.mark.gtkui
class GtkUIScriptEntryTestCase(BaseTestCase, GtkUIBaseTestCase):

    def __init__(self, testname):
        BaseTestCase.__init__(self, testname)
        GtkUIBaseTestCase.__init__(self)
        from deluge.ui import gtkui
        self.var["cmd_name"] = "deluge-gtk"
        self.var["start_cmd"] = gtkui.start
        self.var["sys_arg_cmd"] = ["./deluge-gtk"]

    def set_up(self):
        return GtkUIBaseTestCase.set_up(self)

    def tear_down(self):
        return GtkUIBaseTestCase.tear_down(self)


class DelugeWebMock(DelugeWeb):
    def __init__(self, *args, **kwargs):
        kwargs["daemon"] = False
        DelugeWeb.__init__(self, *args, **kwargs)


class WebUIBaseTestCase(UIBaseTestCase):
    """Implement all WebUI tests here"""

    def test_start_webserver(self):
        self.patch(sys, "argv", self.var["sys_arg_cmd"])
        self.patch(deluge.ui.web.server, "DelugeWeb", DelugeWebMock)
        self.exec_command()

    def test_start_web_with_log_level(self):
        _level = []

        def setup_logger(level="error", filename=None, filemode="w", logrotate=None, output_stream=sys.stdout):
            _level.append(level)

        self.patch(deluge.log, "setup_logger", setup_logger)
        self.patch(sys, "argv", self.var["sys_arg_cmd"] + ["-L", "info"])

        config = deluge.configmanager.ConfigManager("ui.conf", ui_entry.DEFAULT_PREFS)
        config.config["default_ui"] = "web"
        config.save()

        self.patch(deluge.ui.web.server, "DelugeWeb", DelugeWebMock)
        self.exec_command()
        self.assertEqual(_level[0], "info")


class WebUIScriptEntryTestCase(BaseTestCase, WebUIBaseTestCase):

    def __init__(self, testname):
        BaseTestCase.__init__(self, testname)
        WebUIBaseTestCase.__init__(self)
        self.var["cmd_name"] = "deluge-web"
        self.var["start_cmd"] = deluge.ui.web.start
        self.var["sys_arg_cmd"] = ["./deluge-web", "--do-not-daemonize"]

    def set_up(self):
        return WebUIBaseTestCase.set_up(self)

    def tear_down(self):
        return WebUIBaseTestCase.tear_down(self)


class WebUIDelugeScriptEntryTestCase(BaseTestCase, WebUIBaseTestCase):

    def __init__(self, testname):
        BaseTestCase.__init__(self, testname)
        WebUIBaseTestCase.__init__(self)
        self.var["cmd_name"] = "deluge web"
        self.var["start_cmd"] = ui_entry.start_ui
        self.var["sys_arg_cmd"] = ["./deluge", "web", "--do-not-daemonize"]

    def set_up(self):
        return WebUIBaseTestCase.set_up(self)

    def tear_down(self):
        return WebUIBaseTestCase.tear_down(self)


class ConsoleUIBaseTestCase(UIBaseTestCase):
    """Implement Console tests that do not require a running daemon"""

    def test_start_console(self):
        self.patch(sys, "argv", self.var["sys_arg_cmd"])
        with mock.patch("deluge.ui.console.main.ConsoleUI"):
            self.exec_command()

    def test_start_console_with_log_level(self):
        _level = []

        def setup_logger(level="error", filename=None, filemode="w", logrotate=None, output_stream=sys.stdout):
            _level.append(level)

        self.patch(deluge.log, "setup_logger", setup_logger)
        self.patch(sys, "argv", self.var["sys_arg_cmd"] + ["-L", "info"])

        config = deluge.configmanager.ConfigManager("ui.conf", ui_entry.DEFAULT_PREFS)
        config.config["default_ui"] = "console"
        config.save()

        with mock.patch("deluge.ui.console.main.ConsoleUI"):
            # Just test that no exception is raised
            self.exec_command()

        self.assertEqual(_level[0], "info")

    def test_console_help(self):
        self.patch(sys, "argv", self.var["sys_arg_cmd"] + ["-h"])
        fd = StringFileDescriptor(sys.stdout)
        self.patch(argparse._sys, "stdout", fd)

        with mock.patch("deluge.ui.console.main.ConsoleUI"):
            self.assertRaises(exceptions.SystemExit, self.exec_command)
            std_output = fd.out.getvalue()
            self.assertTrue(("usage: %s" % self.var["cmd_name"]) in std_output)  # Check command name
            self.assertTrue("Common Options:" in std_output)
            self.assertTrue("Console Options:" in std_output)
            self.assertTrue("Console commands:\n  The following console commands are available:" in std_output)
            self.assertTrue("The following console commands are available:" in std_output)

    def test_console_command_info(self):
        self.patch(sys, "argv", self.var["sys_arg_cmd"] + ["info"])
        fd = StringFileDescriptor(sys.stdout)
        self.patch(argparse._sys, "stdout", fd)

        with mock.patch("deluge.ui.console.main.ConsoleUI"):
            self.exec_command()

    def test_console_command_info_help(self):
        self.patch(sys, "argv", self.var["sys_arg_cmd"] + ["info", "-h"])
        fd = StringFileDescriptor(sys.stdout)
        self.patch(argparse._sys, "stdout", fd)

        with mock.patch("deluge.ui.console.main.ConsoleUI"):
            self.assertRaises(exceptions.SystemExit, self.exec_command)
            std_output = fd.out.getvalue()
            self.assertTrue("usage: info" in std_output)
            self.assertTrue("Show information about the torrents" in std_output)

    def test_console_unrecognized_arguments(self):
        self.patch(sys, "argv", ["./deluge", "--ui", "console"])  # --ui is not longer supported
        fd = StringFileDescriptor(sys.stdout)
        self.patch(argparse._sys, "stderr", fd)
        with mock.patch("deluge.ui.console.main.ConsoleUI"):
            self.assertRaises(exceptions.SystemExit, self.exec_command)
            self.assertTrue("unrecognized arguments: --ui" in fd.out.getvalue())


class ConsoleUIWithDaemonBaseTestCase(UIWithDaemonBaseTestCase):
    """Implement Console tests that require a running daemon"""

    def set_up(self):
        # Avoid calling reactor.shutdown after commands are executed by main.exec_args()
        self.patch(deluge.ui.console.commands.quit, "reactor", common.ReactorOverride())
        return UIWithDaemonBaseTestCase.set_up(self)

    @defer.inlineCallbacks
    def test_console_command_status(self):
        username, password = deluge.ui.common.get_localhost_auth()
        self.patch(sys, "argv", self.var["sys_arg_cmd"] + ["--port"] + ["58900"] + ["--username"] +
                   [username] + ["--password"] + [password] + ["status"])
        fd = StringFileDescriptor(sys.stdout)
        self.patch(sys, "stdout", fd)
        self.patch(deluge.ui.console.main, "reactor", common.ReactorOverride())

        yield self.exec_command()

        std_output = fd.out.getvalue()
        status_output = """Total upload: 0.0 KiB/s
Total download: 0.0 KiB/s
DHT Nodes: 0
Total torrents: 0
 Allocating: 0
 Checking: 0
 Downloading: 0
 Seeding: 0
 Paused: 0
 Error: 0
 Queued: 0
 Moving: 0
"""
        self.assertEqual(std_output, status_output)


class ConsoleScriptEntryWithDaemonTestCase(BaseTestCase, ConsoleUIWithDaemonBaseTestCase):

    def __init__(self, testname):
        BaseTestCase.__init__(self, testname)
        ConsoleUIWithDaemonBaseTestCase.__init__(self)
        self.var["cmd_name"] = "deluge-console"
        self.var["sys_arg_cmd"] = ["./deluge-console"]

    def set_up(self):
        from deluge.ui.console.console import Console

        def start_console():
            return Console().start()

        self.patch(deluge.ui.console, "start", start_console)
        self.var["start_cmd"] = deluge.ui.console.start

        return ConsoleUIWithDaemonBaseTestCase.set_up(self)

    def tear_down(self):
        return ConsoleUIWithDaemonBaseTestCase.tear_down(self)


class ConsoleScriptEntryTestCase(BaseTestCase, ConsoleUIBaseTestCase):

    def __init__(self, testname):
        BaseTestCase.__init__(self, testname)
        ConsoleUIBaseTestCase.__init__(self)
        self.var["cmd_name"] = "deluge-console"
        self.var["start_cmd"] = deluge.ui.console.start
        self.var["sys_arg_cmd"] = ["./deluge-console"]

    def set_up(self):
        return ConsoleUIBaseTestCase.set_up(self)

    def tear_down(self):
        return ConsoleUIBaseTestCase.tear_down(self)


class ConsoleDelugeScriptEntryTestCase(BaseTestCase, ConsoleUIBaseTestCase):

    def __init__(self, testname):
        BaseTestCase.__init__(self, testname)
        ConsoleUIBaseTestCase.__init__(self)
        self.var["cmd_name"] = "deluge console"
        self.var["start_cmd"] = ui_entry.start_ui
        self.var["sys_arg_cmd"] = ["./deluge", "console"]

    def set_up(self):
        return ConsoleUIBaseTestCase.set_up(self)

    def tear_down(self):
        return ConsoleUIBaseTestCase.tear_down(self)
