#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import locale
import logging
import os
import sys

from twisted.internet import defer, error, reactor

import deluge.common
import deluge.component as component
from deluge.configmanager import ConfigManager
from deluge.decorators import maybe_coroutine, overrides
from deluge.ui.client import client
from deluge.ui.console.eventlog import EventLog
from deluge.ui.console.modes.addtorrents import AddTorrents
from deluge.ui.console.modes.basemode import TermResizeHandler
from deluge.ui.console.modes.cmdline import CmdLine
from deluge.ui.console.modes.eventview import EventView
from deluge.ui.console.modes.preferences import Preferences
from deluge.ui.console.modes.torrentdetail import TorrentDetail
from deluge.ui.console.modes.torrentlist.torrentlist import TorrentList
from deluge.ui.console.utils import colors
from deluge.ui.console.utils.config import migrate_1_to_2
from deluge.ui.console.widgets import StatusBars
from deluge.ui.coreconfig import CoreConfig
from deluge.ui.sessionproxy import SessionProxy

log = logging.getLogger(__name__)

DEFAULT_CONSOLE_PREFS = {
    'ring_bell': False,
    'first_run': True,
    'language': '',
    'torrentview': {
        'sort_primary': 'queue',
        'sort_secondary': 'name',
        'show_sidebar': True,
        'sidebar_width': 25,
        'separate_complete': True,
        'move_selection': True,
        'columns': {},
    },
    'addtorrents': {
        'show_misc_files': False,  # TODO: Showing/hiding this
        'show_hidden_folders': False,  # TODO: Showing/hiding this
        'sort_column': 'date',
        'reverse_sort': True,
        'last_path': '~',
    },
    'cmdline': {
        'ignore_duplicate_lines': False,
        'third_tab_lists_all': False,
        'torrents_per_tab_press': 15,
        'save_command_history': True,
    },
}


class MockConsoleLog:
    def write(self, data):
        pass

    def flush(self):
        pass


class ConsoleUI(component.Component, TermResizeHandler):
    def __init__(self, options, cmds, log_stream):
        component.Component.__init__(self, 'ConsoleUI')
        TermResizeHandler.__init__(self)
        self.options = options
        self.log_stream = log_stream

        # keep track of events for the log view
        self.events = []
        self.torrents = []
        self.statusbars = None
        self.modes = {}
        self.active_mode = None
        self.initialized = False

        try:
            locale.setlocale(locale.LC_ALL, '')
            self.encoding = locale.getpreferredencoding()
        except locale.Error:
            self.encoding = sys.getdefaultencoding()

        log.debug('Using encoding: %s', self.encoding)

        # start up the session proxy
        self.sessionproxy = SessionProxy()

        client.set_disconnect_callback(self.on_client_disconnect)

        # Set the interactive flag to indicate where we should print the output
        self.interactive = True
        self._commands = cmds
        self.coreconfig = CoreConfig()

    def start_ui(self):
        """Start the console UI.

        Note: When running console UI reactor.run() will be called which
              effectively blocks this function making the return value
              insignificant. However, when running unit tests, the reacor is
              replaced by a mock object, leaving the return deferred object
              necessary for the tests to run properly.

        Returns:
            Deferred: If valid commands are provided, a deferred that fires when
                 all commands are executed. Else None is returned.
        """
        if self.options.parsed_cmds:
            # Non-Interactive mode
            self.interactive = False
            if not self._commands:
                print('No valid console commands found')
                return

            deferred = self.exec_args(self.options)
            reactor.run()
            return deferred

        # Interactive

        # We use the curses.wrapper function to prevent the console from getting
        # messed up if an uncaught exception is experienced.
        try:
            from curses import wrapper
        except ImportError:
            wrapper = None

        if deluge.common.windows_check() and not wrapper:
            print(
                """\nDeluge-console does not run in interactive mode on Windows. \n
Please use commands from the command line, e.g.:\n
deluge-console.exe help
deluge-console.exe info
deluge-console.exe "add --help"
deluge-console.exe "add -p c:\\mytorrents c:\\new.torrent"
"""
            )

        # We don't ever want log output to terminal when running in
        # interactive mode, so insert a dummy here
        self.log_stream.out = MockConsoleLog()

        # Set Esc key delay to 0 to avoid a very annoying delay
        # due to curses waiting in case of other key are pressed
        # after ESC is pressed
        os.environ.setdefault('ESCDELAY', '0')

        wrapper(self.run)

    @maybe_coroutine
    async def quit(self):
        if client.connected():
            await client.disconnect()

        try:
            reactor.stop()
        except error.ReactorNotRunning:
            pass

    @maybe_coroutine
    async def exec_args(self, options):
        """Execute console commands from command line."""
        from deluge.ui.console.cmdline.command import Commander

        commander = Commander(self._commands)
        try:
            if not self.interactive and options.parsed_cmds[0].command == 'connect':
                await commander.exec_command(options.parsed_cmds.pop(0))
            else:
                daemon_options = (
                    options.daemon_addr,
                    options.daemon_port,
                    options.daemon_user,
                    options.daemon_pass,
                )
                log.info(
                    'Connect: host=%s, port=%s, username=%s',
                    *daemon_options[0:3],
                )
                await client.connect(*daemon_options)
        except Exception as reason:
            print(
                'Could not connect to daemon: %s:%s\n %s'
                % (options.daemon_addr, options.daemon_port, reason)
            )
            commander.do_command('quit')

        await self.start_console()
        # Wait for RPCs in start() to finish before processing commands.
        await self.started_deferred

        for cmd in options.parsed_cmds:
            if cmd.command in ('quit', 'exit'):
                break
            await commander.exec_command(cmd)

        commander.do_command('quit')

    def run(self, stdscr):
        """This method is called by the curses.wrapper to start the mainloop and screen.

        Args:
            stdscr (_curses.curses window): curses screen passed in from curses.wrapper.

        """
        # We want to do an interactive session, so start up the curses screen and
        # pass it the function that handles commands
        colors.init_colors()
        self.stdscr = stdscr
        self.config = ConfigManager(
            'console.conf', defaults=DEFAULT_CONSOLE_PREFS, file_version=2
        )
        self.config.run_converter((0, 1), 2, migrate_1_to_2)

        self.statusbars = StatusBars()
        from deluge.ui.console.modes.connectionmanager import ConnectionManager

        self.register_mode(ConnectionManager(stdscr, self.encoding), set_mode=True)

        torrentlist = self.register_mode(TorrentList(self.stdscr, self.encoding))
        self.register_mode(CmdLine(self.stdscr, self.encoding))
        self.register_mode(EventView(torrentlist, self.stdscr, self.encoding))
        self.register_mode(
            TorrentDetail(torrentlist, self.stdscr, self.config, self.encoding)
        )
        self.register_mode(
            Preferences(torrentlist, self.stdscr, self.config, self.encoding)
        )
        self.register_mode(
            AddTorrents(torrentlist, self.stdscr, self.config, self.encoding)
        )

        self.eventlog = EventLog()

        self.active_mode.topbar = (
            '{!status!}Deluge ' + deluge.common.get_version() + ' Console'
        )
        self.active_mode.bottombar = '{!status!}'
        self.active_mode.refresh()
        # Start the twisted mainloop
        reactor.run()

    @overrides(TermResizeHandler)
    def on_resize(self, *args):
        rows, cols = super().on_resize(*args)
        for mode in self.modes:
            self.modes[mode].on_resize(rows, cols)

    def register_mode(self, mode, set_mode=False):
        self.modes[mode.mode_name] = mode
        if set_mode:
            self.set_mode(mode.mode_name)
        return mode

    def set_mode(self, mode_name, refresh=False):
        log.debug('Setting console mode: %s', mode_name)
        mode = self.modes.get(mode_name, None)
        if mode is None:
            log.error('Non-existent mode requested: %s', mode_name)
            return
        self.stdscr.erase()

        if self.active_mode:
            self.active_mode.pause()
            d = component.pause([self.active_mode.mode_name])

            def on_mode_paused(result, mode, *args):
                from deluge.ui.console.widgets.popup import PopupsHandler

                if isinstance(mode, PopupsHandler):
                    if mode.popup is not None:
                        # If popups are not removed, they are still referenced in the memory
                        # which can cause issues as the popup's screen will not be destroyed.
                        # This can lead to the popup border being visible for short periods
                        # while the current modes' screen is repainted.
                        log.error(
                            'Mode "%s" still has popups available after being paused.'
                            ' Ensure all popups are removed on pause!',
                            mode.popup.title,
                        )

            d.addCallback(on_mode_paused, self.active_mode)
            reactor.removeReader(self.active_mode)

        self.active_mode = mode
        self.statusbars.screen = self.active_mode

        # The Screen object is designed to run as a twisted reader so that it
        # can use twisted's select poll for non-blocking user input.
        reactor.addReader(self.active_mode)
        self.stdscr.clear()

        if self.active_mode._component_state == 'Stopped':
            component.start([self.active_mode.mode_name])
        else:
            component.resume([self.active_mode.mode_name])

        mode.resume()
        if refresh:
            mode.refresh()
        return mode

    def switch_mode(self, func, error_smg):
        def on_stop(arg):
            if arg and True in arg[0]:
                func()
            else:
                self.messages.append(('Error', error_smg))

        component.stop(['TorrentList']).addCallback(on_stop)

    def is_active_mode(self, mode):
        return mode == self.active_mode

    @maybe_coroutine
    async def start_components(self):
        if not self.interactive:
            return await component.start(['SessionProxy', 'ConsoleUI', 'CoreConfig'])

        await component.start()
        component.pause(
            [
                'TorrentList',
                'EventView',
                'AddTorrents',
                'TorrentDetail',
                'Preferences',
            ]
        )

    @maybe_coroutine
    async def start_console(self):
        self.started_deferred = defer.Deferred()

        if self.initialized:
            await component.stop(['SessionProxy'])
            await component.start(['SessionProxy'])
        else:
            self.initialized = True
            await self.start_components()

    @maybe_coroutine
    async def start(self):
        result = await client.core.get_session_state()
        # Maintain a list of (torrent_id, name) for use in tab completion
        self.torrents = []
        self.events = []

        torrents = await client.core.get_torrents_status({'id': result}, ['name'])
        for torrent_id, status in torrents.items():
            self.torrents.append((torrent_id, status['name']))

        self.started_deferred.callback(True)

        # Register event handlers to keep the torrent list up-to-date
        client.register_event_handler('TorrentAddedEvent', self.on_torrent_added)
        client.register_event_handler('TorrentRemovedEvent', self.on_torrent_removed)

    @defer.inlineCallbacks
    def on_torrent_added(self, event, from_state=False):
        status = yield client.core.get_torrent_status(event, ['name'])
        self.torrents.append((event, status['name']))

    def on_torrent_removed(self, event):
        for index, (tid, name) in enumerate(self.torrents):
            if event == tid:
                del self.torrents[index]

    def match_torrents(self, strings):
        return list(
            {torrent for string in strings for torrent in self.match_torrent(string)}
        )

    def match_torrent(self, string):
        """
        Returns a list of torrent_id matches for the string.  It will search both
        torrent_ids and torrent names, but will only return torrent_ids.

        :param string: str, the string to match on

        :returns: list of matching torrent_ids. Will return an empty list if
            no matches are found.

        """
        deluge.common.decode_bytes(string, self.encoding)

        if string == '*' or string == '':
            return [tid for tid, name in self.torrents]

        match_func = '__eq__'
        if string.startswith('*'):
            string = string[1:]
            match_func = 'endswith'
        if string.endswith('*'):
            match_func = '__contains__' if match_func == 'endswith' else 'startswith'
            string = string[:-1]

        matches = []
        for tid, name in self.torrents:
            deluge.common.decode_bytes(name, self.encoding)
            if getattr(tid, match_func, None)(string) or getattr(
                name, match_func, None
            )(string):
                matches.append(tid)
        return matches

    def get_torrent_name(self, torrent_id):
        for tid, name in self.torrents:
            if torrent_id == tid:
                return name
        return None

    def set_batch_write(self, batch):
        if self.interactive and isinstance(
            self.active_mode, deluge.ui.console.modes.cmdline.CmdLine
        ):
            return self.active_mode.set_batch_write(batch)

    def tab_complete_torrent(self, line):
        if self.interactive and isinstance(
            self.active_mode, deluge.ui.console.modes.cmdline.CmdLine
        ):
            return self.active_mode.tab_complete_torrent(line)

    def tab_complete_path(
        self, line, path_type='file', ext='', sort='name', dirs_first=True
    ):
        if self.interactive and isinstance(
            self.active_mode, deluge.ui.console.modes.cmdline.CmdLine
        ):
            return self.active_mode.tab_complete_path(
                line, path_type=path_type, ext=ext, sort=sort, dirs_first=dirs_first
            )

    def on_client_disconnect(self):
        component.stop()

    def write(self, s):
        if self.interactive:
            if isinstance(self.active_mode, deluge.ui.console.modes.cmdline.CmdLine):
                self.active_mode.write(s)
            else:
                component.get('CmdLine').add_line(s, False)
                self.events.append(s)
        else:
            print(colors.strip_colors(s))

    def write_event(self, s):
        if self.interactive:
            if isinstance(self.active_mode, deluge.ui.console.modes.cmdline.CmdLine):
                self.events.append(s)
                self.active_mode.write(s)
            else:
                component.get('CmdLine').add_line(s, False)
                self.events.append(s)
        else:
            print(colors.strip_colors(s))
