# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Arek Stefański <asmageddon@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging
import os
from base64 import b64encode

import deluge.common
import deluge.component as component
from deluge.decorators import overrides
from deluge.ui.client import client
from deluge.ui.console.modes.basemode import BaseMode
from deluge.ui.console.modes.torrentlist.add_torrents_popup import report_add_status
from deluge.ui.console.utils import curses_util as util
from deluge.ui.console.utils import format_utils
from deluge.ui.console.widgets.popup import InputPopup, MessagePopup

try:
    from future_builtins import zip
except ImportError:
    # Ignore on Py3.
    pass

try:
    import curses
except ImportError:
    pass

log = logging.getLogger(__name__)

# Big help string that gets displayed when the user hits 'h'
HELP_STR = """\
This screen allows you to browse and add torrent files located on your \
hard disk. Currently selected file is highlighted with a white background.
You can change the selected file using the up/down arrows or the \
PgUp/PgDown keys.  Home and End keys go to the first and last file \
in current directory respectively.

Select files with the 'm' key. Use 'M' for multi-selection. Press \
enter key to add them to session.

{!info!}'h'{!normal!} - Show this help

{!info!}'<'{!normal!} and {!info!}'>'{!normal!} - Change sort column and/or order

{!info!}'m'{!normal!} - Mark or unmark currently highlighted file
{!info!}'M'{!normal!} - Mark all files between current file and last selection.
{!info!}'c'{!normal!} - Clear selection.

{!info!}Left Arrow{!normal!} - Go up in directory hierarchy.
{!info!}Right Arrow{!normal!} - Enter currently highlighted folder.

{!info!}Enter{!normal!} - Enter currently highlighted folder or add torrents \
if a file is highlighted

{!info!}'q'{!normal!} - Go back to torrent overview
"""


class AddTorrents(BaseMode):
    def __init__(self, parent_mode, stdscr, console_config, encoding=None):
        self.console_config = console_config
        self.parent_mode = parent_mode
        self.popup = None
        self.view_offset = 0
        self.cursel = 0
        self.marked = set()
        self.last_mark = -1

        path = os.path.expanduser(self.console_config['addtorrents']['last_path'])

        self.path_stack = ['/'] + path.strip('/').split('/')
        self.path_stack_pos = len(self.path_stack)
        self.listing_files = []
        self.listing_dirs = []

        self.raw_rows = []
        self.raw_rows_files = []
        self.raw_rows_dirs = []
        self.formatted_rows = []

        self.sort_column = self.console_config['addtorrents']['sort_column']
        self.reverse_sort = self.console_config['addtorrents']['reverse_sort']

        BaseMode.__init__(self, stdscr, encoding)

        self._listing_space = self.rows - 5
        self.__refresh_listing()

        util.safe_curs_set(util.Curser.INVISIBLE)
        self.stdscr.notimeout(0)

    @overrides(component.Component)
    def start(self):
        pass

    @overrides(component.Component)
    def update(self):
        pass

    def __refresh_listing(self):
        path = os.path.join(*self.path_stack[: self.path_stack_pos])

        listing = os.listdir(path)

        self.listing_files = []
        self.listing_dirs = []

        self.raw_rows = []
        self.raw_rows_files = []
        self.raw_rows_dirs = []
        self.formatted_rows = []

        for f in listing:
            if os.path.isdir(os.path.join(path, f)):
                if self.console_config['addtorrents']['show_hidden_folders']:
                    self.listing_dirs.append(f)
                elif f[0] != '.':
                    self.listing_dirs.append(f)
            elif os.path.isfile(os.path.join(path, f)):
                if self.console_config['addtorrents']['show_misc_files']:
                    self.listing_files.append(f)
                elif f.endswith('.torrent'):
                    self.listing_files.append(f)

        for dirname in self.listing_dirs:
            row = []
            full_path = os.path.join(path, dirname)
            try:
                size = len(os.listdir(full_path))
            except OSError:
                size = -1
            time = os.stat(full_path).st_mtime

            row = [dirname, size, time, full_path, 1]

            self.raw_rows.append(row)
            self.raw_rows_dirs.append(row)

        # Highlight the directory we came from
        if self.path_stack_pos < len(self.path_stack):
            selected = self.path_stack[self.path_stack_pos]
            ld = sorted(self.listing_dirs, key=lambda n: n.lower())
            c = ld.index(selected)
            self.cursel = c

            if (self.view_offset + self._listing_space) <= self.cursel:
                self.view_offset = self.cursel - self._listing_space

        for filename in self.listing_files:
            row = []
            full_path = os.path.join(path, filename)
            size = os.stat(full_path).st_size
            time = os.stat(full_path).st_mtime

            row = [filename, size, time, full_path, 0]

            self.raw_rows.append(row)
            self.raw_rows_files.append(row)

        self.__sort_rows()

    def __sort_rows(self):
        self.console_config['addtorrents']['sort_column'] = self.sort_column
        self.console_config['addtorrents']['reverse_sort'] = self.reverse_sort
        self.console_config.save()

        self.raw_rows_dirs.sort(key=lambda r: r[0].lower())

        if self.sort_column == 'name':
            self.raw_rows_files.sort(
                key=lambda r: r[0].lower(), reverse=self.reverse_sort
            )
        elif self.sort_column == 'date':
            self.raw_rows_files.sort(key=lambda r: r[2], reverse=self.reverse_sort)
        self.raw_rows = self.raw_rows_dirs + self.raw_rows_files
        self.__refresh_rows()

    def __refresh_rows(self):
        self.formatted_rows = []

        for row in self.raw_rows:
            filename = deluge.common.decode_bytes(row[0])
            size = row[1]
            time = row[2]

            if row[4]:
                if size != -1:
                    size_str = '%i items' % size
                else:
                    size_str = ' unknown'

                cols = [filename, size_str, deluge.common.fdate(time)]
                widths = [self.cols - 35, 12, 23]
                self.formatted_rows.append(format_utils.format_row(cols, widths))
            else:
                # Size of .torrent file itself couldn't matter less so we'll leave it out
                cols = [filename, deluge.common.fdate(time)]
                widths = [self.cols - 23, 23]
                self.formatted_rows.append(format_utils.format_row(cols, widths))

    def scroll_list_up(self, distance):
        self.cursel -= distance
        if self.cursel < 0:
            self.cursel = 0

        if self.cursel < self.view_offset + 1:
            self.view_offset = max(self.cursel - 1, 0)

    def scroll_list_down(self, distance):
        self.cursel += distance
        if self.cursel >= len(self.formatted_rows):
            self.cursel = len(self.formatted_rows) - 1

        if (self.view_offset + self._listing_space) <= self.cursel + 1:
            self.view_offset = self.cursel - self._listing_space + 1

    def set_popup(self, pu):
        self.popup = pu
        self.refresh()

    @overrides(BaseMode)
    def on_resize(self, rows, cols):
        BaseMode.on_resize(self, rows, cols)
        if self.popup:
            self.popup.handle_resize()
        self._listing_space = self.rows - 5
        self.refresh()

    def refresh(self, lines=None):
        if self.mode_paused():
            return

        # Update the status bars
        self.stdscr.erase()
        self.draw_statusbars()

        off = 1

        # Render breadcrumbs
        s = 'Location: '
        for i, e in enumerate(self.path_stack):
            if e == '/':
                if i == self.path_stack_pos - 1:
                    s += '{!black,red,bold!}root'
                else:
                    s += '{!red,black,bold!}root'
            else:
                if i == self.path_stack_pos - 1:
                    s += '{!black,white,bold!}%s' % e
                else:
                    s += '{!white,black,bold!}%s' % e

            if e != len(self.path_stack) - 1:
                s += '{!white,black!}/'

        self.add_string(off, s)
        off += 1

        # Render header
        cols = ['Name', 'Contents', 'Modification time']
        widths = [self.cols - 35, 12, 23]
        s = ''
        for i, (c, w) in enumerate(zip(cols, widths)):
            cn = ''
            if i == 0:
                cn = 'name'
            elif i == 2:
                cn = 'date'

            if cn == self.sort_column:
                s += '{!black,green,bold!}' + c.ljust(w - 2)
                if self.reverse_sort:
                    s += '^ '
                else:
                    s += 'v '
            else:
                s += '{!green,black,bold!}' + c.ljust(w)
        self.add_string(off, s)
        off += 1

        # Render files and folders
        for i, row in enumerate(self.formatted_rows[self.view_offset :]):
            i += self.view_offset
            # It's a folder
            color_string = ''
            if self.raw_rows[i][4]:
                if self.raw_rows[i][1] == -1:
                    if i == self.cursel:
                        color_string = '{!black,red,bold!}'
                    else:
                        color_string = '{!red,black!}'
                else:
                    if i == self.cursel:
                        color_string = '{!black,cyan,bold!}'
                    else:
                        color_string = '{!cyan,black!}'

            elif i == self.cursel:
                if self.raw_rows[i][0] in self.marked:
                    color_string = '{!blue,white,bold!}'
                else:
                    color_string = '{!black,white,bold!}'
            elif self.raw_rows[i][0] in self.marked:
                color_string = '{!white,blue,bold!}'

            self.add_string(off, color_string + row)
            off += 1

            if off > self.rows - 2:
                break

        if not component.get('ConsoleUI').is_active_mode(self):
            return

        self.stdscr.noutrefresh()

        if self.popup:
            self.popup.refresh()

        curses.doupdate()

    def back_to_overview(self):
        self.parent_mode.go_top = False
        component.get('ConsoleUI').set_mode(self.parent_mode.mode_name)

    def _perform_action(self):
        if self.cursel < len(self.listing_dirs):
            self._enter_dir()
        else:
            s = self.raw_rows[self.cursel][0]
            if s not in self.marked:
                self.last_mark = self.cursel
            self.marked.add(s)
            self._show_add_dialog()

    def _enter_dir(self):
        # Enter currently selected directory
        dirname = self.raw_rows[self.cursel][0]
        new_dir = self.path_stack_pos >= len(self.path_stack)
        new_dir = new_dir or (dirname != self.path_stack[self.path_stack_pos])
        if new_dir:
            self.path_stack = self.path_stack[: self.path_stack_pos]
            self.path_stack.append(dirname)

        path = os.path.join(*self.path_stack[: self.path_stack_pos + 1])

        if not os.access(path, os.R_OK):
            self.path_stack = self.path_stack[: self.path_stack_pos]
            self.popup = MessagePopup(
                self, 'Error', '{!error!}Access denied: %s' % path
            )
            self.__refresh_listing()
            return

        self.path_stack_pos += 1

        self.view_offset = 0
        self.cursel = 0
        self.last_mark = -1
        self.marked = set()

        self.__refresh_listing()

    def _show_add_dialog(self):
        def _do_add(result, **kwargs):
            ress = {'succ': 0, 'fail': 0, 'total': len(self.marked), 'fmsg': []}

            def fail_cb(msg, t_file, ress):
                log.debug('failed to add torrent: %s: %s', t_file, msg)
                ress['fail'] += 1
                ress['fmsg'].append('{!input!} * %s: {!error!}%s' % (t_file, msg))
                if (ress['succ'] + ress['fail']) >= ress['total']:
                    report_add_status(
                        component.get('TorrentList'),
                        ress['succ'],
                        ress['fail'],
                        ress['fmsg'],
                    )

            def success_cb(tid, t_file, ress):
                if tid:
                    log.debug('added torrent: %s (%s)', t_file, tid)
                    ress['succ'] += 1
                    if (ress['succ'] + ress['fail']) >= ress['total']:
                        report_add_status(
                            component.get('TorrentList'),
                            ress['succ'],
                            ress['fail'],
                            ress['fmsg'],
                        )
                else:
                    fail_cb('Already in session (probably)', t_file, ress)

            for m in self.marked:
                filename = m
                directory = os.path.join(*self.path_stack[: self.path_stack_pos])
                path = os.path.join(directory, filename)
                with open(path, 'rb') as _file:
                    filedump = b64encode(_file.read())
                t_options = {}
                if result['location']['value']:
                    t_options['download_location'] = result['location']['value']
                t_options['add_paused'] = result['add_paused']['value']

                d = client.core.add_torrent_file_async(filename, filedump, t_options)
                d.addCallback(success_cb, filename, ress)
                d.addErrback(fail_cb, filename, ress)

            self.console_config['addtorrents']['last_path'] = os.path.join(
                *self.path_stack[: self.path_stack_pos]
            )
            self.console_config.save()

            self.back_to_overview()

        config = component.get('ConsoleUI').coreconfig
        if config['add_paused']:
            ap = 0
        else:
            ap = 1
        self.popup = InputPopup(
            self, 'Add Torrents (Esc to cancel)', close_cb=_do_add, height_req=17
        )

        msg = 'Adding torrent files:'
        for i, m in enumerate(self.marked):
            name = m
            msg += '\n * {!input!}%s' % name
            if i == 5:
                if i < len(self.marked):
                    msg += '\n  {!red!}And %i more' % (len(self.marked) - 5)
                break
        self.popup.add_text(msg)
        self.popup.add_spaces(1)

        self.popup.add_text_input(
            'location', 'Download Folder:', config['download_location'], complete=True
        )
        self.popup.add_select_input(
            'add_paused', 'Add Paused:', ['Yes', 'No'], [True, False], ap
        )

    def _go_up(self):
        # Go up in directory hierarchy
        if self.path_stack_pos > 1:
            self.path_stack_pos -= 1

            self.view_offset = 0
            self.cursel = 0
            self.last_mark = -1
            self.marked = set()

            self.__refresh_listing()

    def read_input(self):
        c = self.stdscr.getch()

        if self.popup:
            if self.popup.handle_read(c):
                self.popup = None
            self.refresh()
            return

        if util.is_printable_chr(c):
            if chr(c) == 'Q':
                component.get('ConsoleUI').quit()
            elif chr(c) == 'q':
                self.back_to_overview()
                return

        # Navigate the torrent list
        if c == curses.KEY_UP:
            self.scroll_list_up(1)
        elif c == curses.KEY_PPAGE:
            self.scroll_list_up(self.rows // 2)
        elif c == curses.KEY_HOME:
            self.scroll_list_up(len(self.formatted_rows))
        elif c == curses.KEY_DOWN:
            self.scroll_list_down(1)
        elif c == curses.KEY_NPAGE:
            self.scroll_list_down(self.rows // 2)
        elif c == curses.KEY_END:
            self.scroll_list_down(len(self.formatted_rows))
        elif c == curses.KEY_RIGHT:
            if self.cursel < len(self.listing_dirs):
                self._enter_dir()
        elif c == curses.KEY_LEFT:
            self._go_up()
        elif c in [curses.KEY_ENTER, util.KEY_ENTER2]:
            self._perform_action()
        elif c == util.KEY_ESC:
            self.back_to_overview()
        else:
            if util.is_printable_chr(c):
                if chr(c) == 'h':
                    self.popup = MessagePopup(self, 'Help', HELP_STR, width_req=0.75)
                elif chr(c) == '>':
                    if self.sort_column == 'date':
                        self.reverse_sort = not self.reverse_sort
                    else:
                        self.sort_column = 'date'
                        self.reverse_sort = True
                    self.__sort_rows()
                elif chr(c) == '<':
                    if self.sort_column == 'name':
                        self.reverse_sort = not self.reverse_sort
                    else:
                        self.sort_column = 'name'
                        self.reverse_sort = False
                    self.__sort_rows()
                elif chr(c) == 'm':
                    s = self.raw_rows[self.cursel][0]
                    if s in self.marked:
                        self.marked.remove(s)
                    else:
                        self.marked.add(s)

                    self.last_mark = self.cursel
                elif chr(c) == 'j':
                    self.scroll_list_up(1)
                elif chr(c) == 'k':
                    self.scroll_list_down(1)
                elif chr(c) == 'M':
                    if self.last_mark != -1:
                        if self.last_mark > self.cursel:
                            m = list(range(self.cursel, self.last_mark))
                        else:
                            m = list(range(self.last_mark, self.cursel + 1))

                        for i in m:
                            s = self.raw_rows[i][0]
                            self.marked.add(s)
                elif chr(c) == 'c':
                    self.marked.clear()

        self.refresh()
