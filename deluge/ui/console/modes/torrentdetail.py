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

from deluge.ui.sessionproxy import SessionProxy

from popup import Popup,SelectablePopup,MessagePopup
from add_util import add_torrent
from input_popup import InputPopup
import format_utils


try:
    import curses
except ImportError:
    pass

import logging
log = logging.getLogger(__name__)


class TorrentDetail(BaseMode, component.Component):
    def __init__(self, alltorrentmode, torrentid, stdscr, encoding=None):
        self.alltorrentmode = alltorrentmode
        self.torrentid = torrentid
        self.torrent_state = None
        self._status_keys = ["files", "name","state","download_payload_rate","upload_payload_rate",
                             "progress","eta","all_time_download","total_uploaded", "ratio",
                             "num_seeds","total_seeds","num_peers","total_peers", "active_time",
                             "seeding_time","time_added","distributed_copies", "num_pieces", 
                             "piece_length","save_path","file_progress","file_priorities"]
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
        self.file_list = None
        self.current_file = None
        self.current_file_idx = 0
        self.file_limit = maxint
        self.file_off = 0
        self.more_to_draw = False

        self.column_string = ""

        BaseMode.__init__(self, stdscr, encoding)
        component.Component.__init__(self, "TorrentDetail", 1, depend=["SessionProxy"])

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
            self.file_list,self.file_dict = self.build_file_list(state["files"],state["file_progress"],state["file_priorities"])
            self._status_keys.remove("files")
        self._fill_progress(self.file_list,state["file_progress"])
        for i,prio in enumerate(state["file_priorities"]):
            self.file_dict[i][6] = format_utils.format_priority(prio)
        del state["file_progress"]
        del state["file_priorities"]
        self.torrent_state = state
        self.refresh()

    # split file list into directory tree. this function assumes all files in a
    # particular directory are returned together.  it won't work otherwise.
    # returned list is a list of lists of the form:
    # [file/dir_name,index,size,children,expanded,progress,priority]
    # for directories index will be -1, for files the value returned in the
    # state object for use with other libtorrent calls (i.e. setting prio)
    #
    # Also returns a dictionary that maps index values to the file leaves
    # for fast updating of progress and priorities
    def build_file_list(self, file_tuples,prog,prio):
        ret = []
        retdict = {}
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
                               format_utils.format_priority(prio[f["index"]])]
                        retdict[f["index"]] = ent
                    else:
                        ent = [p,-1,-1,cl,False,"-","-"]
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

        self.column_string = "{!header!}%s"%("".join(["%s%s"%(self.column_names[i]," "*(self.column_widths[i]-len(self.column_names[i]))) for i in range(0,len(self.column_names))]))

            
    def draw_files(self,files,depth,off,idx):
        for fl in files:
            # kick out if we're going to draw too low on the screen
            if (off >= self.rows-1): 
                self.more_to_draw = True
                return -1,-1

            self.file_limit = idx

            if idx >= self.file_off:
                # set fg/bg colors based on if we are selected or not
                if idx == self.current_file_idx:
                    self.current_file = fl
                    fc = "{!black,white!}"
                else:
                    fc = "{!white,black!}"

                #actually draw the dir/file string
                if fl[3] and fl[4]: # this is an expanded directory
                    xchar = 'v'
                elif fl[3]: # collapsed directory
                    xchar = '>'
                else: # file
                    xchar = '-'

                r = format_utils.format_row(["%s%s %s"%(" "*depth,xchar,fl[0]),
                                             deluge.common.fsize(fl[2]),fl[5],fl[6]],
                                            self.column_widths)
                
                self.add_string(off,"%s%s"%(fc,r),trim=False)
                off += 1

            if fl[3] and fl[4]:
                # recurse if we have children and are expanded
                off,idx = self.draw_files(fl[3],depth+1,off,idx+1)
                if off < 0: return (off,idx)
            else:
                idx += 1

        return (off,idx)

    def refresh(self,lines=None):
        # Update the status bars
        self.stdscr.clear()
        self.add_string(0,self.statusbars.topbar)
        hstr =  "%sPress [h] for help"%(" "*(self.cols - len(self.statusbars.bottombar) - 10))
        self.add_string(self.rows - 1, "%s%s"%(self.statusbars.bottombar,hstr))

        self.stdscr.hline((self.rows/2)-1,0,"_",self.cols)

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

    def _doRead(self):
        c = self.stdscr.getch()

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

        if c == 27:
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
            pass

        # space
        elif c == 32:
            self.expcol_cur_file()

        self.refresh()
