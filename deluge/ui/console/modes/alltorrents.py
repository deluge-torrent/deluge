# -*- coding: utf-8 -*-
#
# alltorrens.py
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#
#

import deluge.component as component
from basemode import BaseMode
import deluge.common
from deluge.ui.client import client

from collections import deque

from deluge.ui.sessionproxy import SessionProxy

from popup import Popup,SelectablePopup,MessagePopup
from add_util import add_torrent
from input_popup import InputPopup


try:
    import curses
except ImportError:
    pass

import logging
log = logging.getLogger(__name__)


# Big help string that gets displayed when the user hits 'h'
HELP_STR = \
"""This screen shows an overview of the current torrents Deluge is managing.
The currently selected torrent is indicated by having a white background.
You can change the selected torrent using the up/down arrows or the 
PgUp/Pg keys.

Operations can be performed on multiple torrents by marking them and
then hitting Enter.  See below for the keys used to mark torrents.

You can scroll a popup window that doesn't fit its content (like
this one) using the up/down arrows.

All popup windows can be closed/canceled by hitting the Esc key 
(you might need to wait a second for an Esc to register)

The actions you can perform and the keys to perform them are as follows:

'a' - Add a torrent

'h' - Show this help

'f' - Show only torrents in a certain state
      (Will open a popup where you can select the state you want to see)

'i' - Show more detailed information about the current selected torrent

'Q' - quit

'm' - Mark a torrent
'M' - Mark all torrents between currently selected torrent 
      and last marked torrent
'c' - Un-mark all torrents

Enter - Show torrent actions popup.  Here you can do things like
        pause/resume, remove, recheck and so one.  These actions
        apply to all currently marked torrents.  The currently
        selected torrent is automatically marked when you press enter.

'q'/Esc - Close a popup
"""
HELP_LINES = HELP_STR.split('\n')

class ACTION:
    PAUSE=0
    RESUME=1
    REANNOUNCE=2
    EDIT_TRACKERS=3
    RECHECK=4
    REMOVE=5

class FILTER:
    ALL=0
    ACTIVE=1
    DOWNLOADING=2
    SEEDING=3
    PAUSED=4
    CHECKING=5
    ERROR=6
    QUEUED=7

class StateUpdater(component.Component):
    def __init__(self, cb, sf,tcb):
        component.Component.__init__(self, "AllTorrentsStateUpdater", 1, depend=["SessionProxy"])
        self._status_cb = cb
        self._status_fields = sf
        self.status_dict = {}
        self._torrent_cb = tcb
        self._torrent_to_update = None

    def set_torrent_to_update(self, tid, keys):
        self._torrent_to_update = tid
        self._torrent_keys = keys

    def start(self):
        component.get("SessionProxy").get_torrents_status(self.status_dict, self._status_fields).addCallback(self._on_torrents_status,False)

    def update(self):
        component.get("SessionProxy").get_torrents_status(self.status_dict, self._status_fields).addCallback(self._on_torrents_status,True)
        if self._torrent_to_update:
            component.get("SessionProxy").get_torrent_status(self._torrent_to_update, self._torrent_keys).addCallback(self._torrent_cb)

    def _on_torrents_status(self, state, refresh):
        self._status_cb(state,refresh)


class AllTorrents(BaseMode, component.Component):
    def __init__(self, stdscr, coreconfig, encoding=None):
        self.curstate = None
        self.cursel = 1
        self.curoff = 1
        self.column_string = ""
        self.popup = None
        self.messages = deque()
        self.marked = []
        self.last_mark = -1
        self._sorted_ids = None
        self._go_top = False

        self._curr_filter = None

        self.coreconfig = coreconfig

        BaseMode.__init__(self, stdscr, encoding)
        curses.curs_set(0)
        self.stdscr.notimeout(0)
        self.sessionproxy = SessionProxy()

        self._status_fields = ["queue","name","total_wanted","state","progress","num_seeds","total_seeds",
                               "num_peers","total_peers","download_payload_rate", "upload_payload_rate"]

        self.updater = StateUpdater(self.set_state,self._status_fields,self._on_torrent_status)

        self.column_names = ["#", "Name","Size","State","Progress","Seeders","Peers","Down Speed","Up Speed"]
        self._update_columns()


        self._info_fields = [
            ("Name",None,("name",)),
            ("State", None, ("state",)),
            ("Down Speed", self._format_speed, ("download_payload_rate",)),
            ("Up Speed", self._format_speed, ("upload_payload_rate",)),
            ("Progress", self._format_progress, ("progress",)),
            ("ETA", deluge.common.ftime, ("eta",)),
            ("Path", None, ("save_path",)),
            ("Downloaded",deluge.common.fsize,("all_time_download",)),
            ("Uploaded", deluge.common.fsize,("total_uploaded",)),
            ("Share Ratio", lambda x:x < 0 and "∞" or "%.3f"%x, ("ratio",)),
            ("Seeders",self._format_seeds_peers,("num_seeds","total_seeds")),
            ("Peers",self._format_seeds_peers,("num_peers","total_peers")),
            ("Active Time",deluge.common.ftime,("active_time",)),
            ("Seeding Time",deluge.common.ftime,("seeding_time",)),
            ("Date Added",deluge.common.fdate,("time_added",)),
            ("Availability", lambda x:x < 0 and "∞" or "%.3f"%x, ("distributed_copies",)),
            ("Pieces", self._format_pieces, ("num_pieces","piece_length")),
            ]

        self._status_keys = ["name","state","download_payload_rate","upload_payload_rate",
                             "progress","eta","all_time_download","total_uploaded", "ratio",
                             "num_seeds","total_seeds","num_peers","total_peers", "active_time",
                             "seeding_time","time_added","distributed_copies", "num_pieces", 
                             "piece_length","save_path"]

    def _update_columns(self):
        self.column_widths = [5,-1,15,13,10,10,10,15,15]
        req = sum(filter(lambda x:x >= 0,self.column_widths))
        if (req > self.cols): # can't satisfy requests, just spread out evenly
            cw = int(self.cols/len(self.column_names))
            for i in range(0,len(self.column_widths)):
                self.column_widths[i] = cw
        else:
            rem = self.cols - req
            var_cols = len(filter(lambda x: x < 0,self.column_widths))
            vw = int(rem/var_cols)
            for i in range(0, len(self.column_widths)):
                if (self.column_widths[i] < 0):
                    self.column_widths[i] = vw

        self.column_string = "{!header!}%s"%("".join(["%s%s"%(self.column_names[i]," "*(self.column_widths[i]-len(self.column_names[i]))) for i in range(0,len(self.column_names))]))

    def _trim_string(self, string, w):
        return "%s... "%(string[0:w-4])

    def _format_column(self, col, lim):
        size = len(col)
        if (size >= lim - 1):
            return self._trim_string(col,lim)
        else:
            return "%s%s"%(col," "*(lim-size))

    def _format_row(self, row):
        return "".join([self._format_column(row[i],self.column_widths[i]) for i in range(0,len(row))])

    def set_state(self, state, refresh):
        self.curstate = state
        self.numtorrents = len(state)
        if refresh:
            self.refresh()

    def _scroll_up(self, by):
        self.cursel = max(self.cursel - by,1)
        if ((self.cursel - 1) < self.curoff):
            self.curoff = max(self.cursel - 1,1)

    def _scroll_down(self, by):
        self.cursel = min(self.cursel + by,self.numtorrents)
        if ((self.curoff + self.rows - 5) < self.cursel):
            self.curoff = self.cursel - self.rows + 5

    def _current_torrent_id(self):
        if self._sorted_ids:
            return self._sorted_ids[self.cursel-1]
        else:
            return None

    def _selected_torrent_ids(self):
        ret = []
        for i in self.marked:
            ret.append(self._sorted_ids[i-1])
        return ret

    def _on_torrent_status(self, state):
        if (self.popup):
            self.popup.clear()
            name = state["name"]
            off = int((self.cols/4)-(len(name)/2))
            self.popup.set_title(name)
            for i,f in enumerate(self._info_fields):
                if f[1] != None:
                    args = []
                    try:
                        for key in f[2]:
                            args.append(state[key])
                    except:
                        log.debug("Could not get info field: %s",e)
                        continue
                    info = f[1](*args)
                else:
                    info = state[f[2][0]]
                
                self.popup.add_line("{!info!}%s: {!input!}%s"%(f[0],info))
            self.refresh()
        else:
            self.updater.set_torrent_to_update(None,None)
            

    def on_resize(self, *args):
        BaseMode.on_resize_norefresh(self, *args)
        self._update_columns()
        if self.popup:
            self.popup.handle_resize()
        self.refresh()

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
        "sorts by queue #"
        return sorted(state,cmp=self._queue_sort,key=lambda s:state.get(s)["queue"])

    def _format_speed(self, speed):
        if (speed > 0):
            return deluge.common.fspeed(speed)
        else:
            return "-"

    def _format_queue(self, qnum):
        if (qnum >= 0):
            return "%d"%(qnum+1)
        else:
            return ""

    def _format_seeds_peers(self, num, total):
        return "%d (%d)"%(num,total)

    def _format_pieces(self, num, size):
        return "%d (%s)"%(num,deluge.common.fsize(size))

    def _format_progress(self, perc):
        return "%.2f%%"%perc

    def _action_error(self, error):
        rerr = error.value
        self.report_message("An Error Occurred","%s got error %s: %s"%(rerr.method,rerr.exception_type,rerr.exception_msg))
        self.refresh()

    def _torrent_action(self, idx, data):
        ids = self._selected_torrent_ids()
        if ids:
            if data==ACTION.PAUSE:
                log.debug("Pausing torrents: %s",ids)
                client.core.pause_torrent(ids).addErrback(self._action_error)
            elif data==ACTION.RESUME:
                log.debug("Resuming torrents: %s", ids)
                client.core.resume_torrent(ids).addErrback(self._action_error)
            elif data==ACTION.REMOVE:
                log.error("Can't remove just yet")
            elif data==ACTION.RECHECK:
                log.debug("Rechecking torrents: %s", ids)
                client.core.force_recheck(ids).addErrback(self._action_error)
            elif data==ACTION.REANNOUNCE:
                log.debug("Reannouncing torrents: %s",ids)
                client.core.force_reannounce(ids).addErrback(self._action_error)
        if len(ids) == 1:
            self.marked = []
            self.last_mark = -1

    def _show_torrent_actions_popup(self):
        #cid = self._current_torrent_id()
        if len(self.marked):
            self.popup = SelectablePopup(self,"Torrent Actions",self._torrent_action)
            self.popup.add_line("_Pause",data=ACTION.PAUSE)
            self.popup.add_line("_Resume",data=ACTION.RESUME)
            self.popup.add_divider()
            self.popup.add_line("_Update Tracker",data=ACTION.REANNOUNCE)
            self.popup.add_divider()
            self.popup.add_line("Remo_ve Torrent",data=ACTION.REMOVE)
            self.popup.add_line("_Force Recheck",data=ACTION.RECHECK)

    def _torrent_filter(self, idx, data):
        if data==FILTER.ALL:
            self.updater.status_dict = {}
            self._curr_filter = None
        elif data==FILTER.ACTIVE:
            self.updater.status_dict = {"state":"Active"}
            self._curr_filter = "Active"
        elif data==FILTER.DOWNLOADING:
            self.updater.status_dict = {"state":"Downloading"}
            self._curr_filter = "Downloading"
        elif data==FILTER.SEEDING:
            self.updater.status_dict = {"state":"Seeding"}
            self._curr_filter = "Seeding"
        elif data==FILTER.PAUSED:
            self.updater.status_dict = {"state":"Paused"}
            self._curr_filter = "Paused"
        elif data==FILTER.CHECKING:
            self.updater.status_dict = {"state":"Checking"}
            self._curr_filter = "Checking"
        elif data==FILTER.ERROR:
            self.updater.status_dict = {"state":"Error"}
            self._curr_filter = "Error"
        elif data==FILTER.QUEUED:
            self.updater.status_dict = {"state":"Queued"}
            self._curr_filter = "Queued"
        self._go_top = True

    def _show_torrent_filter_popup(self):
        self.popup = SelectablePopup(self,"Filter Torrents",self._torrent_filter)
        self.popup.add_line("_All",data=FILTER.ALL)
        self.popup.add_line("Ac_tive",data=FILTER.ACTIVE)
        self.popup.add_line("_Downloading",data=FILTER.DOWNLOADING,foreground="green")
        self.popup.add_line("_Seeding",data=FILTER.SEEDING,foreground="cyan")
        self.popup.add_line("_Paused",data=FILTER.PAUSED)
        self.popup.add_line("_Error",data=FILTER.ERROR,foreground="red")
        self.popup.add_line("_Checking",data=FILTER.CHECKING,foreground="blue")
        self.popup.add_line("Q_ueued",data=FILTER.QUEUED,foreground="yellow")

    def _do_add(self, result):
        log.debug("Doing adding %s (dl to %s)",result["file"],result["path"])
        def suc_cb(msg):
            self.report_message("Torrent Added",msg)
        def fail_cb(msg):
            self.report_message("Failed To Add Torrent",msg)
        add_torrent(result["file"],result,suc_cb,fail_cb)

    def _show_torrent_add_popup(self):
        dl = ""
        try:
            dl = self.coreconfig["download_location"]
        except KeyError:
            pass
        self.popup = InputPopup(self,"Add Torrent (Esc to cancel)",close_cb=self._do_add)
        self.popup.add_text_input("Enter path to torrent file:","file")
        self.popup.add_text_input("Enter save path:","path",dl)

    def report_message(self,title,message):
        self.messages.append((title,message))

    def refresh(self):
        # Something has requested we scroll to the top of the list
        if self._go_top:
            self.cursel = 1
            self.curoff = 1
            self._go_top = False

        # show a message popup if there's anything queued
        if self.popup == None and self.messages:
            title,msg = self.messages.popleft()
            self.popup = MessagePopup(self,title,msg)

        self.stdscr.clear()

        # Update the status bars
        if self._curr_filter == None:
            self.add_string(0,self.topbar)
        else:
            self.add_string(0,"%s    {!filterstatus!}Current filter: %s"%(self.topbar,self._curr_filter))
        self.add_string(1,self.column_string)
        hstr =  "%sPress [h] for help"%(" "*(self.cols - len(self.bottombar) - 10))
        self.add_string(self.rows - 1, "%s%s"%(self.bottombar,hstr))

        # add all the torrents
        if self.curstate == {}:
            msg = "No torrents match filter".center(self.cols)
            self.add_string(3, "{!info!}%s"%msg)
        elif self.curstate != None:
            tidx = 1
            currow = 2
            self._sorted_ids = self._sort_torrents(self.curstate) 
            for torrent_id in self._sorted_ids:
                if (tidx < self.curoff):
                    tidx += 1
                    continue
                ts = self.curstate[torrent_id]
                s = self._format_row([self._format_queue(ts["queue"]),
                                      ts["name"],
                                      "%s"%deluge.common.fsize(ts["total_wanted"]),
                                      ts["state"],
                                      self._format_progress(ts["progress"]),
                                      self._format_seeds_peers(ts["num_seeds"],ts["total_seeds"]),
                                      self._format_seeds_peers(ts["num_peers"],ts["total_peers"]),
                                      self._format_speed(ts["download_payload_rate"]),
                                      self._format_speed(ts["upload_payload_rate"])
                                      ])

                # default style
                fg = "white"
                bg = "black"
                attr = None

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

                if ts["state"] == "Downloading":
                    fg = "green"
                elif ts["state"] == "Seeding":
                    fg = "cyan"
                elif ts["state"] == "Error":              
                    fg = "red"
                elif ts["state"] == "Queued":
                    fg = "yellow"
                elif ts["state"] == "Checking":
                    fg = "blue"
                    
                if attr:
                    colorstr = "{!%s,%s,%s!}"%(fg,bg,attr)
                else:
                    colorstr = "{!%s,%s!}"%(fg,bg)
                self.add_string(currow,"%s%s"%(colorstr,s))
                tidx += 1
                currow += 1 
                if (currow > (self.rows - 2)):
                    break
        else:
            self.add_string(1, "Waiting for torrents from core...")

        self.stdscr.redrawwin()
        self.stdscr.noutrefresh()

        if self.popup:
            self.popup.refresh()

        curses.doupdate()


    def _mark_unmark(self,idx):
        if idx in self.marked:
            self.marked.remove(idx)
            self.last_mark = -1
        else:
            self.marked.append(idx)
            self.last_mark = idx


    def _doRead(self):
        # Read the character
        c = self.stdscr.getch()

        if self.popup:
            if self.popup.handle_read(c):
                self.popup = None
            self.refresh()
            return

        if c > 31 and c < 256:
            if chr(c) == 'Q':
                from twisted.internet import reactor
                if client.connected():
                    def on_disconnect(result):
                        reactor.stop()
                    client.disconnect().addCallback(on_disconnect)
                else:
                    reactor.stop()            
                return

        if self.curstate==None or self.popup:
            return

        #log.error("pressed key: %d\n",c)
        #if c == 27: # handle escape
        #    log.error("CANCEL")
        
        # Navigate the torrent list
        if c == curses.KEY_UP:
            self._scroll_up(1)
        elif c == curses.KEY_PPAGE:
            self._scroll_up(int(self.rows/2))
        elif c == curses.KEY_DOWN:
            self._scroll_down(1)
        elif c == curses.KEY_NPAGE:
            self._scroll_down(int(self.rows/2))

        # Enter Key
        elif c == curses.KEY_ENTER or c == 10:
            self.marked.append(self.cursel)
            self.last_mark = self.cursel
            self._show_torrent_actions_popup()

        else:
            if c > 31 and c < 256:
                if chr(c) == 'j':
                    self._scroll_up(1)
                elif chr(c) == 'k':
                    self._scroll_down(1)
                elif chr(c) == 'i':
                    cid = self._current_torrent_id()
                    if cid:
                        self.popup = Popup(self,"Info",close_cb=lambda:self.updater.set_torrent_to_update(None,None))
                        self.popup.add_line("Getting torrent info...")
                        self.updater.set_torrent_to_update(cid,self._status_keys)
                elif chr(c) == 'm':
                    self._mark_unmark(self.cursel)
                elif chr(c) == 'M':
                    if self.last_mark >= 0:
                        self.marked.extend(range(self.last_mark,self.cursel+1))
                    else:
                        self._mark_unmark(self.cursel)
                elif chr(c) == 'c':
                    self.marked = []
                    self.last_mark = -1
                elif chr(c) == 'a':
                    self._show_torrent_add_popup()
                elif chr(c) == 'f':
                    self._show_torrent_filter_popup()
                elif chr(c) == 'h':
                    self.popup = Popup(self,"Help")
                    for l in HELP_LINES:
                        self.popup.add_line(l)

        self.refresh()
