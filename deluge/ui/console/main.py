# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import print_function

import locale
import logging
import optparse
import os
import re
import shlex
import sys

from twisted.internet import defer, reactor

import deluge.common
import deluge.component as component
from deluge.ui.client import client
from deluge.ui.console import UI_PATH, colors
from deluge.ui.console.eventlog import EventLog
from deluge.ui.console.statusbars import StatusBars
from deluge.ui.coreconfig import CoreConfig
from deluge.ui.sessionproxy import SessionProxy
from deluge.ui.ui import _UI

log = logging.getLogger(__name__)


class Console(_UI):

    help = """Starts the Deluge console interface"""

    def __init__(self):
        super(Console, self).__init__("console")
        group = optparse.OptionGroup(self.parser, "Console Options", "These daemon connect options will be "
                                     "used for commands, or if console ui autoconnect is enabled.")
        group.add_option("-d", "--daemon", dest="daemon_addr")
        group.add_option("-p", "--port", dest="daemon_port", type="int")
        group.add_option("-u", "--username", dest="daemon_user")
        group.add_option("-P", "--password", dest="daemon_pass")
        self.parser.add_option_group(group)
        self.parser.disable_interspersed_args()

        self.console_cmds = load_commands(os.path.join(UI_PATH, "commands"))

        class CommandOptionGroup(optparse.OptionGroup):
            def __init__(self, parser, title, description=None, cmds=None):
                optparse.OptionGroup.__init__(self, parser, title, description)
                self.cmds = cmds

            def format_help(self, formatter):
                result = formatter.format_heading(self.title)
                formatter.indent()
                if self.description:
                    result += "%s\n" % formatter.format_description(self.description)
                for cname in self.cmds:
                    cmd = self.cmds[cname]
                    if cmd.interactive_only or cname in cmd.aliases:
                        continue
                    allnames = [cname]
                    allnames.extend(cmd.aliases)
                    cname = "/".join(allnames)
                    result += formatter.format_heading(" - ".join([cname, cmd.__doc__]))
                    formatter.indent()
                    result += "%*s%s\n" % (formatter.current_indent, "", cmd.usage.split("\n")[0])
                    formatter.dedent()
                formatter.dedent()
                return result
        cmd_group = CommandOptionGroup(self.parser, "Console Commands",
                                       description="""These commands can be issued from the command line.
                                                    They require quoting and multiple commands separated by ';'
                                                    e.g. Pause torrent with id 'abcd' and get information for id 'efgh':
                                                    `%s \"pause abcd; info efgh\"`"""
                                       % os.path.basename(sys.argv[0]), cmds=self.console_cmds)
        self.parser.add_option_group(cmd_group)

    def start(self):
        super(Console, self).start()
        ConsoleUI(self.args, self.console_cmds, (self.options.daemon_addr, self.options.daemon_port,
                                                 self.options.daemon_user, self.options.daemon_pass))


def start():
    Console().start()


class DelugeHelpFormatter(optparse.IndentedHelpFormatter):
    """
    Format help in a way suited to deluge Legacy mode - colors, format, indentation...
    """

    replace_dict = {
        "<torrent-id>": "{!green!}%s{!input!}",
        "<state>": "{!yellow!}%s{!input!}",
        "\\.\\.\\.": "{!yellow!}%s{!input!}",
        "\\s\\*\\s": "{!blue!}%s{!input!}",
        "(?<![\\-a-z])(-[a-zA-Z0-9])": "{!red!}%s{!input!}",
        # "(\-[a-zA-Z0-9])": "{!red!}%s{!input!}",
        "--[_\\-a-zA-Z0-9]+": "{!green!}%s{!input!}",
        "(\\[|\\])": "{!info!}%s{!input!}",

        "<tab>": "{!white!}%s{!input!}",
        "[_A-Z]{3,}": "{!cyan!}%s{!input!}",

        "<download-folder>": "{!yellow!}%s{!input!}",
        "<torrent-file>": "{!green!}%s{!input!}"

    }

    def __init__(self,
                 indent_increment=2,
                 max_help_position=24,
                 width=None,
                 short_first=1):
        optparse.IndentedHelpFormatter.__init__(
            self, indent_increment, max_help_position, width, short_first)

    def _format_colors(self, string):
        def r(repl):
            return lambda s: repl % s.group()

        for key, replacement in self.replace_dict.items():
            string = re.sub(key, r(replacement), string)

        return string

    def format_usage(self, usage):

        return _("{!info!}Usage{!input!}: %s\n") % self._format_colors(usage)

    def format_option(self, option):
        result = []
        opts = self.option_strings[option]
        opt_width = self.help_position - self.current_indent - 2
        if len(opts) > opt_width:
            opts = "%*s%s\n" % (self.current_indent, "", opts)
            opts = self._format_colors(opts)
            indent_first = self.help_position
        else:  # start help on same line as opts
            opts = "%*s%-*s  " % (self.current_indent, "", opt_width, opts)
            opts = self._format_colors(opts)
            indent_first = 0
        result.append(opts)
        if option.help:
            help_text = self.expand_default(option)
            help_text = self._format_colors(help_text)
            help_lines = optparse.textwrap.wrap(help_text, self.help_width)
            result.append("%*s%s\n" % (indent_first, "", help_lines[0]))
            result.extend(["%*s%s\n" % (self.help_position, "", line)
                           for line in help_lines[1:]])
        elif opts[-1] != "\n":
            result.append("\n")
        return "".join(result)


class OptionParser(optparse.OptionParser):
    """subclass from optparse.OptionParser so exit() won't exit."""
    def __init__(self, **kwargs):
        optparse.OptionParser.__init__(self, **kwargs)

        self.formatter = DelugeHelpFormatter()

    def exit(self, status=0, msg=None):
        self.values._exit = True
        if msg:
            print(msg)

    def error(self, msg):
        """error(msg : string)

           Print a usage message incorporating 'msg' to stderr and exit.
           If you override this in a subclass, it should not return -- it
           should either exit or raise an exception.
        """
        raise Exception(msg)

    def print_usage(self, _file=None):
        console = component.get("ConsoleUI")
        if self.usage:
            for line in self.get_usage().splitlines():
                console.write(line)

    def print_help(self, _file=None):
        console = component.get("ConsoleUI")
        console.set_batch_write(True)
        for line in self.format_help().splitlines():
            console.write(line)
        console.set_batch_write(False)

    def format_option_help(self, formatter=None):
        if formatter is None:
            formatter = self.formatter
        formatter.store_option_strings(self)
        result = []
        result.append(formatter.format_heading(_("{!info!}Options{!input!}")))
        formatter.indent()
        if self.option_list:
            result.append(optparse.OptionContainer.format_option_help(self, formatter))
            result.append("\\n")
        for group in self.option_groups:
            result.append(group.format_help(formatter))
            result.append("\\n")
        formatter.dedent()
        # Drop the last "\\n", or the header if no options or option groups:
        return "".join(result[:-1])


class BaseCommand(object):

    usage = "usage"
    interactive_only = False
    option_list = tuple()
    aliases = []

    def complete(self, text, *args):
        return []

    def handle(self, *args, **options):
        pass

    @property
    def name(self):
        return "base"

    @property
    def epilog(self):
        return self.__doc__

    def split(self, text):
        if deluge.common.windows_check():
            text = text.replace("\\", "\\\\")
        result = shlex.split(text)
        for i, s in enumerate(result):
            result[i] = s.replace(r"\ ", " ")
        result = [s for s in result if s != ""]
        return result

    def create_parser(self):
        return OptionParser(prog=self.name, usage=self.usage, epilog=self.epilog, option_list=self.option_list)


def load_commands(command_dir, exclude=None):
    if not exclude:
        exclude = []

    def get_command(name):
        return getattr(__import__("deluge.ui.console.commands.%s" % name, {}, {}, ["Command"]), "Command")()

    try:
        commands = []
        for filename in os.listdir(command_dir):
            if filename.split(".")[0] in exclude or filename.startswith("_"):
                continue
            if not (filename.endswith(".py") or filename.endswith(".pyc")):
                continue
            cmd = get_command(filename.split(".")[len(filename.split(".")) - 2])
            aliases = [filename.split(".")[len(filename.split(".")) - 2]]
            aliases.extend(cmd.aliases)
            for a in aliases:
                commands.append((a, cmd))
        return dict(commands)
    except OSError:
        return {}


class ConsoleUI(component.Component):
    def __init__(self, args=None, cmds=None, daemon=None):
        component.Component.__init__(self, "ConsoleUI", 2)

        # keep track of events for the log view
        self.events = []

        try:
            locale.setlocale(locale.LC_ALL, "")
            self.encoding = locale.getpreferredencoding()
        except Exception:
            self.encoding = sys.getdefaultencoding()

        log.debug("Using encoding: %s", self.encoding)

        # start up the session proxy
        self.sessionproxy = SessionProxy()

        client.set_disconnect_callback(self.on_client_disconnect)

        # Set the interactive flag to indicate where we should print the output
        self.interactive = True
        self._commands = cmds
        if args:
            args = " ".join(args)
            self.interactive = False
            if not cmds:
                print("Sorry, couldn't find any commands")
                return
            else:
                from deluge.ui.console.commander import Commander
                cmdr = Commander(cmds)
                if daemon:
                    cmdr.exec_args(args, *daemon)
                else:
                    cmdr.exec_args(args, None, None, None, None)

        self.coreconfig = CoreConfig()
        if self.interactive and not deluge.common.windows_check():
            # We use the curses.wrapper function to prevent the console from getting
            # messed up if an uncaught exception is experienced.
            import curses.wrapper
            curses.wrapper(self.run)
        elif self.interactive and deluge.common.windows_check():
            print("""\nDeluge-console does not run in interactive mode on Windows. \n
Please use commands from the command line, eg:\n
    deluge-console.exe help
    deluge-console.exe info
    deluge-console.exe "add --help"
    deluge-console.exe "add -p c:\\mytorrents c:\\new.torrent"
            """)
        else:
            reactor.run()

    def run(self, stdscr):
        """
        This method is called by the curses.wrapper to start the mainloop and
        screen.

        :param stdscr: curses screen passed in from curses.wrapper

        """
        # We want to do an interactive session, so start up the curses screen and
        # pass it the function that handles commands
        colors.init_colors()
        self.statusbars = StatusBars()
        from deluge.ui.console.modes.connectionmanager import ConnectionManager
        self.stdscr = stdscr
        self.screen = ConnectionManager(stdscr, self.encoding)
        self.eventlog = EventLog()

        self.screen.topbar = "{!status!}Deluge " + deluge.common.get_version() + " Console"
        self.screen.bottombar = "{!status!}"
        self.screen.refresh()

        # The Screen object is designed to run as a twisted reader so that it
        # can use twisted's select poll for non-blocking user input.
        reactor.addReader(self.screen)

        # Start the twisted mainloop
        reactor.run()

    def start(self):
        # Maintain a list of (torrent_id, name) for use in tab completion
        self.torrents = []
        if not self.interactive:
            self.started_deferred = defer.Deferred()

            def on_session_state(result):
                def on_torrents_status(torrents):
                    for torrent_id, status in torrents.items():
                        self.torrents.append((torrent_id, status["name"]))
                    self.started_deferred.callback(True)

                client.core.get_torrents_status({"id": result}, ["name"]).addCallback(on_torrents_status)
            client.core.get_session_state().addCallback(on_session_state)

    def match_torrent(self, string):
        """
        Returns a list of torrent_id matches for the string.  It will search both
        torrent_ids and torrent names, but will only return torrent_ids.

        :param string: str, the string to match on

        :returns: list of matching torrent_ids. Will return an empty list if
            no matches are found.

        """
        if self.interactive and isinstance(self.screen, deluge.ui.console.modes.legacy.Legacy):
            return self.screen.match_torrent(string)
        matches = []

        string = string.decode(self.encoding)
        for tid, name in self.torrents:
            if tid.startswith(string) or name.startswith(string):
                matches.append(tid)

        return matches

    def get_torrent_name(self, torrent_id):
        if self.interactive and hasattr(self.screen, "get_torrent_name"):
            return self.screen.get_torrent_name(torrent_id)

        for tid, name in self.torrents:
            if torrent_id == tid:
                return name

        return None

    def set_batch_write(self, batch):
        if self.interactive and isinstance(self.screen, deluge.ui.console.modes.legacy.Legacy):
            return self.screen.set_batch_write(batch)

    def tab_complete_torrent(self, line):
        if self.interactive and isinstance(self.screen, deluge.ui.console.modes.legacy.Legacy):
            return self.screen.tab_complete_torrent(line)

    def tab_complete_path(self, line, path_type="file", ext="", sort="name", dirs_first=True):
        if self.interactive and isinstance(self.screen, deluge.ui.console.modes.legacy.Legacy):
            return self.screen.tab_complete_path(line, path_type=path_type, ext=ext, sort=sort, dirs_first=dirs_first)

    def set_mode(self, mode):
        reactor.removeReader(self.screen)
        self.screen = mode
        self.statusbars.screen = self.screen
        reactor.addReader(self.screen)
        mode.refresh()

    def on_client_disconnect(self):
        component.stop()

    def write(self, s):
        if self.interactive:
            if isinstance(self.screen, deluge.ui.console.modes.legacy.Legacy):
                self.screen.write(s)
            else:
                component.get("LegacyUI").add_line(s, False)
                self.events.append(s)
        else:
            print(colors.strip_colors(deluge.common.utf8_encoded(s)))

    def write_event(self, s):
        if self.interactive:
            if isinstance(self.screen, deluge.ui.console.modes.legacy.Legacy):
                self.events.append(s)
                self.screen.write(s)
            else:
                component.get("LegacyUI").add_line(s, False)
                self.events.append(s)
        else:
            print(colors.strip_colors(deluge.common.utf8_encoded(s)))
