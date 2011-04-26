# -*- coding: utf-8 -*-
#
# torrentdetail.py
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

from sys import maxint
from collections import deque

from deluge.ui.sessionproxy import SessionProxy

from popup import Popup,SelectablePopup,MessagePopup
from add_util import add_torrent
from input_popup import InputPopup
import format_utils

from torrent_actions import torrent_actions_popup

try:
    import curses
except ImportError:
    pass

import logging
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
pause/resume, remove, recheck and so on.

{!info!}'m'{!normal!} - Mark a file
{!info!}'c'{!normal!} - Un-mark all files

{!info!}Space{!normal!} - Expand/Collapse currently selected folder

{!info!}Enter{!normal!} - Show priority popup in which you can set the \
download priority of selected files.

{!info!}Left Arrow{!normal!} - Go back to torrent overview.
"""

class TorrentDetail(BaseMode, component.Component):
    def __init__(self, alltorrentmode, torrentid, stdscr, encoding=None):
        self.alltorrentmode = alltorrentmode
        self.torrentid = torrentid
        self.torrent_state = None
        self.popup = None
        self.messages = deque()
        self._status_keys = ["files", "name","state","download_payload_rate","upload_payload_rate",
                             "progress","eta","all_time_download","total_uploaded", "ratio",
                             "num_seeds","total_seeds","num_peers","total_peers", "active_time",
                             "seeding_time","time_added","distributed_copies", "num_pieces", 
                             "piece_length","save_path","file_progress","file_priorities","message"]
        self._info_fields = [
            ("Name",None,("name",)),
            ("State", None, ("state",)),
            ("Status",None,("message",)),
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
        self.file_list = None
        self.current_file = None
        self.current_file_idx = 0
        self.file_limit = maxint
        self.file_off = 0
        self.more_to_draw = False

        self.column_string = ""
        self.files_sep = None

        self.marked = {}

        BaseMode.__init__(self, stdscr, encoding)
        component.Component.__init__(self, "TorrentDetail", 1, depend=["SessionProxy"])

        self.__split_help()

        self.column_names = ["Filename", "Size", "Progress", "Priority"]
        self._update_columns()

        component.start(["TorrentDetail"])
        curses.curs_set(0)
        self.stdscr.notimeout(0)

    # component start/update
    def start(self):
        component.get("SessionProxy").get_torrent_status(self.torrentid, self._status_keys).addCallback(self.set_state)
    def update(self):
        component.get("SessionProxy").get_torrent_status(self.torrentid, self._status_keys).addCallback(self.set_state)

    def set_state(self, state):
        log.debug("got state")
        if not self.file_list:
            # don't keep getting the files once we've got them once
            if state.get("files"):
                self.files_sep = "{!green,black,bold,underline!}%s"%(("Files (torrent has %d files)"%len(state["files"])).center(self.cols))
                self.file_list,self.file_dict = self.build_file_list(state["files"],state["file_progress"],state["file_priorities"])
                self._status_keys.remove("files")
            else:
                self.files_sep = "{!green,black,bold,underline!}%s"%(("Files (File list unknown)").center(self.cols))
        self._fill_progress(self.file_list,state["file_progress"])
        for i,prio in enumerate(state["file_priorities"]):
            self.file_dict[i][6] = prio
        del state["file_progress"]
        del state["file_priorities"]
        self.torrent_state = state
        self.refresh()

    def __split_help(self):
        self.__help_lines = format_utils.wrap_string(HELP_STR,(self.cols/2)-2)

    # split file list into directory tree. this function assumes all files in a
    # particular directory are returned together.  it won't work otherwise.
    # returned list is a list of lists of the form:
    # [file/dir_name,index,size,children,expanded,progress,priority]
    # for directories index values count down from maxint (for marking usage), 
    # for files the index is the value returned in the
    # state object for use with other libtorrent calls (i.e. setting prio)
    #
    # Also returns a dictionary that maps index values to the file leaves
    # for fast updating of progress and priorities
    def build_file_list(self, file_tuples,prog,prio):
        ret = []
        retdict = {}
        diridx = maxint
        for f in file_tuples:
            cur = ret
            ps = f["path"].split("/")
            fin = ps[-1]
            for p in ps:
                if not cur or p != cur[-1][0]:
                    cl = []
                    if p == fin:
                        ent = [p,f["index"],f["size"],cl,False,
                               format_utils.format_progress(prog[f["index"]]*100),
                               prio[f["index"]]]
                        retdict[f["index"]] = ent
                    else:
                        ent = [p,diridx,-1,cl,False,0,-1]
                        retdict[diridx] = ent
                        diridx-=1
                    cur.append(ent)
                    cur = cl
                else:
                    cur = cur[-1][3]
        self._build_sizes(ret)
        self._fill_progress(ret,prog)
        return (ret,retdict)

    # fill in the sizes of the directory entries based on their children
    def _build_sizes(self, fs):
        ret = 0
        for f in fs:
            if f[2] == -1:
                val = self._build_sizes(f[3])
                ret += val
                f[2] = val
            else:
                ret += f[2]
        return ret

    # fills in progress fields in all entries based on progs
    # returns the # of bytes complete in all the children of fs
    def _fill_progress(self,fs,progs):
        if not progs: return 0
        tb = 0
        for f in fs:
            if f[3]: # dir, has some children
                bd = self._fill_progress(f[3],progs)
                f[5] = format_utils.format_progress((bd/f[2])*100)
            else: # file, update own prog and add to total
                bd = f[2]*progs[f[1]]
                f[5] = format_utils.format_progress(progs[f[1]]*100)
            tb += bd
        return tb

    def _update_columns(self):
        self.column_widths = [-1,15,15,20]
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

        self.column_string = "{!green,black,bold!}%s"%("".join(["%s%s"%(self.column_names[i]," "*(self.column_widths[i]-len(self.column_names[i]))) for i in range(0,len(self.column_names))]))


    def report_message(self,title,message):
        self.messages.append((title,message))

    def clear_marks(self):
        self.marked = {}

    def set_popup(self,pu):
        self.popup = pu
        self.refresh()

            
    def draw_files(self,files,depth,off,idx):
        for fl in files:
            # kick out if we're going to draw too low on the screen
            if (off >= self.rows-1): 
                self.more_to_draw = True
                return -1,-1

            self.file_limit = idx

            if idx >= self.file_off:
                # set fg/bg colors based on if we are selected/marked or not

                # default values
                fg = "white"
                bg = "black"

                if fl[1] in self.marked:
                    bg = "blue"

                if idx == self.current_file_idx:
                    self.current_file = fl
                    bg = "white"
                    if fl[1] in self.marked:
                        fg = "blue"
                    else:
                        fg = "black"

                color_string = "{!%s,%s!}"%(fg,bg)

                #actually draw the dir/file string
                if fl[3] and fl[4]: # this is an expanded directory
                    xchar = 'v'
                elif fl[3]: # collapsed directory
                    xchar = '>'
                else: # file
                    xchar = '-'

                r = format_utils.format_row(["%s%s %s"%(" "*depth,xchar,fl[0]),
                                             deluge.common.fsize(fl[2]),fl[5],
                                             format_utils.format_priority(fl[6])],
                                            self.column_widths)
                
                self.add_string(off,"%s%s"%(color_string,r),trim=False)
                off += 1

            if fl[3] and fl[4]:
                # recurse if we have children and are expanded
                off,idx = self.draw_files(fl[3],depth+1,off,idx+1)
                if off < 0: return (off,idx)
            else:
                idx += 1

        return (off,idx)

    def on_resize(self, *args):
        BaseMode.on_resize_norefresh(self, *args)
        self._update_columns()
        self.__split_help()
        if self.popup:
            self.popup.handle_resize()
        self.refresh()

    def refresh(self,lines=None):
        # show a message popup if there's anything queued
        if self.popup == None and self.messages:
            title,msg = self.messages.popleft()
            self.popup = MessagePopup(self,title,msg)

        # Update the status bars
        self.stdscr.clear()
        self.add_string(0,self.statusbars.topbar)
        hstr =  "%sPress [h] for help"%(" "*(self.cols - len(self.statusbars.bottombar) - 10))
        self.add_string(self.rows - 1, "%s%s"%(self.statusbars.bottombar,hstr))

        if self.files_sep:
            self.add_string((self.rows/2)-1,self.files_sep)

        off = 1
        if self.torrent_state:
            for f in self._info_fields:
                if off >= (self.rows/2): break
                if f[1] != None:
                    args = []
                    try:
                        for key in f[2]:
                            args.append(self.torrent_state[key])
                    except:
                        log.debug("Could not get info field: %s",e)
                        continue
                    info = f[1](*args)
                else:
                    info = self.torrent_state[f[2][0]]
                
                self.add_string(off,"{!info!}%s: {!input!}%s"%(f[0],info))
                off += 1
        else:
            self.add_string(1, "Waiting for torrent state")

        off = self.rows/2
        self.add_string(off,self.column_string)
        if self.file_list:
            off += 1
            self.more_to_draw = False
            self.draw_files(self.file_list,0,off,0)

        #self.stdscr.redrawwin()
        self.stdscr.noutrefresh()

        if self.popup:
            self.popup.refresh()

        curses.doupdate()

    # expand or collapse the current file
    def expcol_cur_file(self):
        self.current_file[4] = not self.current_file[4]
        self.refresh()

    def file_list_down(self):
        if (self.current_file_idx + 1) > self.file_limit:
            if self.more_to_draw:
                self.current_file_idx += 1
                self.file_off += 1
            else:
                return
        else:
            self.current_file_idx += 1

        self.refresh()

    def file_list_up(self):
        self.current_file_idx = max(0,self.current_file_idx-1)
        self.file_off = min(self.file_off,self.current_file_idx)
        self.refresh()

    def back_to_overview(self):
        component.stop(["TorrentDetail"])
        component.deregister("TorrentDetail")
        self.stdscr.clear()
        component.get("ConsoleUI").set_mode(self.alltorrentmode)
        self.alltorrentmode.resume()

    # build list of priorities for all files in the torrent
    # based on what is currently selected and a selected priority.
    def build_prio_list(self, files, ret_list, parent_prio, selected_prio):
        # has a priority been set on my parent (if so, I inherit it)
        for f in files:
            if f[3]: # dir, check if i'm setting on whole dir, then recurse
                if f[1] in self.marked: # marked, recurse and update all children with new prio
                    parent_prio = selected_prio
                    self.build_prio_list(f[3],ret_list,parent_prio,selected_prio)
                    parent_prio = -1
                else: # not marked, just recurse
                    self.build_prio_list(f[3],ret_list,parent_prio,selected_prio)
            else: # file, need to add to list
                if f[1] in self.marked or parent_prio >= 0:
                    # selected (or parent selected), use requested priority
                    ret_list.append((f[1],selected_prio))
                else:
                    # not selected, just keep old priority
                    ret_list.append((f[1],f[6]))

    def do_priority(self, idx, data):
        plist = []
        self.build_prio_list(self.file_list,plist,-1,data)
        plist.sort()
        priorities = [p[1] for p in plist]
        log.debug("priorities: %s", priorities)

        client.core.set_torrent_file_priorities(self.torrentid, priorities)

        if len(self.marked) == 1:
            self.marked = {}
        return True

    # show popup for priority selections
    def show_priority_popup(self):
        if self.marked:
            self.popup = SelectablePopup(self,"Set File Priority",self.do_priority)
            self.popup.add_line("_Do Not Download",data=deluge.common.FILE_PRIORITY["Do Not Download"])
            self.popup.add_line("_Normal Priority",data=deluge.common.FILE_PRIORITY["Normal Priority"])
            self.popup.add_line("_High Priority",data=deluge.common.FILE_PRIORITY["High Priority"])
            self.popup.add_line("H_ighest Priority",data=deluge.common.FILE_PRIORITY["Highest Priority"])

    def _mark_unmark(self,idx):
        if idx in self.marked:
            del self.marked[idx]
        else:
            self.marked[idx] = True

    def _doRead(self):
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
            elif chr(c) == 'q':
                self.back_to_overview()
                return

        if c == 27 or c == curses.KEY_LEFT:
            self.back_to_overview()
            return

        # Navigate the torrent list
        if c == curses.KEY_UP:
            self.file_list_up()
        elif c == curses.KEY_PPAGE:
            pass
        elif c == curses.KEY_DOWN:
            self.file_list_down()
        elif c == curses.KEY_NPAGE:
            pass

        # Enter Key
        elif c == curses.KEY_ENTER or c == 10:
            self.marked[self.current_file[1]] = True
            self.show_priority_popup()

        # space
        elif c == 32:
            self.expcol_cur_file()
        else:
            if c > 31 and c < 256:
                if chr(c) == 'm':
                    if self.current_file:
                        self._mark_unmark(self.current_file[1])
                elif chr(c) == 'c':
                    self.marked = {}
                elif chr(c) == 'a':
                    torrent_actions_popup(self,[self.torrentid],details=False)
                    return
                elif chr(c) == 'h':
                    self.popup = Popup(self,"Help",init_lines=self.__help_lines)

        self.refresh()
