#
# Copyright (C) 2016 bendikro <bro.devel+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import argparse
import sys
from io import StringIO
from unittest import mock

import pytest
import pytest_twisted
from twisted.internet import defer

import deluge
import deluge.component as component
import deluge.ui.console
import deluge.ui.console.cmdline.commands.quit
import deluge.ui.console.main
import deluge.ui.web.server
from deluge.common import get_localhost_auth, windows_check
from deluge.conftest import BaseTestCase
from deluge.ui import ui_entry
from deluge.ui.web.server import DelugeWeb

from . import common
from .daemon_base import DaemonBase

DEBUG_COMMAND = False

sys_stdout = sys.stdout
# To catch output to stdout/stderr while running unit tests, we patch
# the file descriptors in sys and argparse._sys with StringFileDescriptor.
# Regular print statements from such tests will therefore write to the
# StringFileDescriptor object instead of the terminal.
# To print to terminal from the tests, use: print('Message...', file=sys_stdout)


class StringFileDescriptor:
    """File descriptor that writes to string buffer"""

    def __init__(self, fd):
        self.out = StringIO()
        self.fd = fd
        for a in ['encoding']:
            setattr(self, a, getattr(sys_stdout, a))

    def write(self, *data, **kwargs):
        data_string = str(*data)
        print(data_string, file=self.out, end='')

    def flush(self):
        self.out.flush()


class UIBaseTestCase:
    def set_up(self):
        common.setup_test_logger(level='info', prefix=self.config_dir / self.id())
        return component.start()

    def tear_down(self):
        return component.shutdown()

    def exec_command(self):
        if DEBUG_COMMAND:
            print('Executing: %s\n' % sys.argv, file=sys_stdout)
        return self.var['start_cmd']()


class UIWithDaemonBaseTestCase(UIBaseTestCase, DaemonBase):
    """Subclass for test that require a deluged daemon"""

    def set_up(self):
        d = self.common_set_up()
        common.setup_test_logger(level='info', prefix=self.config_dir / self.id())
        return d


class TestDelugeEntry(BaseTestCase):
    def set_up(self):
        return component.start()

    def tear_down(self):
        return component.shutdown()

    def test_deluge_help(self):
        self.patch(sys, 'argv', ['./deluge', '-h'])
        config = deluge.configmanager.ConfigManager('ui.conf', ui_entry.DEFAULT_PREFS)
        config.config['default_ui'] = 'console'
        config.save()

        fd = StringFileDescriptor(sys.stdout)
        self.patch(argparse._sys, 'stdout', fd)

        with mock.patch('deluge.ui.console.main.ConsoleUI'):
            with pytest.raises(SystemExit):
                ui_entry.start_ui()
            assert 'usage: deluge' in fd.out.getvalue()
            assert 'UI Options:' in fd.out.getvalue()
            assert '* console' in fd.out.getvalue()

    def test_start_default(self):
        self.patch(sys, 'argv', ['./deluge'])
        config = deluge.configmanager.ConfigManager('ui.conf', ui_entry.DEFAULT_PREFS)
        config.config['default_ui'] = 'console'
        config.save()

        with mock.patch('deluge.ui.console.main.ConsoleUI'):
            # Just test that no exception is raised
            ui_entry.start_ui()

    def test_start_with_log_level(self):
        _level = []

        def setup_logger(
            level='error',
            filename=None,
            filemode='w',
            logrotate=None,
            output_stream=sys.stdout,
        ):
            _level.append(level)

        self.patch(deluge.log, 'setup_logger', setup_logger)
        self.patch(sys, 'argv', ['./deluge', '-L', 'info'])

        config = deluge.configmanager.ConfigManager('ui.conf', ui_entry.DEFAULT_PREFS)
        config.config['default_ui'] = 'console'
        config.save()

        with mock.patch('deluge.ui.console.main.ConsoleUI'):
            # Just test that no exception is raised
            ui_entry.start_ui()

        assert _level[0] == 'info'


class GtkUIBaseTestCase(UIBaseTestCase):
    """Implement all GtkUI tests here"""

    def test_start_gtk3ui(self):
        self.patch(sys, 'argv', self.var['sys_arg_cmd'])

        from deluge.ui.gtk3 import gtkui

        with mock.patch.object(gtkui.GtkUI, 'start', autospec=True):
            self.exec_command()


@pytest.mark.gtkui
class TestGtkUIDelugeScriptEntry(BaseTestCase, GtkUIBaseTestCase):
    @pytest.fixture(autouse=True)
    def set_var(self, request):
        request.cls.var = {
            'cmd_name': 'deluge gtk',
            'start_cmd': ui_entry.start_ui,
            'sys_arg_cmd': ['./deluge', 'gtk'],
        }


@pytest.mark.gtkui
class TestGtkUIScriptEntry(BaseTestCase, GtkUIBaseTestCase):
    @pytest.fixture(autouse=True)
    def set_var(self, request):
        from deluge.ui import gtk3

        request.cls.var = {
            'cmd_name': 'deluge-gtk',
            'start_cmd': gtk3.start,
            'sys_arg_cmd': ['./deluge-gtk'],
        }


class DelugeWebMock(DelugeWeb):
    def __init__(self, *args, **kwargs):
        kwargs['daemon'] = False
        DelugeWeb.__init__(self, *args, **kwargs)


class WebUIBaseTestCase(UIBaseTestCase):
    """Implement all WebUI tests here"""

    def test_start_webserver(self):
        self.patch(sys, 'argv', self.var['sys_arg_cmd'])
        self.patch(deluge.ui.web.server, 'DelugeWeb', DelugeWebMock)
        self.exec_command()

    def test_start_web_with_log_level(self):
        _level = []

        def setup_logger(
            level='error',
            filename=None,
            filemode='w',
            logrotate=None,
            output_stream=sys.stdout,
        ):
            _level.append(level)

        self.patch(deluge.log, 'setup_logger', setup_logger)
        self.patch(sys, 'argv', self.var['sys_arg_cmd'] + ['-L', 'info'])

        config = deluge.configmanager.ConfigManager('ui.conf', ui_entry.DEFAULT_PREFS)
        config.config['default_ui'] = 'web'
        config.save()

        self.patch(deluge.ui.web.server, 'DelugeWeb', DelugeWebMock)
        self.exec_command()
        assert _level[0] == 'info'


class TestWebUIScriptEntry(BaseTestCase, WebUIBaseTestCase):
    @pytest.fixture(autouse=True)
    def set_var(self, request):
        request.cls.var = {
            'cmd_name': 'deluge-web',
            'start_cmd': deluge.ui.web.start,
            'sys_arg_cmd': ['./deluge-web'],
        }
        if not windows_check():
            request.cls.var['sys_arg_cmd'].append('--do-not-daemonize')


class TestWebUIDelugeScriptEntry(BaseTestCase, WebUIBaseTestCase):
    @pytest.fixture(autouse=True)
    def set_var(self, request):
        request.cls.var = {
            'cmd_name': 'deluge web',
            'start_cmd': ui_entry.start_ui,
            'sys_arg_cmd': ['./deluge', 'web'],
        }
        if not windows_check():
            request.cls.var['sys_arg_cmd'].append('--do-not-daemonize')


class ConsoleUIBaseTestCase(UIBaseTestCase):
    """Implement Console tests that do not require a running daemon"""

    def test_start_console(self):
        self.patch(sys, 'argv', self.var['sys_arg_cmd'])
        with mock.patch('deluge.ui.console.main.ConsoleUI'):
            self.exec_command()

    def test_start_console_with_log_level(self, request):
        _level = []

        def setup_logger(
            level='error',
            filename=None,
            filemode='w',
            logrotate=None,
            output_stream=sys.stdout,
        ):
            _level.append(level)

        self.patch(deluge.log, 'setup_logger', setup_logger)
        self.patch(sys, 'argv', self.var['sys_arg_cmd'] + ['-L', 'info'])

        config = deluge.configmanager.ConfigManager('ui.conf', ui_entry.DEFAULT_PREFS)
        config.config['default_ui'] = 'console'
        config.save()

        with mock.patch('deluge.ui.console.main.ConsoleUI'):
            # Just test that no exception is raised
            self.exec_command()

        assert _level[0] == 'info'

    def test_console_help(self):
        self.patch(sys, 'argv', self.var['sys_arg_cmd'] + ['-h'])
        fd = StringFileDescriptor(sys.stdout)
        self.patch(argparse._sys, 'stdout', fd)

        with mock.patch('deluge.ui.console.main.ConsoleUI'):
            with pytest.raises(SystemExit):
                self.exec_command()
            std_output = fd.out.getvalue()
            assert (
                'usage: %s' % self.var['cmd_name']
            ) in std_output  # Check command name
            assert 'Common Options:' in std_output
            assert 'Console Options:' in std_output
            assert (
                'Console Commands:\n  The following console commands are available:'
                in std_output
            )
            assert 'The following console commands are available:' in std_output

    def test_console_command_info(self):
        self.patch(sys, 'argv', self.var['sys_arg_cmd'] + ['info'])
        fd = StringFileDescriptor(sys.stdout)
        self.patch(argparse._sys, 'stdout', fd)

        with mock.patch('deluge.ui.console.main.ConsoleUI'):
            self.exec_command()

    def test_console_command_info_help(self):
        self.patch(sys, 'argv', self.var['sys_arg_cmd'] + ['info', '-h'])
        fd = StringFileDescriptor(sys.stdout)
        self.patch(argparse._sys, 'stdout', fd)

        with mock.patch('deluge.ui.console.main.ConsoleUI'):
            with pytest.raises(SystemExit):
                self.exec_command()
            std_output = fd.out.getvalue()
            assert 'usage: info' in std_output
            assert 'Show information about the torrents' in std_output

    def test_console_unrecognized_arguments(self):
        self.patch(
            sys, 'argv', ['./deluge', '--ui', 'console']
        )  # --ui is not longer supported
        fd = StringFileDescriptor(sys.stdout)
        self.patch(argparse._sys, 'stderr', fd)
        with mock.patch('deluge.ui.console.main.ConsoleUI'):
            with pytest.raises(SystemExit):
                self.exec_command()
            assert 'unrecognized arguments: --ui' in fd.out.getvalue()


class ConsoleUIWithDaemonBaseTestCase(UIWithDaemonBaseTestCase):
    """Implement Console tests that require a running daemon"""

    def set_up(self):
        # Avoid calling reactor.shutdown after commands are executed by main.exec_args()
        deluge.ui.console.main.reactor = common.ReactorOverride()
        return UIWithDaemonBaseTestCase.set_up(self)

    def patch_arg_command(self, command):
        if type(command) == str:
            command = [command]
        username, password = get_localhost_auth()
        self.patch(
            sys,
            'argv',
            self.var['sys_arg_cmd']
            + ['--port']
            + [str(self.listen_port)]
            + ['--username']
            + [username]
            + ['--password']
            + [password]
            + command,
        )

    @pytest_twisted.inlineCallbacks
    def test_console_command_add(self):
        filename = common.get_test_data_file('test.torrent')
        self.patch_arg_command([f'add "{filename}"'])
        fd = StringFileDescriptor(sys.stdout)
        self.patch(sys, 'stdout', fd)

        yield self.exec_command()

        std_output = fd.out.getvalue()
        assert (
            std_output
            == 'Attempting to add torrent: ' + filename + '\nTorrent added!\n'
        )

    @pytest_twisted.inlineCallbacks
    def test_console_command_add_move_completed(self):
        filename = common.get_test_data_file('test.torrent')
        tmp_path = 'c:\\tmp' if windows_check() else '/tmp'
        self.patch_arg_command(
            [
                f'add --move-path "{tmp_path}" "{filename}" ; status'
                ' ; manage'
                ' ab570cdd5a17ea1b61e970bb72047de141bce173'
                ' move_completed'
                ' move_completed_path'
            ]
        )
        fd = StringFileDescriptor(sys.stdout)
        self.patch(sys, 'stdout', fd)

        yield self.exec_command()

        std_output = fd.out.getvalue()
        assert std_output.endswith(
            f'move_completed: True\nmove_completed_path: {tmp_path}\n'
        ) or std_output.endswith(
            f'move_completed_path: {tmp_path}\nmove_completed: True\n'
        )

    async def test_console_command_status(self):
        fd = StringFileDescriptor(sys.stdout)
        self.patch_arg_command(['status'])
        self.patch(sys, 'stdout', fd)

        await self.exec_command()

        std_output = fd.out.getvalue()
        assert std_output.startswith('Total upload: ')
        assert std_output.endswith(' Moving: 0\n')

    @defer.inlineCallbacks
    def test_console_command_config_set_download_location(self):
        fd = StringFileDescriptor(sys.stdout)
        self.patch_arg_command(['config --set download_location /downloads'])
        self.patch(sys, 'stdout', fd)

        yield self.exec_command()
        std_output = fd.out.getvalue()
        assert std_output.startswith('Setting "download_location" to: \'/downloads\'')
        assert std_output.endswith('Configuration value successfully updated.\n')


@pytest.mark.usefixtures('daemon', 'client')
class TestConsoleScriptEntryWithDaemon(BaseTestCase, ConsoleUIWithDaemonBaseTestCase):
    @pytest.fixture(autouse=True)
    def set_var(self, request):
        request.cls.var = {
            'cmd_name': 'deluge-console',
            'start_cmd': deluge.ui.console.test_start,
            'sys_arg_cmd': ['./deluge-console'],
        }


class TestConsoleScriptEntry(BaseTestCase, ConsoleUIBaseTestCase):
    @pytest.fixture(autouse=True)
    def set_var(self, request):
        request.cls.var = {
            'cmd_name': 'deluge-console',
            'start_cmd': deluge.ui.console.start,
            'sys_arg_cmd': ['./deluge-console'],
        }


class TestConsoleDelugeScriptEntry(BaseTestCase, ConsoleUIBaseTestCase):
    @pytest.fixture(autouse=True)
    def set_var(self, request):
        request.cls.var = {
            'cmd_name': 'deluge console',
            'start_cmd': ui_entry.start_ui,
            'sys_arg_cmd': ['./deluge', 'console'],
        }
