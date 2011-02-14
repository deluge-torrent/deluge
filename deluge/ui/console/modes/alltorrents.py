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
from torrentdetail import TorrentDetail
from preferences import Preferences
from torrent_actions import torrent_actions_popup
from eventview import EventView

import format_utils

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

Right Arrow - Show torrent details.  This includes more detailed information
              about the currently selected torrent, as well as a view of the
              files in the torrent and the ability to set file priorities.

Enter - Show torrent actions popup.  Here you can do things like
        pause/resume, remove, recheck and so one.  These actions
        apply to all currently marked torrents.  The currently
        selected torrent is automatically marked when you press enter.

'q'/Esc - Close a popup
"""
HELP_LINES = HELP_STR.split('\n')

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


class AllTorrents(BaseMode):
    def __init__(self, stdscr, encoding=None):
        self.formatted_rows = None
        self.cursel = 1
        self.curoff = 1 # TODO: this should really be 0 indexed
        self.column_string = ""
        self.popup = None
        self.messages = deque()
        self.marked = []
        self.last_mark = -1
        self._sorted_ids = None
        self._go_top = False

        self._curr_filter = None

        self.coreconfig = component.get("ConsoleUI").coreconfig

        BaseMode.__init__(self, stdscr, encoding)
        curses.curs_set(0)
        self.stdscr.notimeout(0)

        self._status_fields = ["queue","name","total_wanted","state","progress","num_seeds","total_seeds",
                               "num_peers","total_peers","download_payload_rate", "upload_payload_rate"]

        self.updater = StateUpdater(self.set_state,self._status_fields,self._on_torrent_status)

        self.column_names = ["#", "Name","Size","State","Progress","Seeders","Peers","Down Speed","Up Speed"]
        self._update_columns()


        self._info_fields = [
            ("Name",None,("name",)),
            ("State", None, ("state",)),
            ("Down Speed", format_utils.format_speed, ("download_payload_rate",)),
            ("Up Speed", format_utils.format_speed, ("upload_payload_rate",)),
            ("Progress", format_utils.format_progress, ("progress",)),
            ("ETA", deluge.common.ftime, ("eta",)),
            ("Path", None, ("save_path",)),
            ("Downloaded",deluge.common.fsize,("all_time_download",)),
            ("Uploaded", deluge.common.fsize,("total_uploaded",)),
            ("Share Ratio", lambda x:x < 0 and "∞" or "%.3f"%x, ("ratio",)),
            ("Seeders",format_utils.format_seeds_peers,("num_seeds","total_seeds")),
            ("Peers",format_utils.format_seeds_peers,("num_peers","total_peers")),
            ("Active Time",deluge.common.ftime,("active_time",)),
            ("Seeding Time",deluge.common.ftime,("seeding_time",)),
            ("Date Added",deluge.common.fdate,("time_added",)),
            ("Availability", lambda x:x < 0 and "∞" or "%.3f"%x, ("distributed_copies",)),
            ("Pieces", format_utils.format_pieces, ("num_pieces","piece_length")),
            ]

        self._status_keys = ["name","state","download_payload_rate","upload_payload_rate",
                             "progress","eta","all_time_download","total_uploaded", "ratio",
                             "num_seeds","total_seeds","num_peers","total_peers", "active_time",
                             "seeding_time","time_added","distributed_copies", "num_pieces", 
                             "piece_length","save_path"]

    def resume(self):
        component.start(["AllTorrentsStateUpdater"])
        self.refresh()
        

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


    def set_state(self, state, refresh):
        self.curstate = state # cache in case we change sort order
        newrows = []
        self._sorted_ids = self._sort_torrents(self.curstate)
        for torrent_id in self._sorted_ids:
            ts = self.curstate[torrent_id]
            newrows.append((format_utils.format_row([self._format_queue(ts["queue"]),
                                                     ts["name"],
                                                     "%s"%deluge.common.fsize(ts["total_wanted"]),
                                                     ts["state"],
                                                     format_utils.format_progress(ts["progress"]),
                                                     format_utils.format_seeds_peers(ts["num_seeds"],ts["total_seeds"]),
                                                     format_utils.format_seeds_peers(ts["num_peers"],ts["total_peers"]),
                                                     format_utils.format_speed(ts["download_payload_rate"]),
                                                     format_utils.format_speed(ts["upload_payload_rate"])
                                                     ],self.column_widths),ts["state"]))
        self.numtorrents = len(state)
        self.formatted_rows = newrows
        if refresh:
            self.refresh()

    def _scroll_up(self, by):
        prevoff = self.curoff
        self.cursel = max(self.cursel - by,1)
        if ((self.cursel - 1) < self.curoff):
            self.curoff = max(self.cursel - 1,1)
        return prevoff != self.curoff

    def _scroll_down(self, by):
        prevoff = self.curoff
        self.cursel = min(self.cursel + by,self.numtorrents)
        if ((self.curoff + self.rows - 5) < self.cursel):
            self.curoff = self.cursel - self.rows + 5
        return prevoff != self.curoff

    def current_torrent_id(self):
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

    def _format_queue(self, qnum):
        if (qnum >= 0):
            return "%d"%(qnum+1)
        else:
            return ""


    def show_torrent_details(self,tid):
        component.stop(["AllTorrentsStateUpdater"])
        self.stdscr.clear()
        td = TorrentDetail(self,tid,self.stdscr,self.encoding)
        component.get("ConsoleUI").set_mode(td)

    def show_preferences(self, core_config):
        component.stop(["AllTorrentsStateUpdater"])
        self.stdscr.clear()
        prefs = Preferences(self,core_config,self.stdscr,self.encoding)
        component.get("ConsoleUI").set_mode(prefs)

    def __show_events(self):
        component.stop(["AllTorrentsStateUpdater"])
        self.stdscr.clear()
        ev = EventView(self,self.stdscr,self.encoding)
        component.get("ConsoleUI").set_mode(ev)

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
        return True

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
        log.debug("Adding Torrent: %s (dl path: %s) (paused: %d)",result["file"],result["path"],result["add_paused"])
        def suc_cb(msg):
            self.report_message("Torrent Added",msg)
        def fail_cb(msg):
            self.report_message("Failed To Add Torrent",msg)
        add_torrent(result["file"],result,suc_cb,fail_cb)

    def _show_torrent_add_popup(self):
        dl = ""
        ap = 1
        try:
            dl = self.coreconfig["download_location"]
        except KeyError:
            pass
        try:
            if self.coreconfig["add_paused"]:
                ap = 0
        except KeyError:
            pass

        self.popup = InputPopup(self,"Add Torrent (Esc to cancel)",close_cb=self._do_add)
        self.popup.add_text_input("Enter path to torrent file:","file")
        self.popup.add_text_input("Enter save path:","path",dl)
        self.popup.add_select_input("Add Paused:","add_paused",["Yes","No"],[True,False],ap)

    def report_message(self,title,message):
        self.messages.append((title,message))

    def clear_marks(self):
        self.marked = []
        self.last_mark = -1

    def set_popup(self,pu):
        self.popup = pu
        self.refresh()

    def refresh(self,lines=None):
        #log.error("ref")
        #import traceback
        #traceback.print_stack()
        # Something has requested we scroll to the top of the list
        if self._go_top:
            self.cursel = 1
            self.curoff = 1
            self._go_top = False

        # show a message popup if there's anything queued
        if self.popup == None and self.messages:
            title,msg = self.messages.popleft()
            self.popup = MessagePopup(self,title,msg)

        if not lines:
            self.stdscr.clear()

        # Update the status bars
        if self._curr_filter == None:
            self.add_string(0,self.statusbars.topbar)
        else:
            self.add_string(0,"%s    {!filterstatus!}Current filter: %s"%(self.statusbars.topbar,self._curr_filter))
        self.add_string(1,self.column_string)
        hstr =  "%sPress [h] for help"%(" "*(self.cols - len(self.statusbars.bottombar) - 10))
        self.add_string(self.rows - 1, "%s%s"%(self.statusbars.bottombar,hstr))

        # add all the torrents
        if self.formatted_rows == []:
            msg = "No torrents match filter".center(self.cols)
            self.add_string(3, "{!info!}%s"%msg)
        elif self.formatted_rows:
            tidx = self.curoff
            currow = 2

            if lines:
                todraw = []
                for l in lines:
                    todraw.append(self.formatted_rows[l])
                lines.reverse()
            else:
                todraw = self.formatted_rows[tidx-1:]

            for row in todraw:
                # default style
                fg = "white"
                bg = "black"
                attr = None
                if lines:
                    tidx = lines.pop()+1
                    currow = tidx-self.curoff+2

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
                    
                if attr:
                    colorstr = "{!%s,%s,%s!}"%(fg,bg,attr)
                else:
                    colorstr = "{!%s,%s!}"%(fg,bg)

                self.add_string(currow,"%s%s"%(colorstr,row[0]))
                tidx += 1
                currow += 1 
                if (currow > (self.rows - 2)):
                    break
        else:
            self.add_string(1, "Waiting for torrents from core...")

        #self.stdscr.redrawwin()
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
        effected_lines = None

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

        if self.formatted_rows==None or self.popup:
            return

        #log.error("pressed key: %d\n",c)
        #if c == 27: # handle escape
        #    log.error("CANCEL")
        
        # Navigate the torrent list
        if c == curses.KEY_UP:
            if self.cursel == 1: return
            if not self._scroll_up(1):
                effected_lines = [self.cursel-1,self.cursel]
        elif c == curses.KEY_PPAGE:
            self._scroll_up(int(self.rows/2))
        elif c == curses.KEY_DOWN:
            if self.cursel >= self.numtorrents: return
            if not self._scroll_down(1):
                effected_lines = [self.cursel-2,self.cursel-1]
        elif c == curses.KEY_NPAGE:
            self._scroll_down(int(self.rows/2))

        elif c == curses.KEY_RIGHT:
            # We enter a new mode for the selected torrent here
            tid = self.current_torrent_id()
            if tid:
                self.show_torrent_details(tid)
                return

        # Enter Key
        elif (c == curses.KEY_ENTER or c == 10) and self.numtorrents:
            self.marked.append(self.cursel)
            self.last_mark = self.cursel
            torrent_actions_popup(self,self._selected_torrent_ids(),details=True)
            return

        else:
            if c > 31 and c < 256:
                if chr(c) == 'j':
                    if not self._scroll_up(1):
                        effected_lines = [self.cursel-1,self.cursel]
                elif chr(c) == 'k':
                    if not self._scroll_down(1):
                        effected_lines = [self.cursel-2,self.cursel-1]
                elif chr(c) == 'i':
                    cid = self.current_torrent_id()
                    if cid:
                        self.popup = Popup(self,"Info",close_cb=lambda:self.updater.set_torrent_to_update(None,None))
                        self.popup.add_line("Getting torrent info...")
                        self.updater.set_torrent_to_update(cid,self._status_keys)
                elif chr(c) == 'm':
                    self._mark_unmark(self.cursel)
                    effected_lines = [self.cursel-1]
                elif chr(c) == 'M':
                    if self.last_mark >= 0:
                        self.marked.extend(range(self.last_mark,self.cursel+1))
                        effected_lines = range(self.last_mark,self.cursel)
                    else:
                        self._mark_unmark(self.cursel)
                        effected_lines = [self.cursel-1]
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
                elif chr(c) == 'p':
                    client.core.get_config().addCallback(self.show_preferences)
                    return
                elif chr(c) == 'e':
                    self.__show_events()
                    return

        self.refresh(effected_lines)
