# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging
from collections import deque

import deluge.component as component
from deluge.common import FILE_PRIORITY, fdate, fsize, ftime
from deluge.ui.client import client
from deluge.ui.console import colors
from deluge.ui.console.modes import format_utils
from deluge.ui.console.modes.basemode import BaseMode
from deluge.ui.console.modes.input_popup import InputPopup
from deluge.ui.console.modes.popup import MessagePopup, SelectablePopup
from deluge.ui.console.modes.torrent_actions import ACTION, torrent_actions_popup

try:
    import curses
except ImportError:
    pass

log = logging.getLogger(__name__)

# Big help string that gets displayed when the user hits 'h'
HELP_STR = """\
This screen shows detailed information about a torrent, and also the \
information about the individual files in the torrent.

You can navigate the file list with the Up/Down arrows and use space to \
collapse/expand the file tree.

All popup windows can be closed/canceled by hitting the Esc key \
(you might need to wait a second for an Esc to register)

The actions you can perform and the keys to perform them are as follows:

{!info!}'h'{!normal!} - Show this help

{!info!}'a'{!normal!} - Show torrent actions popup.  Here you can do things like \
pause/resume, recheck, set torrent options and so on.

{!info!}'r'{!normal!} - Rename currently highlighted folder or a file. You can't \
rename multiple files at once so you need to first clear your selection \
with {!info!}'c'{!normal!}

{!info!}'m'{!normal!} - Mark or unmark a file or a folder
{!info!}'c'{!normal!} - Un-mark all files

{!info!}Space{!normal!} - Expand/Collapse currently selected folder

{!info!}Enter{!normal!} - Show priority popup in which you can set the \
download priority of selected files and folders.

{!info!}Left Arrow{!normal!} - Go back to torrent overview.
"""


class TorrentDetail(BaseMode, component.Component):
    def __init__(self, alltorrentmode, torrentid, stdscr, console_config, encoding=None):

        self.console_config = console_config
        self.alltorrentmode = alltorrentmode
        self.torrentid = torrentid
        self.torrent_state = None
        self.popup = None
        self.messages = deque()
        self._status_keys = ["files", "name", "state", "download_payload_rate", "upload_payload_rate",
                             "progress", "eta", "all_time_download", "total_uploaded", "ratio",
                             "num_seeds", "total_seeds", "num_peers", "total_peers", "active_time",
                             "seeding_time", "time_added", "distributed_copies", "num_pieces",
                             "piece_length", "download_location", "file_progress", "file_priorities", "message",
                             "total_wanted", "tracker_host", "owner"]

        self.file_list = None
        self.current_file = None
        self.current_file_idx = 0
        self.file_off = 0
        self.more_to_draw = False
        self.full_names = None

        self.column_string = ""
        self.files_sep = None

        self.marked = {}

        BaseMode.__init__(self, stdscr, encoding)
        component.Component.__init__(self, "TorrentDetail", 1, depend=["SessionProxy"])

        self.column_names = ["Filename", "Size", "Progress", "Priority"]
        self.__update_columns()

        component.start(["TorrentDetail"])

        self._listing_start = self.rows // 2
        self._listing_space = self._listing_start - self._listing_start

        client.register_event_handler("TorrentFileRenamedEvent", self._on_torrentfilerenamed_event)
        client.register_event_handler("TorrentFolderRenamedEvent", self._on_torrentfolderrenamed_event)
        client.register_event_handler("TorrentRemovedEvent", self._on_torrentremoved_event)

        curses.curs_set(0)
        self.stdscr.notimeout(0)

    # component start/update
    def start(self):
        component.get("SessionProxy").get_torrent_status(self.torrentid, self._status_keys).addCallback(self.set_state)

    def update(self):
        component.get("SessionProxy").get_torrent_status(self.torrentid, self._status_keys).addCallback(self.set_state)

    def set_state(self, state):
        log.debug("got state")

        if state.get("files"):
            self.full_names = dict([(x["index"], x["path"]) for x in state["files"]])

        need_prio_update = False
        if not self.file_list:
            # don't keep getting the files once we've got them once
            if state.get("files"):
                self.files_sep = "{!green,black,bold,underline!}%s" % (
                    ("Files (torrent has %d files)" % len(state["files"])).center(self.cols))
                self.file_list, self.file_dict = self.build_file_list(state["files"], state["file_progress"],
                                                                      state["file_priorities"])
                self._status_keys.remove("files")
            else:
                self.files_sep = "{!green,black,bold,underline!}%s" % (("Files (File list unknown)").center(self.cols))
            need_prio_update = True
        self.__fill_progress(self.file_list, state["file_progress"])
        for i, prio in enumerate(state["file_priorities"]):
            if self.file_dict[i][6] != prio:
                need_prio_update = True
                self.file_dict[i][6] = prio
        if need_prio_update:
            self.__fill_prio(self.file_list)
        del state["file_progress"]
        del state["file_priorities"]
        self.torrent_state = state
        self.refresh()

    def build_file_list(self, torrent_files, progress, priority):
        """ Split file list from torrent state into a directory tree.

        Returns:

            Tuple:
                A list of lists in the form:
                    [file/dir_name, index, size, children, expanded, progress, priority]

                Dictionary:
                    Map of file index for fast updating of progress and priorities.
        """

        file_list = []
        file_dict = {}
        # directory index starts from total file count.
        dir_idx = len(torrent_files)
        for torrent_file in torrent_files:
            cur = file_list
            paths = torrent_file["path"].split("/")
            for path in paths:
                if not cur or path != cur[-1][0]:
                    child_list = []
                    if path == paths[-1]:
                        file_progress = format_utils.format_progress(progress[torrent_file["index"]] * 100)
                        entry = [path, torrent_file["index"], torrent_file["size"], child_list,
                                 False, file_progress, priority[torrent_file["index"]]]
                        file_dict[torrent_file["index"]] = entry
                    else:
                        entry = [path, dir_idx, -1, child_list, False, 0, -1]
                        file_dict[dir_idx] = entry
                        dir_idx += 1
                    cur.append(entry)
                    cur = child_list
                else:
                    cur = cur[-1][3]
        self.__build_sizes(file_list)
        self.__fill_progress(file_list, progress)
        return file_list, file_dict

    # fill in the sizes of the directory entries based on their children
    def __build_sizes(self, fs):
        ret = 0
        for f in fs:
            if f[2] == -1:
                val = self.__build_sizes(f[3])
                ret += val
                f[2] = val
            else:
                ret += f[2]
        return ret

    # fills in progress fields in all entries based on progs
    # returns the # of bytes complete in all the children of fs
    def __fill_progress(self, fs, progs):
        if not progs:
            return 0
        tb = 0
        for f in fs:
            if f[3]:  # dir, has some children
                bd = self.__fill_progress(f[3], progs)
                f[5] = format_utils.format_progress((bd / f[2]) * 100)
            else:  # file, update own prog and add to total
                bd = f[2] * progs[f[1]]
                f[5] = format_utils.format_progress(progs[f[1]] * 100)
            tb += bd
        return tb

    def __fill_prio(self, fs):
        for f in fs:
            if f[3]:  # dir, so fill in children and compute our prio
                self.__fill_prio(f[3])
                child_prios = [e[6] for e in f[3]]
                if len(child_prios) > 1:
                    f[6] = -2  # mixed
                else:
                    f[6] = child_prios.pop(0)

    def __update_columns(self):
        self.column_widths = [-1, 15, 15, 20]
        req = sum([col_width for col_width in self.column_widths if col_width >= 0])
        if req > self.cols:  # can't satisfy requests, just spread out evenly
            cw = int(self.cols / len(self.column_names))
            for i in range(0, len(self.column_widths)):
                self.column_widths[i] = cw
        else:
            rem = self.cols - req
            var_cols = len([col_width for col_width in self.column_widths if col_width < 0])
            vw = int(rem / var_cols)
            for i in range(0, len(self.column_widths)):
                if self.column_widths[i] < 0:
                    self.column_widths[i] = vw

        self.column_string = "{!green,black,bold!}%s" % ("".join(["%s%s" % (self.column_names[i], " " * (
            self.column_widths[i] - len(self.column_names[i]))) for i in range(0, len(self.column_names))]))

    def report_message(self, title, message):
        self.messages.append((title, message))

    def clear_marks(self):
        self.marked = {}

    def set_popup(self, pu):
        self.popup = pu
        self.refresh()

    def _on_torrentremoved_event(self, torrent_id):
        if torrent_id == self.torrentid:
            self.back_to_overview()

    def _on_torrentfilerenamed_event(self, torrent_id, index, new_name):
        if torrent_id == self.torrentid:
            self.file_dict[index][0] = new_name.split("/")[-1]
            component.get("SessionProxy").get_torrent_status(
                self.torrentid, self._status_keys).addCallback(self.set_state)

    def _on_torrentfolderrenamed_event(self, torrent_id, old_folder, new_folder):
        if torrent_id == self.torrentid:
            fe = None
            fl = None
            for i in old_folder.strip("/").split("/"):
                if not fl:
                    fe = fl = self.file_list
                s = [files for files in fl if files[0].strip("/") == i][0]
                fe = s
                fl = s[3]
            fe[0] = new_folder.strip("/").rpartition("/")[-1]

            # self.__get_file_by_name(old_folder, self.file_list)[0] = new_folder.strip("/")
            component.get("SessionProxy").get_torrent_status(
                self.torrentid, self._status_keys).addCallback(self.set_state)

    def draw_files(self, files, depth, off, idx):

        color_selected = "blue"
        color_partially_selected = "magenta"
        color_highlighted = "white"
        for fl in files:
            # from sys import stderr
            # print >> stderr, fl[6]
            # kick out if we're going to draw too low on the screen
            if off >= self.rows - 1:
                self.more_to_draw = True
                return -1, -1

            # default color values
            fg = "white"
            bg = "black"
            attr = ""

            if fl[6] == -2:
                pass  # Mixed
            elif fl[6] == 0:
                fg = "red"  # Do Not Download
            elif fl[6] == 1:
                pass  # Normal
            elif fl[6] <= 6:
                fg = "yellow"  # High
            elif fl[6] == 7:
                fg = "green"  # Highest

            if idx >= self.file_off:
                # set fg/bg colors based on whether the file is selected/marked or not

                if fl[1] in self.marked:
                    bg = color_selected
                    if fl[3]:
                        if self.marked[fl[1]] < self.__get_contained_files_count(file_list=fl[3]):
                            bg = color_partially_selected
                    attr = "bold"

                if idx == self.current_file_idx:
                    self.current_file = fl
                    bg = color_highlighted
                    if fl[1] in self.marked:
                        fg = color_selected
                        if fl[3]:
                            if self.marked[fl[1]] < self.__get_contained_files_count(file_list=fl[3]):
                                fg = color_partially_selected
                    else:
                        if fg == "white":
                            fg = "black"
                        attr = "bold"

                if attr:
                    color_string = "{!%s,%s,%s!}" % (fg, bg, attr)
                else:
                    color_string = "{!%s,%s!}" % (fg, bg)

                # actually draw the dir/file string
                if fl[3] and fl[4]:  # this is an expanded directory
                    xchar = "v"
                elif fl[3]:  # collapsed directory
                    xchar = ">"
                else:  # file
                    xchar = "-"

                r = format_utils.format_row(["%s%s %s" % (" " * depth, xchar, fl[0]),
                                             fsize(fl[2]), fl[5],
                                             format_utils.format_priority(fl[6])],
                                            self.column_widths)

                self.add_string(off, "%s%s" % (color_string, r), trim=False)
                off += 1

            if fl[3] and fl[4]:
                # recurse if we have children and are expanded
                off, idx = self.draw_files(fl[3], depth + 1, off, idx + 1)
                if off < 0:
                    return (off, idx)
            else:
                idx += 1

        return (off, idx)

    def __get_file_list_length(self, file_list=None):
        """
        Counts length of the displayed file list.
        """
        if file_list is None:
            file_list = self.file_list
        length = 0
        if file_list:
            for element in file_list:
                length += 1
                if element[3] and element[4]:
                    length += self.__get_file_list_length(element[3])
        return length

    def __get_contained_files_count(self, file_list=None, idx=None):
        length = 0
        if file_list is None:
            file_list = self.file_list
        if idx is not None:
            for element in file_list:
                if element[1] == idx:
                    return self.__get_contained_files_count(file_list=element[3])
                elif element[3]:
                    c = self.__get_contained_files_count(file_list=element[3], idx=idx)
                    if c > 0:
                        return c
        else:
            for element in file_list:
                length += 1
                if element[3]:
                    length -= 1
                    length += self.__get_contained_files_count(element[3])
        return length

    def on_resize(self, *args):
        BaseMode.on_resize_norefresh(self, *args)

        # Always refresh Legacy(it will also refresh AllTorrents), otherwise it will bug deluge out
        legacy = component.get("LegacyUI")
        legacy.on_resize(*args)

        self.__update_columns()
        if self.popup:
            self.popup.handle_resize()

        self._listing_start = self.rows / 2
        self.refresh()

    def render_header(self, off):
        status = self.torrent_state

        up_color = colors.state_color["Seeding"]
        down_color = colors.state_color["Downloading"]

        # Name
        s = "{!info!}Name: {!input!}%s" % status["name"]
        self.add_string(off, s)
        off += 1

        # Print DL info and ETA
        if status["download_payload_rate"] > 0:
            s = "%sDownloading: {!input!}" % down_color
        else:
            s = "{!info!}Downloaded: {!input!}"
        s += fsize(status["all_time_download"])
        if status["progress"] != 100.0:
            s += "/%s" % fsize(status["total_wanted"])
        if status["download_payload_rate"] > 0:
            s += " {!yellow!}@ %s%s" % (down_color, fsize(status["download_payload_rate"]))
            s += "{!info!} ETA: {!input!}%s" % format_utils.format_time(status["eta"])
        self.add_string(off, s)
        off += 1

        # Print UL info and ratio
        if status["upload_payload_rate"] > 0:
            s = "%sUploading: {!input!}" % up_color
        else:
            s = "{!info!}Uploaded: {!input!}"
        s += fsize(status["total_uploaded"])
        if status["upload_payload_rate"] > 0:
            s += " {!yellow!}@ %s%s" % (up_color, fsize(status["upload_payload_rate"]))
        ratio_str = format_utils.format_float(status["ratio"])
        if ratio_str == "-":
            ratio_str = "inf"
        s += " {!info!}Ratio: {!input!}%s" % ratio_str
        self.add_string(off, s)
        off += 1

        # Seed/peer info
        s = "{!info!}Seeds:{!green!} %s {!input!}(%s)" % (status["num_seeds"], status["total_seeds"])
        self.add_string(off, s)
        off += 1
        s = "{!info!}Peers:{!red!} %s {!input!}(%s)" % (status["num_peers"], status["total_peers"])
        self.add_string(off, s)
        off += 1

        # Tracker
        if status["message"] == "OK":
            color = "{!green!}"
        else:
            color = "{!red!}"
        s = "{!info!}Tracker: {!magenta!}%s{!input!} says \"%s%s{!input!}\"" % (
            status["tracker_host"], color, status["message"])
        self.add_string(off, s)
        off += 1

        # Pieces and availability
        s = "{!info!}Pieces: {!yellow!}%s {!input!}x {!yellow!}%s" % (
            status["num_pieces"], fsize(status["piece_length"]))
        if status["distributed_copies"]:
            s += " {!info!}Availability: {!input!}%s" % format_utils.format_float(status["distributed_copies"])
        self.add_string(off, s)
        off += 1

        # Time added
        s = "{!info!}Added: {!input!}%s" % fdate(status["time_added"])
        self.add_string(off, s)
        off += 1

        # Time active
        s = "{!info!}Time active: {!input!}%s" % (ftime(status["active_time"]))
        if status["seeding_time"]:
            s += ", {!cyan!}%s{!input!} seeding" % (ftime(status["seeding_time"]))
        self.add_string(off, s)
        off += 1

        # Download Folder
        s = "{!info!}Download Folder: {!input!}%s" % status["download_location"]
        self.add_string(off, s)
        off += 1

        # Owner
        if status["owner"]:
            s = "{!info!}Owner: {!input!}%s" % status["owner"]

        return off

    def refresh(self, lines=None):
        # show a message popup if there's anything queued
        if self.popup is None and self.messages:
            title, msg = self.messages.popleft()
            self.popup = MessagePopup(self, title, msg)

        # Update the status bars
        self.stdscr.erase()
        self.add_string(0, self.statusbars.topbar)

        # This will quite likely fail when switching modes
        try:
            rf = format_utils.remove_formatting
            string = self.statusbars.bottombar
            hstr = "Press {!magenta,blue,bold!}[h]{!status!} for help"

            string += " " * (self.cols - len(rf(string)) - len(rf(hstr))) + hstr

            self.add_string(self.rows - 1, string)
        except Exception as ex:
            log.debug("Exception caught: %s", ex)

        off = 1
        if self.torrent_state:
            off = self.render_header(off)
        else:
            self.add_string(1, "Waiting for torrent state")

        off += 1

        if self.files_sep:
            self.add_string(off, self.files_sep)
            off += 1

        self._listing_start = off
        self._listing_space = self.rows - self._listing_start

        self.add_string(off, self.column_string)
        if self.file_list:
            off += 1
            self.more_to_draw = False
            self.draw_files(self.file_list, 0, off, 0)

        if component.get("ConsoleUI").screen != self:
            return

        self.stdscr.noutrefresh()

        if self.popup:
            self.popup.refresh()

        curses.doupdate()

    def expcol_cur_file(self):
        """
        Expand or collapse current file
        """
        self.current_file[4] = not self.current_file[4]
        self.refresh()

    def file_list_down(self, rows=1):
        maxlen = self.__get_file_list_length() - 1

        self.current_file_idx += rows

        if self.current_file_idx > maxlen:
            self.current_file_idx = maxlen

        if self.current_file_idx > self.file_off + (self._listing_space - 3):
            self.file_off = self.current_file_idx - (self._listing_space - 3)

        self.refresh()

    def file_list_up(self, rows=1):
        self.current_file_idx = max(0, self.current_file_idx - rows)
        self.file_off = min(self.file_off, self.current_file_idx)
        self.refresh()

    def back_to_overview(self):
        component.stop(["TorrentDetail"])
        component.deregister(self)
        self.stdscr.erase()
        component.get("ConsoleUI").set_mode(self.alltorrentmode)
        self.alltorrentmode._go_top = False
        self.alltorrentmode.resume()

    # build list of priorities for all files in the torrent
    # based on what is currently selected and a selected priority.
    def build_prio_list(self, files, ret_list, parent_prio, selected_prio):
        # has a priority been set on my parent (if so, I inherit it)
        for f in files:
            # Do not set priorities for the whole dir, just selected contents
            if f[3]:
                self.build_prio_list(f[3], ret_list, parent_prio, selected_prio)
            else:  # file, need to add to list
                if f[1] in self.marked or parent_prio >= 0:
                    # selected (or parent selected), use requested priority
                    ret_list.append((f[1], selected_prio))
                else:
                    # not selected, just keep old priority
                    ret_list.append((f[1], f[6]))

    def do_priority(self, idx, data, was_empty):
        plist = []
        self.build_prio_list(self.file_list, plist, -1, data)
        plist.sort()
        priorities = [p[1] for p in plist]
        log.debug("priorities: %s", priorities)

        client.core.set_torrent_file_priorities(self.torrentid, priorities)

        if was_empty:
            self.marked = {}
        return True

    # show popup for priority selections
    def show_priority_popup(self, was_empty):
        def popup_func(idx, data, we=was_empty):
            return self.do_priority(idx, data, we)

        if self.marked:
            self.popup = SelectablePopup(self, "Set File Priority", popup_func)
            self.popup.add_line("_Do Not Download", data=FILE_PRIORITY["Do Not Download"], foreground="red")
            self.popup.add_line("_Normal Priority", data=FILE_PRIORITY["Normal Priority"])
            self.popup.add_line("_High Priority", data=FILE_PRIORITY["High Priority"], foreground="yellow")
            self.popup.add_line("H_ighest Priority", data=FILE_PRIORITY["Highest Priority"], foreground="green")
            self.popup._selected = 1

    def __mark_unmark(self, idx):
        """
        Selects or unselects file or a catalog(along with contained files)
        """
        fc = self.__get_contained_files_count(idx=idx)
        if idx not in self.marked:
            # Not selected, select it
            self.__mark_tree(self.file_list, idx)
        elif self.marked[idx] < fc:
            # Partially selected, unselect all contents
            self.__unmark_tree(self.file_list, idx)
        else:
            # Selected, unselect it
            self.__unmark_tree(self.file_list, idx)

    def __mark_tree(self, file_list, idx, mark_all=False):
        """
        Given file_list of TorrentDetail and index of file or folder,
        recursively selects all files contained
        as well as marks folders higher in hierarchy as partially selected
        """
        total_marked = 0
        for element in file_list:
            marked = 0
            # Select the file if it's the one we want or
            # if it's inside a directory that got selected
            if (element[1] == idx) or mark_all:
                # If it's a folder then select everything inside
                if element[3]:
                    marked = self.__mark_tree(element[3], idx, True)
                    self.marked[element[1]] = marked
                else:
                    marked = 1
                    self.marked[element[1]] = 1
            else:
                # Does not match but the item to be selected might be inside, recurse
                if element[3]:
                    marked = self.__mark_tree(element[3], idx, False)
                    # Partially select the folder if it contains files that were selected
                    if marked > 0:
                        self.marked[element[1]] = marked
                else:
                    if element[1] in self.marked:
                        # It's not the element we want but it's marked so count it
                        marked = 1
            # Count and then return total amount of files selected in all subdirectories
            total_marked += marked

        return total_marked

    def __get_file_by_num(self, num, file_list, idx=0):
        for element in file_list:
            if idx == num:
                return element

            if element[3] and element[4]:
                i = self.__get_file_by_num(num, element[3], idx + 1)
                if not isinstance(i, int):
                    return i
                else:
                    idx = i
            else:
                idx += 1

        return idx

    def __get_file_by_name(self, name, file_list, idx=0):
        for element in file_list:
            if element[0].strip("/") == name.strip("/"):
                return element

            if element[3] and element[4]:
                i = self.__get_file_by_name(name, element[3], idx + 1)
                if not isinstance(i, int):
                    return i
                else:
                    idx = i
            else:
                idx += 1

        return idx

    def __unmark_tree(self, file_list, idx, unmark_all=False):
        """
        Given file_list of TorrentDetail and index of file or folder,
        recursively deselects all files contained
        as well as marks folders higher in hierarchy as unselected or partially selected
        """
        total_marked = 0
        for element in file_list:
            marked = 0
            # It's either the item we want to select or
            # a contained item, deselect it
            if (element[1] == idx) or unmark_all:
                if element[1] in self.marked:
                    del self.marked[element[1]]
                    # Deselect all contents if it's a catalog
                    if element[3]:
                        self.__unmark_tree(element[3], idx, True)
            else:
                # Not file we wanted but it might be inside this folder, recurse inside
                if element[3]:
                    marked = self.__unmark_tree(element[3], idx, False)
                    # If none of the contents remain selected, unselect this folder as well
                    if marked == 0:
                        if element[1] in self.marked:
                            del self.marked[element[1]]
                    # Otherwise update selection count
                    else:
                        self.marked[element[1]] = marked
                else:
                    if element[1] in self.marked:
                        marked = 1

            # Count and then return selection count so we can update
            # directories higher up in the hierarchy
            total_marked += marked
        return total_marked

    def _selection_to_file_idx(self, file_list=None, idx=0, true_idx=0, closed=False):
        if not file_list:
            file_list = self.file_list

        for element in file_list:
            if idx == self.current_file_idx:
                return true_idx

            # It's a folder
            if element[3]:
                i = self._selection_to_file_idx(element[3], idx + 1, true_idx, closed or not element[4])
                if isinstance(i, tuple):
                    idx, true_idx = i
                    if element[4]:
                        idx, true_idx = i
                    else:
                        idx += 1
                        _, true_idx = i
                else:
                    return i
            else:
                if not closed:
                    idx += 1
                true_idx += 1

        return (idx, true_idx)

    def _get_full_folder_path(self, num, file_list=None, path="", idx=0):
        if not file_list:
            file_list = self.file_list

        for element in file_list:
            if not element[3]:
                idx += 1
                continue

            if num == idx:
                return "%s%s/" % (path, element[0])

            if element[4]:
                i = self._get_full_folder_path(num, element[3], path + element[0] + "/", idx + 1)
                if not isinstance(i, int):
                    return i
                else:
                    idx = i
            else:
                idx += 1

        return idx

    def _do_rename_folder(self, torrent_id, folder, new_folder):
        client.core.rename_folder(torrent_id, folder, new_folder)

    def _do_rename_file(self, torrent_id, file_idx, new_filename):
        if not new_filename:
            return
        client.core.rename_files(torrent_id, [(file_idx, new_filename)])

    def _show_rename_popup(self):
        # Perhaps in the future: Renaming multiple files
        if self.marked:
            title = "Error (Enter to close)"
            text = "Sorry, you can't rename multiple files, please clear selection with {!info!}'c'{!normal!} key"
            self.popup = MessagePopup(self, title, text)
        else:
            _file = self.__get_file_by_num(self.current_file_idx, self.file_list)
            old_filename = _file[0]

            idx = self._selection_to_file_idx()
            tid = self.torrentid

            if _file[3]:

                def do_rename(result):
                    if not result["new_foldername"]:
                        return
                    old_fname = self._get_full_folder_path(self.current_file_idx)
                    new_fname = "%s/%s/" % (old_fname.strip("/").rpartition("/")[0], result["new_foldername"])
                    self._do_rename_folder(tid, old_fname, new_fname)

                popup = InputPopup(self, "Rename folder (Esc to cancel)", close_cb=do_rename)
                popup.add_text("{!info!}Renaming folder:{!input!}")
                popup.add_text(" * %s\n" % old_filename)
                popup.add_text_input("Enter new folder name:", "new_foldername", old_filename.strip("/"))

                self.popup = popup
            else:

                def do_rename(result):
                    fname = "%s/%s" % (self.full_names[idx].rpartition("/")[0], result["new_filename"])
                    self._do_rename_file(tid, idx, fname)

                popup = InputPopup(self, "Rename file (Esc to cancel)", close_cb=do_rename)
                popup.add_text("{!info!}Renaming file:{!input!}")
                popup.add_text(" * %s\n" % old_filename)
                popup.add_text_input("Enter new filename:", "new_filename", old_filename)

                self.popup = popup

    def read_input(self):
        c = self.stdscr.getch()

        if self.popup:
            if self.popup.handle_read(c):
                self.popup = None
            self.refresh()
            return

        if c > 31 and c < 256:
            if chr(c) == "Q":
                from twisted.internet import reactor
                if client.connected():
                    def on_disconnect(result):
                        reactor.stop()
                    client.disconnect().addCallback(on_disconnect)
                else:
                    reactor.stop()
                return
            elif chr(c) == "q":
                self.back_to_overview()
                return

        if c == 27 or c == curses.KEY_LEFT:
            self.back_to_overview()
            return

        if not self.torrent_state:
            # actions below only make sense if there is a torrent state
            return

        # Navigate the torrent list
        if c == curses.KEY_UP:
            self.file_list_up()
        elif c == curses.KEY_PPAGE:
            self.file_list_up(self._listing_space - 2)
        elif c == curses.KEY_HOME:
            self.file_off = 0
            self.current_file_idx = 0
        elif c == curses.KEY_DOWN:
            self.file_list_down()
        elif c == curses.KEY_NPAGE:
            self.file_list_down(self._listing_space - 2)
        elif c == curses.KEY_END:
            self.current_file_idx = self.__get_file_list_length() - 1
            self.file_off = self.current_file_idx - (self._listing_space - 3)
        elif c == curses.KEY_DC:
            torrent_actions_popup(self, [self.torrentid], action=ACTION.REMOVE)
        # Enter Key
        elif c == curses.KEY_ENTER or c == 10:
            was_empty = (self.marked == {})
            self.__mark_tree(self.file_list, self.current_file[1])
            self.show_priority_popup(was_empty)

        # space
        elif c == 32:
            self.expcol_cur_file()
        else:
            if c > 31 and c < 256:
                if chr(c) == "m":
                    if self.current_file:
                        self.__mark_unmark(self.current_file[1])
                elif chr(c) == "r":
                    self._show_rename_popup()
                elif chr(c) == "c":
                    self.marked = {}
                elif chr(c) == "a":
                    torrent_actions_popup(self, [self.torrentid], details=False)
                    return
                elif chr(c) == "o":
                    torrent_actions_popup(self, [self.torrentid], action=ACTION.TORRENT_OPTIONS)
                    return
                elif chr(c) == "h":
                    self.popup = MessagePopup(self, "Help", HELP_STR, width_req=0.75)
                elif chr(c) == "j":
                    self.file_list_up()
                if chr(c) == "k":
                    self.file_list_down()

        self.refresh()
