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

import deluge.common
import deluge.component as component
import deluge.ui.console.modes.column
from deluge.configmanager import ConfigManager
from deluge.ui.client import client
from deluge.ui.console.modes import format_utils
from deluge.ui.console.modes.addtorrents import AddTorrents
from deluge.ui.console.modes.basemode import BaseMode
from deluge.ui.console.modes.eventview import EventView
from deluge.ui.console.modes.input_popup import InputPopup
from deluge.ui.console.modes.legacy import Legacy
from deluge.ui.console.modes.popup import MessagePopup, Popup, SelectablePopup
from deluge.ui.console.modes.preferences import Preferences
from deluge.ui.console.modes.torrent_actions import ACTION, torrent_actions_popup
from deluge.ui.console.modes.torrentdetail import TorrentDetail

try:
    import curses
except ImportError:
    pass

log = logging.getLogger(__name__)


# Big help string that gets displayed when the user hits 'h'
HELP_STR = """\
This screen shows an overview of the current torrents Deluge is managing. \
The currently selected torrent is indicated with a white background. \
You can change the selected torrent using the up/down arrows or the \
PgUp/PgDown keys.  Home and End keys go to the first and last torrent \
respectively.

Operations can be performed on multiple torrents by marking them and \
then hitting Enter.  See below for the keys used to mark torrents.

You can scroll a popup window that doesn't fit its content (like \
this one) using the up/down arrows, PgUp/PgDown and Home/End keys.

All popup windows can be closed/canceled by hitting the Esc key \
(you might need to wait a second for an Esc to register) \
or the 'q' key (does not work for dialogs like the add torrent dialog)

The actions you can perform and the keys to perform them are as follows:

{!info!}'h'{!normal!} - Show this help

{!info!}'p'{!normal!} - View/Set preferences
{!info!}'l'{!normal!} - Enter Legacy mode(command line mode)
{!info!}'e'{!normal!} - Show the event log view ({!info!}'q'{!normal!} to go back to overview)

{!info!}'a'{!normal!} - Add a torrent
{!info!}Delete{!normal!} - Delete a torrent

{!info!}'/'{!normal!} - Search torrent names.\
  Searching starts immediately - matching torrents are highlighted in\
  green, you can cycle through them with Up/Down arrows and Home/End keys\
  You can view torrent details with right arrow, open action popup with\
  Enter key and exit search mode with '/' key, left arrow or\
  backspace with empty search field

{!info!}'f'{!normal!} - Show only torrents in a certain state
      (Will open a popup where you can select the state you want to see)

{!info!}'i'{!normal!} - Show more detailed information about the currently selected torrent

{!info!}Enter{!normal!} - Show torrent actions popup.  Here you can do things like \
  pause/resume, remove, recheck and so on.  These actions \
  apply to all currently marked torrents.  The currently \
  selected torrent is automatically marked when you press enter.

{!info!}'o'{!normal!} - Show and set torrent options - this will either apply\
  to all selected torrents(but not the highlighted one) or currently\
  selected torrent if nothing is selected

{!info!}'Q'{!normal!} - quit deluge-console

{!info!}'m'{!normal!} - Mark a torrent
{!info!}'M'{!normal!} - Mark all torrents between currently selected torrent and last marked torrent
{!info!}'c'{!normal!} - Clear selection

{!info!}'v'{!normal!} - Show a dialog which allows you to choose columns to display
{!info!}'<'/'>'{!normal!} - Change column by which to sort torrents

{!info!}Right Arrow{!normal!} - Torrent Detail Mode.  This includes more detailed information \
about the currently selected torrent, as well as a view of the \
files in the torrent and the ability to set file priorities.

{!info!}'q'/Esc{!normal!} - Close a popup (Note that Esc can take a moment to register \
  as having been pressed and 'q' does not work for dialogs where you\
  input something
"""

STATE_FILTER = {
    "all": 0,
    "active": 1,
    "downloading": 2,
    "seeding": 3,
    "paused": 4,
    "checking": 5,
    "error": 6,
    "queued": 7,
    "allocating": 8,
    "moving": 9
}

DEFAULT_PREFS = {
    "show_queue": True,
    "show_size": True,
    "show_state": False,
    "show_progress": True,
    "show_seeds": False,
    "show_peers": False,
    "show_downspeed": True,
    "show_upspeed": True,
    "show_eta": True,
    "show_ratio": False,
    "show_avail": False,
    "show_added": False,
    "show_tracker": False,
    "show_savepath": False,
    "show_downloaded": False,
    "show_uploaded": False,
    "show_remaining": False,
    "show_owner": False,
    "show_downloading_time": False,
    "show_seeding_time": False,
    "show_completed": False,
    "show_seeds_peers_ratio": False,
    "show_complete_seen": False,
    "show_down_limit": False,
    "show_up_limit": False,
    "show_shared": False,
    "queue_width": 4,
    "name_width": -1,
    "size_width": 8,
    "state_width": 13,
    "progress_width": 7,
    "seeds_width": 10,
    "peers_width": 10,
    "downspeed_width": 7,
    "upspeed_width": 7,
    "eta_width": 8,
    "ratio_width": 10,
    "avail_width": 10,
    "added_width": 15,
    "tracker_width": 15,
    "savepath_width": 15,
    "downloaded_width": 13,
    "uploaded_width": 13,
    "remaining_width": 13,
    "owner_width": 10,
    "downloading_time_width": 10,
    "seeding_time_width": 10,
    "completed_width": 15,
    "seeds_peers_ratio_width": 10,
    "complete_seen_width": 15,
    "down_limit_width": 7,
    "up_limit_width": 7,
    "shared_width": 10,
    "ignore_duplicate_lines": False,
    "move_selection": True,
    "third_tab_lists_all": False,
    "torrents_per_tab_press": 15,
    "sort_primary": "queue",
    "sort_secondary": "name",
    "separate_complete": True,
    "ring_bell": False,
    "save_legacy_history": True,
    "first_run": True,
    "addtorrents_show_misc_files": False,  # TODO: Showing/hiding this
    "addtorrents_show_hidden_folders": False,  # TODO: Showing/hiding this
    "addtorrents_sort_column": "date",
    "addtorrents_reverse_sort": True,
    "addtorrents_last_path": "~"
}

column_pref_names = ["queue", "name", "size", "state", "progress", "seeds",
                     "peers", "downspeed", "upspeed", "eta", "ratio", "avail",
                     "added", "tracker", "savepath", "downloaded", "uploaded",
                     "remaining", "owner", "downloading_time", "seeding_time",
                     "completed", "seeds_peers_ratio", "complete_seen",
                     "down_limit", "up_limit", "shared",
                     ]

prefs_to_names = {
    "queue": "#",
    "name": "Name",
    "size": "Size",
    "state": "State",
    "progress": "Progress",
    "seeds": "Seeds",
    "peers": "Peers",
    "downspeed": "Down Speed",
    "upspeed": "Up Speed",
    "eta": "ETA",
    "ratio": "Ratio",
    "avail": "Avail",
    "added": "Added",
    "tracker": "Tracker",
    "savepath": "Download Folder",
    "downloaded": "Downloaded",
    "uploaded": "Uploaded",
    "remaining": "Remaining",
    "owner": "Owner",
    "seeding_time": "Seeding Time",
    "downloading_time": "Active Time",
    "complete_seen": "Complete Seen",
    "completed": "Completed",
    "seeds_peers_ratio": "Seeds:Peers",
    "down_limit": "Down Limit",
    "up_limit": "Up Limit",
    "shared": "Shared"
}

column_names_to_state_keys = {
    "size": "total_wanted",
    "downspeed": "download_payload_rate",
    "upspeed": "upload_payload_rate",
    "seeds": "num_seeds",
    "peers": "num_peers",
    "avail": "distributed_copies",
    "added": "time_added",
    "tracker": "tracker_host",
    "savepath": "download_location",
    "uploaded": "total_uploaded",
    "downloaded": "all_time_download",
    "remaining": "total_remaining",
    "seeding_time": "seeding_time",
    "downloading_time": "active_time",
    "complete_seen": "last_seen_complete",
    "completed": "completed_time",
    "seeds_peers_ratio": "seeds_peers_ratio",
    "down_limit": "max_download_speed",
    "up_limit": "max_upload_speed",
    "shared": "shared"
}

reverse_sort_fields = [
    "total_wanted",
    "download_payload_rate",
    "upload_payload_rate",
    "num_seeds",
    "num_peers",
    "distributed_copies",
    "time_added",
    "total_uploaded",
    "all_time_download",
    "total_remaining",
    "progress",
    "ratio",
    "seeding_time",
    "active_time"
]

SEARCH_EMPTY = 0
SEARCH_FAILING = 1
SEARCH_SUCCESS = 2
SEARCH_START_REACHED = 3
SEARCH_END_REACHED = 4


class AllTorrents(BaseMode, component.Component):
    def __init__(self, stdscr, encoding=None):
        self.torrent_names = None
        self.numtorrents = -1
        self._cached_rows = {}
        self.cursel = 1
        self.curoff = 1  # TODO: this should really be 0 indexed
        self.column_string = ""
        self.popup = None
        self.messages = deque()
        self.marked = []
        self.last_mark = -1
        self._sorted_ids = None
        self._go_top = False

        self._curr_filter = None
        self.entering_search = False
        self.search_string = None
        self.search_state = SEARCH_EMPTY

        self.coreconfig = component.get("ConsoleUI").coreconfig

        self.legacy_mode = None

        self.__status_dict = {}
        self.__torrent_info_id = None

        BaseMode.__init__(self, stdscr, encoding)
        component.Component.__init__(self, "AllTorrents", 1, depend=["SessionProxy"])
        curses.curs_set(0)
        self.stdscr.notimeout(0)

        self.update_config()

        component.start(["AllTorrents"])

        self._info_fields = [
            ("Name", None, ("name",)),
            ("State", None, ("state",)),
            ("Down Speed", format_utils.format_speed, ("download_payload_rate",)),
            ("Up Speed", format_utils.format_speed, ("upload_payload_rate",)),
            ("Progress", format_utils.format_progress, ("progress",)),
            ("ETA", deluge.common.ftime, ("eta",)),
            ("Download Folder", None, ("download_location",)),
            ("Downloaded", deluge.common.fsize, ("all_time_download",)),
            ("Uploaded", deluge.common.fsize, ("total_uploaded",)),
            ("Share Ratio", format_utils.format_float, ("ratio",)),
            ("Seeds", format_utils.format_seeds_peers, ("num_seeds", "total_seeds")),
            ("Peers", format_utils.format_seeds_peers, ("num_peers", "total_peers")),
            ("Active Time", deluge.common.ftime, ("active_time",)),
            ("Seeding Time", deluge.common.ftime, ("seeding_time",)),
            ("Complete Seen", format_utils.format_date_never, ("last_seen_complete",)),
            ("Date Added", format_utils.format_time, ("time_added",)),
            ("Completed", format_utils.format_date, ("completed_time",)),
            ("Availability", format_utils.format_float, ("distributed_copies",)),
            ("Pieces", format_utils.format_pieces, ("num_pieces", "piece_length")),
            ("Seed Rank", str, ("seed_rank",)),
        ]

        self.__status_keys = ["name", "state", "download_payload_rate", "upload_payload_rate",
                              "progress", "eta", "download_location", "all_time_download", "total_uploaded",
                              "ratio", "num_seeds", "total_seeds", "num_peers", "total_peers",
                              "active_time", "seeding_time", "last_seen_complete", "time_added",
                              "completed_time", "distributed_copies", "num_pieces", "piece_length",
                              "seed_rank"
                              ]

        self.legacy_mode = Legacy(self.stdscr, self.encoding)

        if self.config["first_run"]:
            self.popup = MessagePopup(self, "Welcome to Deluge", HELP_STR, width_req=0.75)
            self.config["first_run"] = False
            self.config.save()

    # component start/update
    def start(self):
        component.get("SessionProxy").get_torrents_status(self.__status_dict, self.__status_fields
                                                          ).addCallback(self.set_state, False)

    def update(self):
        component.get("SessionProxy").get_torrents_status(self.__status_dict, self.__status_fields
                                                          ).addCallback(self.set_state, True)
        if self.__torrent_info_id:
            component.get("SessionProxy").get_torrent_status(self.__torrent_info_id, self.__status_keys
                                                             ).addCallback(self._on_torrent_status)

    def update_config(self):
        self.config = ConfigManager("console.conf", DEFAULT_PREFS)
        s_primary = self.config["sort_primary"]
        s_secondary = self.config["sort_secondary"]
        self.__cols_to_show = [pref for pref in column_pref_names
                               if ("show_%s" % pref) not in self.config or self.config["show_%s" % pref]]

        self.__columns = [prefs_to_names[col] for col in self.__cols_to_show]
        self.__status_fields = deluge.ui.console.modes.column.get_required_fields(self.__columns)

        # we always need these, even if we're not displaying them
        for rf in ["state", "name", "queue", "progress"]:
            if rf not in self.__status_fields:
                self.__status_fields.append(rf)

        # same with sort keys
        if s_primary and (s_primary not in self.__status_fields):
            self.__status_fields.append(s_primary)
        if s_secondary and (s_secondary not in self.__status_fields):
            self.__status_fields.append(s_secondary)

        self.__update_columns()

    def resume(self):
        component.start(["AllTorrents"])
        self.refresh()

    def __update_columns(self):
        self.column_widths = [self.config["%s_width" % c] for c in self.__cols_to_show]
        requested_width = sum([width for width in self.column_widths if width >= 0])
        if requested_width > self.cols:  # can't satisfy requests, just spread out evenly
            cw = int(self.cols / len(self.__columns))
            for i in range(0, len(self.column_widths)):
                self.column_widths[i] = cw
        else:
            rem = self.cols - requested_width
            var_cols = len([width for width in self.column_widths if width < 0])
            if var_cols > 0:
                vw = int(rem / var_cols)
                for i in range(0, len(self.column_widths)):
                    if self.column_widths[i] < 0:
                        self.column_widths[i] = vw

        self.column_string = "{!header!}"

        try:
            primary_sort_col_name = prefs_to_names[self.config["sort_primary"]]
        except KeyError:
            primary_sort_col_name = ""

        for i, column in enumerate(self.__columns):
            ccol = column
            width = self.column_widths[i]

            # Trim the column if it's too long to fit
            if len(ccol) > width:
                ccol = ccol[:width - 1]

            # Padding
            ccol += " " * (width - len(ccol))

            # Highlight the primary sort column
            if column == primary_sort_col_name:
                if i != len(self.__columns) - 1:
                    ccol = "{!black,green,bold!}%s{!header!}" % ccol
                else:
                    ccol = ("{!black,green,bold!}%s" % ccol)[:-1]

            self.column_string += ccol

    def set_state(self, state, refresh):
        self.curstate = state  # cache in case we change sort order
        newnames = []
        self._cached_rows = {}
        self._sorted_ids = self._sort_torrents(self.curstate)
        for torrent_id in self._sorted_ids:
            ts = self.curstate[torrent_id]
            newnames.append(ts["name"])

        self.numtorrents = len(state)
        self.torrent_names = newnames
        if refresh:
            self.refresh()

    def get_torrent_name(self, torrent_id):
        for p, i in enumerate(self._sorted_ids):
            if torrent_id == i:
                return self.torrent_names[p]
        return None

    def _scroll_up(self, by):
        prevoff = self.curoff
        self.cursel = max(self.cursel - by, 1)
        if (self.cursel - 1) < self.curoff:
            self.curoff = max(self.cursel - 1, 1)
        return prevoff != self.curoff

    def _scroll_down(self, by):
        prevoff = self.curoff
        self.cursel = min(self.cursel + by, self.numtorrents)
        if (self.curoff + self.rows - 5) < self.cursel:
            self.curoff = self.cursel - self.rows + 5
        return prevoff != self.curoff

    def current_torrent_id(self):
        if self._sorted_ids:
            return self._sorted_ids[self.cursel - 1]
        else:
            return None

    def _selected_torrent_ids(self):
        ret = []
        for i in self.marked:
            ret.append(self._sorted_ids[i - 1])
        return ret

    def _on_torrent_status(self, state):
        if self.popup:
            self.popup.clear()
            name = state["name"]
            self.popup.set_title(name)
            for i, f in enumerate(self._info_fields):
                if f[1] is not None:
                    args = []
                    try:
                        for key in f[2]:
                            args.append(state[key])
                    except Exception as ex:
                        log.debug("Could not get info field: %s", ex)
                        continue
                    info = f[1](*args)
                else:
                    info = state[f[2][0]]

                nl = len(f[0]) + 4
                if (nl + len(info)) > self.popup.width:
                    self.popup.add_line("{!info!}%s: {!input!}%s" % (f[0], info[:(self.popup.width - nl)]))
                    info = info[(self.popup.width - nl):]
                    n = self.popup.width - 3
                    chunks = [info[i:i + n] for i in xrange(0, len(info), n)]
                    for c in chunks:
                        self.popup.add_line(" %s" % c)
                else:
                    self.popup.add_line("{!info!}%s: {!input!}%s" % (f[0], info))
            self.refresh()
        else:
            self.__torrent_info_id = None

    def on_resize(self, *args):
        BaseMode.on_resize_norefresh(self, *args)
        if self.popup:
            self.popup.handle_resize()

        self.update()
        self.__update_columns()

        self.refresh([])

    def _queue_sort(self, v1, v2):
        if v1 == v2:
            return 0
        if v2 < 0:
            return -1
        if v1 < 0:
            return 1
        if v1 > v2:
            return 1
        if v2 > v1:
            return -1

    def _sort_torrents(self, state):
        "sorts by primary and secondary sort fields"

        if not state:
            return {}

        s_primary = self.config["sort_primary"]
        s_secondary = self.config["sort_secondary"]

        result = state

        # Sort first by secondary sort field and then primary sort field
        # so it all works out

        cmp_func = self._queue_sort

        sg = state.get

        def sort_by_field(state, result, field):
            if field in column_names_to_state_keys:
                field = column_names_to_state_keys[field]

            reverse = field in reverse_sort_fields

            # Get first element so we can check if it has given field
            # and if it's a string
            first_element = state[state.keys()[0]]
            if field in first_element:
                is_string = isinstance(first_element[field], basestring)

                def sort_key(s):
                    return sg(s)[field]

                def sort_key2(s):
                    return sg(s)[field].lower()

                # If it's a string, sort case-insensitively but preserve A>a order
                if is_string:
                    result = sorted(result, cmp_func, sort_key, reverse)
                    result = sorted(result, cmp_func, sort_key2, reverse)
                else:
                    result = sorted(result, cmp_func, sort_key, reverse)

            if field == "eta":
                result = sorted(result, key=lambda s: state.get(s)["eta"] == 0)

            return result

        # Just in case primary and secondary fields are empty and/or
        # both are too ambiguous, also sort by queue position first
        if "queue" not in [s_secondary, s_primary]:
            result = sort_by_field(state, result, "queue")
        if s_secondary != s_primary:
            result = sort_by_field(state, result, s_secondary)
        result = sort_by_field(state, result, s_primary)

        if self.config["separate_complete"]:
            result = sorted(result, cmp_func, lambda s: state.get(s)["progress"] == 100.0)

        return result

    def _format_queue(self, qnum):
        if qnum >= 0:
            return "%d" % (qnum + 1)
        else:
            return ""

    def show_addtorrents_screen(self):
        def dodeets(arg):
            if arg and True in arg[0]:
                self.stdscr.erase()
                component.get("ConsoleUI").set_mode(AddTorrents(self, self.stdscr, self.config, self.encoding))
            else:
                self.messages.append(("Error", "An error occurred trying to display add torrents screen"))
        component.stop(["AllTorrents"]).addCallback(dodeets)

    def show_torrent_details(self, tid):
        def dodeets(arg):
            if arg and True in arg[0]:
                self.stdscr.erase()
                component.get("ConsoleUI").set_mode(TorrentDetail(self, tid, self.stdscr, self.config, self.encoding))
            else:
                self.messages.append(("Error", "An error occurred trying to display torrent details"))
        component.stop(["AllTorrents"]).addCallback(dodeets)

    def show_preferences(self):
        def _on_get_config(config):
            client.core.get_listen_port().addCallback(_on_get_listen_port, config)

        def _on_get_listen_port(port, config):
            client.core.get_cache_status().addCallback(_on_get_cache_status, port, config)

        def _on_get_cache_status(status, port, config):
            def doprefs(arg):
                if arg and True in arg[0]:
                    self.stdscr.erase()
                    component.get("ConsoleUI").set_mode(Preferences(self, config, self.config, port,
                                                                    status, self.stdscr, self.encoding))
                else:
                    self.messages.append(("Error", "An error occurred trying to display preferences"))
            component.stop(["AllTorrents"]).addCallback(doprefs)

        client.core.get_config().addCallback(_on_get_config)

    def __show_events(self):
        def doevents(arg):
            if arg and True in arg[0]:
                self.stdscr.erase()
                component.get("ConsoleUI").set_mode(EventView(self, self.stdscr, self.encoding))
            else:
                self.messages.append(("Error", "An error occurred trying to display events"))
        component.stop(["AllTorrents"]).addCallback(doevents)

    def __legacy_mode(self):
        def dolegacy(arg):
            if arg and True in arg[0]:
                self.stdscr.erase()
                component.get("ConsoleUI").set_mode(self.legacy_mode)
                self.legacy_mode.refresh()
                curses.curs_set(2)
            else:
                self.messages.append(("Error", "An error occurred trying to switch to legacy mode"))
        component.stop(["AllTorrents"]).addCallback(dolegacy)

    def _torrent_filter(self, idx, data):
        if data == STATE_FILTER["all"]:
            self.__status_dict = {}
            self._curr_filter = None
        elif data == STATE_FILTER["active"]:
            self.__status_dict = {"state": "Active"}
            self._curr_filter = "Active"
        elif data == STATE_FILTER["downloading"]:
            self.__status_dict = {"state": "Downloading"}
            self._curr_filter = "Downloading"
        elif data == STATE_FILTER["seeding"]:
            self.__status_dict = {"state": "Seeding"}
            self._curr_filter = "Seeding"
        elif data == STATE_FILTER["paused"]:
            self.__status_dict = {"state": "Paused"}
            self._curr_filter = "Paused"
        elif data == STATE_FILTER["checking"]:
            self.__status_dict = {"state": "Checking"}
            self._curr_filter = "Checking"
        elif data == STATE_FILTER["error"]:
            self.__status_dict = {"state": "Error"}
            self._curr_filter = "Error"
        elif data == STATE_FILTER["queued"]:
            self.__status_dict = {"state": "Queued"}
            self._curr_filter = "Queued"
        elif data == STATE_FILTER["allocating"]:
            self.__status_dict = {"state": "Allocating"}
            self._curr_filter = "Allocating"
        elif data == STATE_FILTER["moving"]:
            self.__status_dict = {"state": "Moving"}
            self._curr_filter = "Moving"

        self._go_top = True
        return True

    def _show_torrent_filter_popup(self):
        self.popup = SelectablePopup(self, "Filter Torrents", self._torrent_filter)
        self.popup.add_line("_All", data=STATE_FILTER["all"])
        self.popup.add_line("Ac_tive", data=STATE_FILTER["active"])
        self.popup.add_line("_Downloading", data=STATE_FILTER["downloading"], foreground="green")
        self.popup.add_line("_Seeding", data=STATE_FILTER["seeding"], foreground="cyan")
        self.popup.add_line("_Paused", data=STATE_FILTER["paused"])
        self.popup.add_line("_Error", data=STATE_FILTER["error"], foreground="red")
        self.popup.add_line("_Checking", data=STATE_FILTER["checking"], foreground="blue")
        self.popup.add_line("Q_ueued", data=STATE_FILTER["queued"], foreground="yellow")
        self.popup.add_line("A_llocating", data=STATE_FILTER["allocating"], foreground="yellow")
        self.popup.add_line("_Moving", data=STATE_FILTER["moving"], foreground="green")

    def _report_add_status(self, succ_cnt, fail_cnt, fail_msgs):
        if fail_cnt == 0:
            self.report_message("Torrents Added", "{!success!}Successfully added %d torrent(s)" % succ_cnt)
        else:
            msg = ("{!error!}Failed to add the following %d torrent(s):\n {!input!}" % fail_cnt) + "\n ".join(fail_msgs)
            if succ_cnt != 0:
                msg += "\n \n{!success!}Successfully added %d torrent(s)" % succ_cnt
            self.report_message("Torrent Add Report", msg)

    def _show_torrent_add_popup(self):

        def do_add_from_url(result):
            def fail_cb(msg, url):
                log.debug("failed to add torrent: %s: %s", url, msg)
                error_msg = "{!input!} * %s: {!error!}%s" % (url, msg)
                self._report_add_status(0, 1, [error_msg])

            def success_cb(tid, url):
                if tid:
                    log.debug("added torrent: %s (%s)", url, tid)
                    self._report_add_status(1, 0, [])
                else:
                    fail_cb("Already in session (probably)", url)

            url = result["url"]

            if not url:
                return

            t_options = {
                "download_location": result["path"],
                "add_paused": result["add_paused"]
            }

            if deluge.common.is_magnet(url):
                client.core.add_torrent_magnet(url, t_options).addCallback(success_cb, url).addErrback(fail_cb, url)
            elif deluge.common.is_url(url):
                client.core.add_torrent_url(url, t_options).addCallback(success_cb, url).addErrback(fail_cb, url)
            else:
                self.messages.append(("Error", "{!error!}Invalid URL or magnet link: %s" % url))
                return

            log.debug("Adding Torrent(s): %s (dl path: %s) (paused: %d)", url, result["path"], result["add_paused"])

        def show_add_url_popup():
            try:
                dl = self.coreconfig["download_location"]
            except KeyError:
                dl = ""

            ap = 1

            try:
                if self.coreconfig["add_paused"]:
                    ap = 0
            except KeyError:
                pass

            self.popup = InputPopup(self, "Add Torrent (Esc to cancel)", close_cb=do_add_from_url)
            self.popup.add_text_input("Enter torrent URL or Magnet link:", "url")
            self.popup.add_text_input("Enter save path:", "path", dl)
            self.popup.add_select_input("Add Paused:", "add_paused", ["Yes", "No"], [True, False], ap)

        def option_chosen(index, data):
            self.popup = None

            if not data:
                return
            if data == 1:
                self.show_addtorrents_screen()
            elif data == 2:
                show_add_url_popup()

        self.popup = SelectablePopup(self, "Add torrent", option_chosen)
        self.popup.add_line("From _File(s)", data=1)
        self.popup.add_line("From _URL or Magnet", data=2)
        self.popup.add_line("_Cancel", data=0)

    def _do_set_column_visibility(self, data):
        for key, value in data.items():
            self.config[key] = value
        self.config.save()
        self.update_config()
        self.__update_columns()
        self.refresh([])

    def _show_visible_columns_popup(self):
        title = "Visible columns (Enter to exit)"
        self.popup = InputPopup(self, title, close_cb=self._do_set_column_visibility,
                                immediate_action=True, height_req=len(column_pref_names) + 1,
                                width_req=max([len(col) for col in column_pref_names + [title]]) + 8)

        for col in column_pref_names:
            name = prefs_to_names[col]
            prop = "show_%s" % col
            if prop not in self.config:
                continue
            state = self.config[prop]

            self.popup.add_checked_input(name, prop, state)

    def report_message(self, title, message):
        self.messages.append((title, message))

    def clear_marks(self):
        self.marked = []
        self.last_mark = -1

    def set_popup(self, pu):
        self.popup = pu
        self.refresh()

    def refresh(self, lines=None):
        # log.error("ref")
        # import traceback
        # traceback.print_stack()
        # Something has requested we scroll to the top of the list
        if self._go_top:
            self.cursel = 1
            self.curoff = 1
            self._go_top = False

        # show a message popup if there's anything queued
        if self.popup is None and self.messages:
            title, msg = self.messages.popleft()
            self.popup = MessagePopup(self, title, msg, width_req=1.0)

        if not lines:
            if component.get("ConsoleUI").screen != self:
                return
            self.stdscr.erase()

        # Update the status bars
        if self._curr_filter is None:
            self.add_string(0, self.statusbars.topbar)
        else:
            self.add_string(0, "%s    {!filterstatus!}Current filter: %s" % (self.statusbars.topbar, self._curr_filter))
        self.add_string(1, self.column_string)

        if self.entering_search:
            string = {
                SEARCH_EMPTY: "{!black,white!}Search torrents: %s{!black,white!}",
                SEARCH_SUCCESS: "{!black,white!}Search torrents: {!black,green!}%s{!black,white!}",
                SEARCH_FAILING: "{!black,white!}Search torrents: {!black,red!}%s{!black,white!}",
                SEARCH_START_REACHED:
                "{!black,white!}Search torrents: {!black,yellow!}%s{!black,white!} (start reached)",
                SEARCH_END_REACHED: "{!black,white!}Search torrents: {!black,yellow!}%s{!black,white!} (end reached)"
            }[self.search_state] % self.search_string

            self.add_string(self.rows - 1, string)
        else:
            # This will quite likely fail when switching modes
            try:
                rf = format_utils.remove_formatting
                string = self.statusbars.bottombar
                hstr = "Press {!magenta,blue,bold!}[h]{!status!} for help"

                string += " " * (self.cols - len(rf(string)) - len(rf(hstr))) + hstr

                self.add_string(self.rows - 1, string)
            except Exception:
                pass

        # add all the torrents
        if self.numtorrents == 0:
            msg = "No torrents match filter".center(self.cols)
            self.add_string(3, "{!info!}%s" % msg)
        elif self.numtorrents > 0:
            tidx = self.curoff
            currow = 2

            # Because dots are slow
            sorted_ids = self._sorted_ids
            curstate = self.curstate
            gcv = deluge.ui.console.modes.column.get_column_value
            fr = format_utils.format_row
            cols = self.__columns
            colw = self.column_widths
            cr = self._cached_rows

            def draw_row(index):
                if index not in cr:
                    ts = curstate[sorted_ids[index]]
                    cr[index] = (fr([gcv(name, ts) for name in cols], colw), ts["state"])
                return cr[index]

            if lines:
                todraw = []
                for l in lines:
                    if l < tidx - 1:
                        continue
                    if l >= tidx - 1 + self.rows - 3:
                        break
                    if l >= self.numtorrents:
                        break
                    todraw.append(draw_row(l))
                lines.reverse()
            else:
                todraw = []
                for i in range(tidx - 1, tidx - 1 + self.rows - 3):
                    if i >= self.numtorrents:
                        break
                    todraw += [draw_row(i)]

            for row in todraw:
                # default style
                fg = "white"
                bg = "black"
                attr = None
                if lines:
                    tidx = lines.pop() + 1
                    currow = tidx - self.curoff + 2

                if tidx in self.marked:
                    bg = "blue"
                    attr = "bold"

                if tidx == self.cursel:
                    bg = "white"
                    attr = "bold"
                    if tidx in self.marked:
                        fg = "blue"
                    else:
                        fg = "black"

                if row[1] == "Downloading":
                    fg = "green"
                elif row[1] == "Seeding":
                    fg = "cyan"
                elif row[1] == "Error":
                    fg = "red"
                elif row[1] == "Queued":
                    fg = "yellow"
                elif row[1] == "Checking":
                    fg = "blue"
                elif row[1] == "Moving":
                    fg = "green"

                if self.entering_search and len(self.search_string) > 1:
                    lcase_name = self.torrent_names[tidx - 1].lower()
                    sstring_lower = self.search_string.lower()
                    if lcase_name.find(sstring_lower) != -1:
                        if tidx == self.cursel:
                            pass
                        elif tidx in self.marked:
                            bg = "magenta"
                        else:
                            bg = "green"
                            if fg == "green":
                                fg = "black"
                            attr = "bold"

                if attr:
                    colorstr = "{!%s,%s,%s!}" % (fg, bg, attr)
                else:
                    colorstr = "{!%s,%s!}" % (fg, bg)

                try:
                    self.add_string(currow, "%s%s" % (colorstr, row[0]), trim=False)
                except Exception:
                    # XXX: Yeah, this should be fixed in some better way
                    pass
                tidx += 1
                currow += 1
                if currow > (self.rows - 2):
                    break
        else:
            self.add_string(1, "Waiting for torrents from core...")

        # self.stdscr.redrawwin()
        if self.entering_search:
            curses.curs_set(2)
            self.stdscr.move(self.rows - 1, len(self.search_string) + 17)
        else:
            curses.curs_set(0)

        if component.get("ConsoleUI").screen != self:
            return

        self.stdscr.noutrefresh()

        if self.popup:
            self.popup.refresh()

        curses.doupdate()

    def _mark_unmark(self, idx):
        if idx in self.marked:
            self.marked.remove(idx)
            self.last_mark = -1
        else:
            self.marked.append(idx)
            self.last_mark = idx

    def __search_match_count(self):
        match_count = 0

        search_string = self.search_string.lower()

        for n in self.torrent_names:
            n = n.lower()
            if n.find(search_string) != -1:
                match_count += 1

        return match_count

    def __do_search(self, direction="first", skip=0):
        """
        Performs a search on visible torrent and sets cursor to the match

        :param string: direction, the direction of search, can be first, last, next or previous

        :returns: Nothing
        """

        if direction == "first":
            search_space = enumerate(self.torrent_names)
        elif direction == "last":
            search_space = enumerate(self.torrent_names)
            search_space = list(search_space)
            search_space = reversed(search_space)
        elif direction == "next":
            search_space = enumerate(self.torrent_names)
            search_space = list(search_space)
            search_space = search_space[self.cursel:]
        elif direction == "previous":
            search_space = enumerate(self.torrent_names)
            search_space = list(search_space)[:self.cursel - 1]
            search_space = reversed(search_space)

        search_string = self.search_string.lower()
        for i, n in search_space:
            n = n.lower()
            if n.find(search_string) != -1:
                if skip > 0:
                    skip -= 1
                    continue
                self.cursel = (i + 1)
                if (self.curoff + self.rows - 5) < self.cursel:
                    self.curoff = self.cursel - self.rows + 5
                elif (self.curoff + 1) > self.cursel:
                    self.curoff = max(1, self.cursel - 1)
                self.search_state = SEARCH_SUCCESS
                return
        if direction in ["first", "last"]:
            self.search_state = SEARCH_FAILING
        elif direction == "next":
            self.search_state = SEARCH_END_REACHED
        elif direction == "previous":
            self.search_state = SEARCH_START_REACHED

    def __update_search(self, c):
        cname = self.torrent_names[self.cursel - 1]
        if c == curses.KEY_BACKSPACE or c == 127:
            if self.search_string:
                self.search_string = self.search_string[:-1]
                if cname.lower().find(self.search_string.lower()) != -1:
                    self.search_state = SEARCH_SUCCESS
            else:
                self.entering_search = False
                self.search_state = SEARCH_EMPTY

            self.refresh([])

        elif c == curses.KEY_DC:
            self.search_string = ""
            self.search_state = SEARCH_SUCCESS
            self.refresh([])

        elif c == curses.KEY_UP:
            self.__do_search("previous")
            self.refresh([])

        elif c == curses.KEY_DOWN:
            self.__do_search("next")
            self.refresh([])

        elif c == curses.KEY_LEFT:
            self.entering_search = False
            self.search_state = SEARCH_EMPTY
            self.refresh([])

        elif c == ord("/"):
            self.entering_search = False
            self.search_state = SEARCH_EMPTY
            self.refresh([])

        elif c == curses.KEY_RIGHT:
            tid = self.current_torrent_id()
            self.show_torrent_details(tid)

        elif c == curses.KEY_HOME:
            self.__do_search("first")
            self.refresh([])

        elif c == curses.KEY_END:
            self.__do_search("last")
            self.refresh([])

        elif c in [10, curses.KEY_ENTER]:
            self.last_mark = -1
            tid = self.current_torrent_id()
            torrent_actions_popup(self, [tid], details=True)

        elif c == 27:
            self.search_string = ""
            self.search_state = SEARCH_EMPTY
            self.refresh([])

        elif c > 31 and c < 256:
            old_search_string = self.search_string
            stroke = chr(c)
            uchar = ""
            while not uchar:
                try:
                    uchar = stroke.decode(self.encoding)
                except UnicodeDecodeError:
                    c = self.stdscr.getch()
                    stroke += chr(c)

            if uchar:
                self.search_string += uchar

            still_matching = (
                cname.lower().find(self.search_string.lower()) ==
                cname.lower().find(old_search_string.lower()) and
                cname.lower().find(self.search_string.lower()) != -1
            )

            if self.search_string and not still_matching:
                self.__do_search()
            elif self.search_string:
                self.search_state = SEARCH_SUCCESS
            self.refresh([])

        if not self.search_string:
            self.search_state = SEARCH_EMPTY
            self.refresh([])

    def read_input(self):
        # Read the character
        effected_lines = None

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

        if self.numtorrents < 0:
            return

        elif self.entering_search:
            self.__update_search(c)
            return

        if c == curses.KEY_UP:
            if self.cursel == 1:
                return
            if not self._scroll_up(1):
                effected_lines = [self.cursel - 1, self.cursel]
        elif c == curses.KEY_PPAGE:
            self._scroll_up(int(self.rows / 2))
        elif c == curses.KEY_DOWN:
            if self.cursel >= self.numtorrents:
                return
            if not self._scroll_down(1):
                effected_lines = [self.cursel - 2, self.cursel - 1]
        elif c == curses.KEY_NPAGE:
            self._scroll_down(int(self.rows / 2))
        elif c == curses.KEY_HOME:
            self._scroll_up(self.cursel)
        elif c == curses.KEY_END:
            self._scroll_down(self.numtorrents - self.cursel)
        elif c == curses.KEY_DC:
            if self.cursel not in self.marked:
                self.marked.append(self.cursel)
            self.last_mark = self.cursel
            torrent_actions_popup(self, self._selected_torrent_ids(), action=ACTION.REMOVE)

        elif c == curses.KEY_RIGHT:
            # We enter a new mode for the selected torrent here
            tid = self.current_torrent_id()
            if tid:
                self.show_torrent_details(tid)
                return

        # Enter Key
        elif (c == curses.KEY_ENTER or c == 10) and self.numtorrents:
            if self.cursel not in self.marked:
                self.marked.append(self.cursel)
            self.last_mark = self.cursel
            torrent_actions_popup(self, self._selected_torrent_ids(), details=True)
            return
        else:
            if c > 31 and c < 256:
                if chr(c) == "/":
                    self.search_string = ""
                    self.entering_search = True
                elif chr(c) == "n" and self.search_string:
                    self.__do_search("next")
                elif chr(c) == "j":
                    if not self._scroll_up(1):
                        effected_lines = [self.cursel - 1, self.cursel]
                elif chr(c) == "k":
                    if not self._scroll_down(1):
                        effected_lines = [self.cursel - 2, self.cursel - 1]
                elif chr(c) == "i":
                    cid = self.current_torrent_id()
                    if cid:
                        def cb():
                            self.__torrent_info_id = None
                        self.popup = Popup(self, "Info", close_cb=cb, height_req=20)
                        self.popup.add_line("Getting torrent info...")
                        self.__torrent_info_id = cid
                elif chr(c) == "m":
                    self._mark_unmark(self.cursel)
                    effected_lines = [self.cursel - 1]
                elif chr(c) == "M":
                    if self.last_mark >= 0:
                        if (self.cursel + 1) > self.last_mark:
                            mrange = range(self.last_mark, self.cursel + 1)
                        else:
                            mrange = range(self.cursel - 1, self.last_mark)
                        self.marked.extend(mrange[1:])
                        effected_lines = mrange
                    else:
                        self._mark_unmark(self.cursel)
                        effected_lines = [self.cursel - 1]
                elif chr(c) == "c":
                    self.marked = []
                    self.last_mark = -1
                elif chr(c) == "a":
                    self._show_torrent_add_popup()
                elif chr(c) == "v":
                    self._show_visible_columns_popup()
                elif chr(c) == "o":
                    if not self.marked:
                        self.marked = [self.cursel]
                        self.last_mark = self.cursel
                    else:
                        self.last_mark = -1
                    torrent_actions_popup(self, self._selected_torrent_ids(), action=ACTION.TORRENT_OPTIONS)

                elif chr(c) == "<":
                    i = len(self.__cols_to_show)
                    try:
                        i = self.__cols_to_show.index(self.config["sort_primary"]) - 1
                    except KeyError:
                        pass

                    i = max(0, i)
                    i = min(len(self.__cols_to_show) - 1, i)

                    self.config["sort_primary"] = self.__cols_to_show[i]
                    self.config.save()
                    self.update_config()
                    self.__update_columns()
                    self.refresh([])

                elif chr(c) == ">":
                    i = 0
                    try:
                        i = self.__cols_to_show.index(self.config["sort_primary"]) + 1
                    except KeyError:
                        pass

                    i = min(len(self.__cols_to_show) - 1, i)
                    i = max(0, i)

                    self.config["sort_primary"] = self.__cols_to_show[i]
                    self.config.save()
                    self.update_config()
                    self.__update_columns()
                    self.refresh([])

                elif chr(c) == "f":
                    self._show_torrent_filter_popup()
                elif chr(c) == "h":
                    self.popup = MessagePopup(self, "Help", HELP_STR, width_req=0.75)
                elif chr(c) == "p":
                    self.show_preferences()
                    return
                elif chr(c) == "e":
                    self.__show_events()
                    return
                elif chr(c) == "l":
                    self.__legacy_mode()
                    return

        self.refresh(effected_lines)
