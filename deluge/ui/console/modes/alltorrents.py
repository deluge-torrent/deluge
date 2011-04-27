# -*- coding: utf-8 -*-
#
# alltorrents.py
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
from deluge.configmanager import ConfigManager

from collections import deque

from deluge.ui.sessionproxy import SessionProxy

from popup import Popup,SelectablePopup,MessagePopup
from add_util import add_torrent
from input_popup import InputPopup
from torrentdetail import TorrentDetail
from preferences import Preferences
from torrent_actions import torrent_actions_popup
from eventview import EventView
from legacy import Legacy

import format_utils,column

try:
    import curses
except ImportError:
    pass

import logging
log = logging.getLogger(__name__)


# Big help string that gets displayed when the user hits 'h'
HELP_STR = """\
This screen shows an overview of the current torrents Deluge is managing. \
The currently selected torrent is indicated by having a white background. \
You can change the selected torrent using the up/down arrows or the \
PgUp/Pg keys.  Home and End keys go to the first and last torrent \
respectively.

Operations can be performed on multiple torrents by marking them and \
then hitting Enter.  See below for the keys used to mark torrents.

You can scroll a popup window that doesn't fit its content (like \
this one) using the up/down arrows.

All popup windows can be closed/canceled by hitting the Esc key \
(you might need to wait a second for an Esc to register)

The actions you can perform and the keys to perform them are as follows:

{!info!}'h'{!normal!} - Show this help

{!info!}'a'{!normal!} - Add a torrent

{!info!}'p'{!normal!} - View/Set preferences

{!info!}'/'{!normal!} - Search torrent names.  Enter to exectue search, ESC to cancel

{!info!}'n'{!normal!} - Next matching torrent for last search

{!info!}'f'{!normal!} - Show only torrents in a certain state
      (Will open a popup where you can select the state you want to see)

{!info!}'i'{!normal!} - Show more detailed information about the current selected torrent

{!info!}'e'{!normal!} - Show the event log view ({!info!}'q'{!normal!} to get out of event log)

{!info!}'l'{!normal!} - Go into 'legacy' mode (the way deluge-console used to work)

{!info!}'Q'{!normal!} - quit

{!info!}'m'{!normal!} - Mark a torrent
{!info!}'M'{!normal!} - Mark all torrents between currently selected torrent and last marked torrent
{!info!}'c'{!normal!} - Un-mark all torrents

{!info!}Right Arrow{!normal!} - Torrent Detail Mode.  This includes more detailed information \
about the currently selected torrent, as well as a view of the \
files in the torrent and the ability to set file priorities.

{!info!}Enter{!normal!} - Show torrent actions popup.  Here you can do things like \
pause/resume, remove, recheck and so on.  These actions \
apply to all currently marked torrents.  The currently \
selected torrent is automatically marked when you press enter. 

{!info!}'q'/Esc{!normal!} - Close a popup (Note that Esc can take a moment to register \
as having been pressed.
"""

class FILTER:
    ALL=0
    ACTIVE=1
    DOWNLOADING=2
    SEEDING=3
    PAUSED=4
    CHECKING=5
    ERROR=6
    QUEUED=7

DEFAULT_PREFS = {
    "show_queue":True,
    "show_name":True,
    "show_size":True,
    "show_state":True,
    "show_progress":True,
    "show_seeders":True,
    "show_peers":True,
    "show_downspeed":True,
    "show_upspeed":True,
    "show_eta":False,
    "show_ratio":False,
    "show_avail":False,
    "show_added":False,
    "show_tracker":False,
    "show_savepath":False,
    "show_downloaded":False,
    "show_uploaded":False,
    "show_owner":False,
    "queue_width":5,
    "name_width":-1,
    "size_width":15,
    "state_width":13,
    "progress_width":10,
    "seeders_width":10,
    "peers_width":10,
    "downspeed_width":15,
    "upspeed_width":15,
    "eta_width":10,
    "ratio_width":10,
    "avail_width":10,
    "added_width":25,
    "tracker_width":15,
    "savepath_width":15,
    "downloaded_width":13,
    "uploaded_width":13,
    "owner_width":10,
}

column_pref_names = ["queue","name","size","state",
                     "progress","seeders","peers",
                     "downspeed","upspeed","eta",
                     "ratio","avail","added","tracker",
                     "savepath","downloaded","uploaded",
                     "owner"]

prefs_to_names = {
    "queue":"#", 
    "name":"Name",
    "size":"Size",
    "state":"State",
    "progress":"Progress",
    "seeders":"Seeders",
    "peers":"Peers",
    "downspeed":"Down Speed",
    "upspeed":"Up Speed",
    "eta":"ETA",
    "ratio":"Ratio",
    "avail":"Avail",
    "added":"Added",
    "tracker":"Tracker",
    "savepath":"Save Path",
    "downloaded":"Downloaded",
    "uploaded":"Uploaded",
    "owner":"Owner",
}

class AllTorrents(BaseMode, component.Component):
    def __init__(self, stdscr, encoding=None):
        self.formatted_rows = None
        self.torrent_names = None
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
        self.entering_search = False
        self.search_string = None
        self.cursor = 0

        self.coreconfig = component.get("ConsoleUI").coreconfig

        self.legacy_mode = None

        self.__status_dict = {}
        self.__torrent_info_id = None

        BaseMode.__init__(self, stdscr, encoding)
        component.Component.__init__(self, "AllTorrents", 1, depend=["SessionProxy"])
        curses.curs_set(0)
        self.stdscr.notimeout(0)

        self.__split_help()
        self.update_config()

        component.start(["AllTorrents"])

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
            ("Share Ratio", format_utils.format_float, ("ratio",)),
            ("Seeders",format_utils.format_seeds_peers,("num_seeds","total_seeds")),
            ("Peers",format_utils.format_seeds_peers,("num_peers","total_peers")),
            ("Active Time",deluge.common.ftime,("active_time",)),
            ("Seeding Time",deluge.common.ftime,("seeding_time",)),
            ("Date Added",deluge.common.fdate,("time_added",)),
            ("Availability", format_utils.format_float, ("distributed_copies",)),
            ("Pieces", format_utils.format_pieces, ("num_pieces","piece_length")),
            ]

        self.__status_keys = ["name","state","download_payload_rate","upload_payload_rate",
                             "progress","eta","all_time_download","total_uploaded", "ratio",
                             "num_seeds","total_seeds","num_peers","total_peers", "active_time",
                             "seeding_time","time_added","distributed_copies", "num_pieces", 
                             "piece_length","save_path"]

    # component start/update
    def start(self):
        component.get("SessionProxy").get_torrents_status(self.__status_dict, self.__status_fields).addCallback(self.set_state,False)

    def update(self):
        component.get("SessionProxy").get_torrents_status(self.__status_dict, self.__status_fields).addCallback(self.set_state,True)
        if self.__torrent_info_id:
            component.get("SessionProxy").get_torrent_status(self.__torrent_info_id, self.__status_keys).addCallback(self._on_torrent_status)

    def update_config(self):
        self.config = ConfigManager("console.conf",DEFAULT_PREFS)
        self.__cols_to_show = [pref for pref in column_pref_names if self.config["show_%s"%pref]]
        self.__columns = [prefs_to_names[col] for col in self.__cols_to_show]
        self.__status_fields = column.get_required_fields(self.__columns)
        for rf in ["state","name","queue"]: # we always need these, even if we're not displaying them
            if not rf in self.__status_fields: self.__status_fields.append(rf)
        self.__update_columns()

    def __split_help(self):
        self.__help_lines = format_utils.wrap_string(HELP_STR,(self.cols/2)-2)

    def resume(self):
        component.start(["AllTorrents"])
        self.refresh()
        
    def __update_columns(self):
        self.column_widths = [self.config["%s_width"%c] for c in self.__cols_to_show]
        req = sum(filter(lambda x:x >= 0,self.column_widths))
        if (req > self.cols): # can't satisfy requests, just spread out evenly
            cw = int(self.cols/len(self.__columns))
            for i in range(0,len(self.column_widths)):
                self.column_widths[i] = cw
        else:
            rem = self.cols - req
            var_cols = len(filter(lambda x: x < 0,self.column_widths))
            if (var_cols > 0):
                vw = int(rem/var_cols)
                for i in range(0, len(self.column_widths)):
                    if (self.column_widths[i] < 0):
                        self.column_widths[i] = vw

        self.column_string = "{!header!}%s"%("".join(["%s%s"%(self.__columns[i]," "*(self.column_widths[i]-len(self.__columns[i]))) for i in range(0,len(self.__columns))]))


    def set_state(self, state, refresh):
        self.curstate = state # cache in case we change sort order
        newnames = []
        newrows = []
        self._sorted_ids = self._sort_torrents(self.curstate)
        for torrent_id in self._sorted_ids:
            ts = self.curstate[torrent_id]
            newnames.append(ts["name"])
            newrows.append((format_utils.format_row([column.get_column_value(name,ts) for name in self.__columns],self.column_widths),ts["state"]))

        self.numtorrents = len(state)
        self.formatted_rows = newrows
        self.torrent_names = newnames
        if refresh:
            self.refresh()

    def get_torrent_name(self, torrent_id):
        for p,i in enumerate(self._sorted_ids):
            if torrent_id == i:
                return self.torrent_names[p]
        return None

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
                
                nl = len(f[0])+4
                if (nl+len(info))>self.popup.width:
                    self.popup.add_line("{!info!}%s: {!input!}%s"%(f[0],info[:(self.popup.width - nl)]))
                    info = info[(self.popup.width - nl):]
                    n = self.popup.width-3
                    chunks = [info[i:i+n] for i in xrange(0, len(info), n)]
                    for c in chunks:
                        self.popup.add_line(" %s"%c)
                else:
                    self.popup.add_line("{!info!}%s: {!input!}%s"%(f[0],info))
            self.refresh()
        else:
            self.__torrent_info_id = None
            

    def on_resize(self, *args):
        BaseMode.on_resize_norefresh(self, *args)
        self.__update_columns()
        self.__split_help()
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
        def dodeets(arg):
            if arg and True in arg[0]:
                self.stdscr.clear()
                component.get("ConsoleUI").set_mode(TorrentDetail(self,tid,self.stdscr,self.encoding))
            else:
                self.messages.append(("Error","An error occured trying to display torrent details"))
        component.stop(["AllTorrents"]).addCallback(dodeets)

    def show_preferences(self):
        def _on_get_config(config):
            client.core.get_listen_port().addCallback(_on_get_listen_port,config)

        def _on_get_listen_port(port,config):
            client.core.get_cache_status().addCallback(_on_get_cache_status,port,config)

        def _on_get_cache_status(status,port,config):
            def doprefs(arg):
                if arg and True in arg[0]:
                    self.stdscr.clear()
                    component.get("ConsoleUI").set_mode(Preferences(self,config,self.config,port,status,self.stdscr,self.encoding))
                else:
                    self.messages.append(("Error","An error occured trying to display preferences"))
            component.stop(["AllTorrents"]).addCallback(doprefs)

        client.core.get_config().addCallback(_on_get_config)
        

    def __show_events(self):
        def doevents(arg):
            if arg and True in arg[0]:
                self.stdscr.clear()
                component.get("ConsoleUI").set_mode(EventView(self,self.stdscr,self.encoding))
            else:
                self.messages.append(("Error","An error occured trying to display events"))
        component.stop(["AllTorrents"]).addCallback(doevents)

    def __legacy_mode(self):
        def dolegacy(arg):
            if arg and True in arg[0]:
                self.stdscr.clear()
                if not self.legacy_mode:
                    self.legacy_mode = Legacy(self.stdscr,self.encoding)
                component.get("ConsoleUI").set_mode(self.legacy_mode)
                self.legacy_mode.refresh()
                curses.curs_set(2)
            else:
                self.messages.append(("Error","An error occured trying to switch to legacy mode"))
        component.stop(["AllTorrents"]).addCallback(dolegacy)

    def _torrent_filter(self, idx, data):
        if data==FILTER.ALL:
            self.__status_dict = {}
            self._curr_filter = None
        elif data==FILTER.ACTIVE:
            self.__status_dict = {"state":"Active"}
            self._curr_filter = "Active"
        elif data==FILTER.DOWNLOADING:
            self.__status_dict = {"state":"Downloading"}
            self._curr_filter = "Downloading"
        elif data==FILTER.SEEDING:
            self.__status_dict = {"state":"Seeding"}
            self._curr_filter = "Seeding"
        elif data==FILTER.PAUSED:
            self.__status_dict = {"state":"Paused"}
            self._curr_filter = "Paused"
        elif data==FILTER.CHECKING:
            self.__status_dict = {"state":"Checking"}
            self._curr_filter = "Checking"
        elif data==FILTER.ERROR:
            self.__status_dict = {"state":"Error"}
            self._curr_filter = "Error"
        elif data==FILTER.QUEUED:
            self.__status_dict = {"state":"Queued"}
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

    def __report_add_status(self, succ_cnt, fail_cnt, fail_msgs):
        if fail_cnt == 0:
            self.report_message("Torrents Added","{!success!}Sucessfully added %d torrent(s)"%succ_cnt)
        else:
            msg = ("{!error!}Failed to add the following %d torrent(s):\n {!error!}"%fail_cnt)+"\n {!error!}".join(fail_msgs)
            if succ_cnt != 0:
                msg += "\n \n{!success!}Sucessfully added %d torrent(s)"%succ_cnt
            self.report_message("Torrent Add Report",msg)

    def _do_add(self, result):
        log.debug("Adding Torrent(s): %s (dl path: %s) (paused: %d)",result["file"],result["path"],result["add_paused"])
        ress = {"succ":0,
                "fail":0,
                "fmsg":[]}

        def fail_cb(msg,t_file,ress):
            log.debug("failed to add torrent: %s: %s"%(t_file,msg))
            ress["fail"]+=1
            ress["fmsg"].append("%s: %s"%(t_file,msg))
            if (ress["succ"]+ress["fail"]) >= ress["total"]:
                self.__report_add_status(ress["succ"],ress["fail"],ress["fmsg"])
        def suc_cb(tid,t_file,ress):
            if tid:
                log.debug("added torrent: %s (%s)"%(t_file,tid))
                ress["succ"]+=1
                if (ress["succ"]+ress["fail"]) >= ress["total"]:
                    self.__report_add_status(ress["succ"],ress["fail"],ress["fmsg"])
            else:
                fail_cb("Already in session (probably)",t_file,ress)

        add_torrent(result["file"],result,suc_cb,fail_cb,ress)

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
        self.popup.add_spaces(1)
        self.popup.add_select_input("Path is:","path_type",["Auto","File","URL"],[0,1,2],0)

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

        if self.entering_search:
            self.add_string(self.rows - 1,"{!black,white!}Search torrents: %s"%self.search_string)
        else:
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

                self.add_string(currow,"%s%s"%(colorstr,row[0]),trim=False)
                tidx += 1
                currow += 1 
                if (currow > (self.rows - 2)):
                    break
        else:
            self.add_string(1, "Waiting for torrents from core...")

        #self.stdscr.redrawwin()
        if self.entering_search:
            curses.curs_set(2)
            self.stdscr.move(self.rows-1,self.cursor+17)
        else:
            curses.curs_set(0)

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

    def __do_search(self):
        # search forward for the next torrent matching self.search_string
        for i,n in enumerate(self.torrent_names[self.cursel:]):
            if n.find(self.search_string) >= 0:
                self.cursel += (i+1)
                if ((self.curoff + self.rows - 5) < self.cursel):
                    self.curoff = self.cursel - self.rows + 5
                return

    def __update_search(self, c):
        if c == curses.KEY_BACKSPACE or c == 127:
            if self.search_string and  self.cursor > 0:
                self.search_string = self.search_string[:self.cursor - 1] + self.search_string[self.cursor:]
                self.cursor-=1
        elif c == curses.KEY_DC:
            if self.search_string and self.cursor < len(self.search_string):
                self.search_string = self.search_string[:self.cursor] + self.search_string[self.cursor+1:]
        elif c == curses.KEY_LEFT:
            self.cursor = max(0,self.cursor-1)
        elif c == curses.KEY_RIGHT:
            self.cursor = min(len(self.search_string),self.cursor+1)
        elif c == curses.KEY_HOME:
            self.cursor = 0
        elif c == curses.KEY_END:
            self.cursor = len(self.search_string)
        elif c == 27:
            self.search_string = None
            self.entering_search = False
        elif c == 10 or c == curses.KEY_ENTER:
            self.entering_search = False
            if self.search_string:
                self.__do_search()
            else:
                self.search_string = None
        elif c > 31 and c < 256:
            stroke = chr(c)
            uchar = ""
            while not uchar:
                try:
                    uchar = stroke.decode(self.encoding)
                except UnicodeDecodeError:
                    c = self.stdscr.getch()
                    stroke += chr(c)
            if uchar:
                if self.cursor == len(self.search_string):
                    self.search_string += uchar
                else:
                    # Insert into string
                    self.search_string = self.search_string[:self.cursor] + uchar + self.search_string[self.cursor:]
                # Move the cursor forward
                self.cursor+=1

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

        elif self.entering_search:
            self.__update_search(c)
            self.refresh([])
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
        elif c == curses.KEY_HOME:
            self._scroll_up(self.cursel)
        elif c == curses.KEY_END:
            self._scroll_down(self.numtorrents-self.cursel)

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
            torrent_actions_popup(self,self._selected_torrent_ids(),details=True)
            return
        else:
            if c > 31 and c < 256:
                if chr(c) == '/':
                    self.search_string = ""
                    self.cursor = 0
                    self.entering_search = True
                elif chr(c) == 'n' and self.search_string:
                    self.__do_search()
                elif chr(c) == 'j':
                    if not self._scroll_up(1):
                        effected_lines = [self.cursel-1,self.cursel]
                elif chr(c) == 'k':
                    if not self._scroll_down(1):
                        effected_lines = [self.cursel-2,self.cursel-1]
                elif chr(c) == 'i':
                    cid = self.current_torrent_id()
                    if cid:
                        def cb(): self.__torrent_info_id = None
                        self.popup = Popup(self,"Info",close_cb=cb)
                        self.popup.add_line("Getting torrent info...")
                        self.__torrent_info_id = cid
                elif chr(c) == 'm':
                    self._mark_unmark(self.cursel)
                    effected_lines = [self.cursel-1]
                elif chr(c) == 'M':
                    if self.last_mark >= 0:
                        if (self.cursel+1) > self.last_mark:
                            mrange = range(self.last_mark,self.cursel+1)
                        else:
                            mrange = range(self.cursel-1,self.last_mark)
                        self.marked.extend(mrange[1:])
                        effected_lines = mrange
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
                    self.popup = Popup(self,"Help",init_lines=self.__help_lines)
                elif chr(c) == 'p':
                    self.show_preferences()
                    return
                elif chr(c) == 'e':
                    self.__show_events()
                    return
                elif chr(c) == 'l':
                    self.__legacy_mode()
                    return

        self.refresh(effected_lines)
