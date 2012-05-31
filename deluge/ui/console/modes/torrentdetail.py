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
import deluge.common as common
from deluge.ui.client import client

from sys import maxint
from collections import deque

from deluge.ui.sessionproxy import SessionProxy

from popup import Popup,SelectablePopup,MessagePopup
from add_util import add_torrent
from input_popup import InputPopup
import deluge.ui.console.colors as colors
import format_utils

from torrent_actions import torrent_actions_popup, ACTION

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
    def __init__(self, alltorrentmode, torrentid, stdscr, console_config, encoding=None):

        self.console_config = console_config
        self.alltorrentmode = alltorrentmode
        self.torrentid = torrentid
        self.torrent_state = None
        self.popup = None
        self.messages = deque()
        self._status_keys = ["files", "name","state","download_payload_rate","upload_payload_rate",
                             "progress","eta","all_time_download","total_uploaded", "ratio",
                             "num_seeds","total_seeds","num_peers","total_peers", "active_time",
                             "seeding_time","time_added","distributed_copies", "num_pieces",
                             "piece_length","save_path","file_progress","file_priorities","message",
                             "total_wanted", "tracker_host", "owner"]

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
        self.__update_columns()

        component.start(["TorrentDetail"])

        self._listing_start = self.rows // 2
        self._listing_space = self._listing_start - self._listing_start

        curses.curs_set(0)
        self.stdscr.notimeout(0)

    # component start/update
    def start(self):
        component.get("SessionProxy").get_torrent_status(self.torrentid, self._status_keys).addCallback(self.set_state)
    def update(self):
        component.get("SessionProxy").get_torrent_status(self.torrentid, self._status_keys).addCallback(self.set_state)

    def set_state(self, state):
        log.debug("got state")
        need_prio_update = False
        if not self.file_list:
            # don't keep getting the files once we've got them once
            if state.get("files"):
                self.files_sep = "{!green,black,bold,underline!}%s"%(("Files (torrent has %d files)"%len(state["files"])).center(self.cols))
                self.file_list,self.file_dict = self.build_file_list(state["files"],state["file_progress"],state["file_priorities"])
                self._status_keys.remove("files")
            else:
                self.files_sep = "{!green,black,bold,underline!}%s"%(("Files (File list unknown)").center(self.cols))
            need_prio_update = True
        self.__fill_progress(self.file_list,state["file_progress"])
        for i,prio in enumerate(state["file_priorities"]):
            if self.file_dict[i][6] != prio:
                need_prio_update = True
                self.file_dict[i][6] = prio
        if need_prio_update:
            self.__fill_prio(self.file_list)
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
        self.__build_sizes(ret)
        self.__fill_progress(ret,prog)
        return (ret,retdict)

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
    def __fill_progress(self,fs,progs):
        if not progs: return 0
        tb = 0
        for f in fs:
            if f[3]: # dir, has some children
                bd = self.__fill_progress(f[3],progs)
                f[5] = format_utils.format_progress((bd/f[2])*100)
            else: # file, update own prog and add to total
                bd = f[2]*progs[f[1]]
                f[5] = format_utils.format_progress(progs[f[1]]*100)
            tb += bd
        return tb

    def __fill_prio(self,fs):
        for f in fs:
            if f[3]: # dir, so fill in children and compute our prio
                self.__fill_prio(f[3])
                s = set([e[6] for e in f[3]]) # pull out all child prios and turn into a set
                if len(s) > 1:
                    f[6] = -2  # mixed
                else:
                    f[6] = s.pop()

    def __update_columns(self):
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

        color_selected = "blue"
        color_partially_selected = "magenta"
        color_highlighted = "white"
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
                    bg = color_selected
                    if fl[3]:
                        if self.marked[fl[1]] < self.__get_contained_files_count(file_list=fl[3]):
                            bg = color_partially_selected

                if idx == self.current_file_idx:
                    self.current_file = fl
                    bg = color_highlighted
                    if fl[1] in self.marked:
                        fg = color_selected
                        if fl[3]:
                            if self.marked[fl[1]] < self.__get_contained_files_count(file_list = fl[3]):
                                fg = color_partially_selected
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

    def __get_file_list_length(self, file_list=None):
        """
        Counts length of the displayed file list.
        """
        if file_list == None:
            file_list = self.file_list
        length = 0
        if file_list:
            for element in file_list:
                length += 1
                if element[3] and element[4]:
                    length += self.__get_file_list_length(element[3])
        return length

    def __get_contained_files_count(self, file_list=None, idx = None):
        length = 0
        if file_list == None:
            file_list = self.file_list
        if idx != None:
            for element in file_list:
                if   element[1] == idx:
                    return self.__get_contained_files_count(file_list = element[3])
                elif element[3]:
                    c = self.__get_contained_files_count(file_list = element[3], idx=idx)
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

        #Always refresh Legacy(it will also refresh AllTorrents), otherwise it will bug deluge out
        legacy = component.get("LegacyUI")
        legacy.on_resize(*args)

        self.__update_columns()
        self.__split_help()
        if self.popup:
            self.popup.handle_resize()

        self._listing_start = self.rows / 2
        self.refresh()

    def render_header(self, off):
        status = self.torrent_state

        up_color = colors.state_color["Seeding"]
        down_color = colors.state_color["Downloading"]

        #Name
        s = "{!info!}Name: {!input!}%s" % status["name"]
        self.add_string(off, s); off += 1

        #Print DL info and ETA
        if status["download_payload_rate"] > 0:
            s = "%sDownloading: {!input!}" % down_color
        else:
            s = "{!info!}Downloaded: {!input!}"
        s+= common.fsize(status["all_time_download"])
        if status["progress"] != 100.0:
            s+= "/%s" % common.fsize(status["total_wanted"])
        if status["download_payload_rate"] > 0:
            s+= " {!yellow!}@ %s%s" % (down_color, common.fsize(status["download_payload_rate"]))
            s+= "{!info!} ETA: {!input!}%s" % format_utils.format_time(status["eta"])
        self.add_string(off, s); off += 1

        #Print UL info and ratio
        if status["upload_payload_rate"] > 0:
            s = "%sUploading: {!input!}" % up_color
        else:
            s = "{!info!}Uploaded: {!input!}"
        s+= common.fsize(status["total_uploaded"])
        if status["upload_payload_rate"] > 0:
            s+= " {!yellow!}@ %s%s" % (up_color, common.fsize(status["upload_payload_rate"]))
        s+= " {!info!}Ratio: {!input!}%s" % format_utils.format_float(status["ratio"])
        self.add_string(off, s); off += 1

        #Seeder/leecher info
        s = "{!info!}Seeders:{!green!} %s {!input!}(%s)" % (status["num_seeds"], status["total_seeds"])
        self.add_string(off, s); off += 1
        s = "{!info!}Leechers:{!red!} %s {!input!}(%s)" % (status["num_peers"], status["total_peers"])
        self.add_string(off, s); off += 1

        #Tracker
        if status["message"] == "OK":
            color = "{!green!}"
        else:
            color = "{!red!}"
        s = "{!info!}Tracker: {!magenta!}%s{!input!} says \"%s%s{!input!}\"" % (status["tracker_host"], color, status["message"])
        self.add_string(off, s); off += 1

        #Pieces and availability
        s = "{!info!}Pieces: {!yellow!}%s {!input!}x {!yellow!}%s" % (status["num_pieces"], common.fsize(status["piece_length"]))
        if status["distributed_copies"]:
            s+= " {!info!}Availability: {!input!}%s" % format_utils.format_float(status["distributed_copies"])
        self.add_string(off, s); off += 1

        #Time added
        s = "{!info!}Added: {!input!}%s" % common.fdate(status["time_added"])
        self.add_string(off, s); off += 1

        #Time active
        s = "{!info!}Time active: {!input!}%s" % ( common.ftime(status["active_time"]) )
        if status["seeding_time"]:
            s+= ", {!cyan!}%s{!input!} seeding" % ( common.ftime(status["seeding_time"]) )
        self.add_string(off, s); off += 1

        #Save Path
        s = "{!info!}Save path: {!input!}%s" % status["save_path"]
        self.add_string(off, s); off += 1

        #Owner
        if status["owner"]:
            s = "{!info!}Owner: {!input!}%s" % status["owner"]

        return off

    def refresh(self,lines=None):
        # show a message popup if there's anything queued
        if self.popup == None and self.messages:
            title,msg = self.messages.popleft()
            self.popup = MessagePopup(self,title,msg)

        # Update the status bars
        self.stdscr.erase()
        self.add_string(0,self.statusbars.topbar)

        #This will quite likely fail when switching modes
        try:
            rf = format_utils.remove_formatting
            string = self.statusbars.bottombar
            hstr = "Press {!magenta,blue,bold!}[h]{!status!} for help"

            string += " " * ( self.cols - len(rf(string)) - len(rf(hstr))) + hstr

            self.add_string(self.rows - 1, string)
        except:
            pass

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

        self.add_string(off,self.column_string)
        if self.file_list:
            off += 1
            self.more_to_draw = False
            self.draw_files(self.file_list,0,off,0)

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

        if self.current_file_idx > self.file_off  + (self._listing_space - 3):
            self.file_off = self.current_file_idx - (self._listing_space - 3)

        self.refresh()

    def file_list_up(self, rows=1):
        self.current_file_idx = max(0,self.current_file_idx-rows)
        self.file_off = min(self.file_off,self.current_file_idx)
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
            #Do not set priorities for the whole dir, just selected contents
            if f[3]:
                self.build_prio_list(f[3],ret_list,parent_prio,selected_prio)
            else: # file, need to add to list
                if f[1] in self.marked or parent_prio >= 0:
                    # selected (or parent selected), use requested priority
                    ret_list.append((f[1],selected_prio))
                else:
                    # not selected, just keep old priority
                    ret_list.append((f[1],f[6]))

    def do_priority(self, idx, data, was_empty):
        plist = []
        self.build_prio_list(self.file_list,plist,-1,data)
        plist.sort()
        priorities = [p[1] for p in plist]
        log.debug("priorities: %s", priorities)

        client.core.set_torrent_file_priorities(self.torrentid, priorities)

        if was_empty:
            self.marked = {}
        return True

    # show popup for priority selections
    def show_priority_popup(self, was_empty):
        func = lambda idx, data, we=was_empty: self.do_priority(idx, data, we)
        if self.marked:
            self.popup = SelectablePopup(self,"Set File Priority", func)
            self.popup.add_line("_Do Not Download",data=deluge.common.FILE_PRIORITY["Do Not Download"])
            self.popup.add_line("_Normal Priority",data=deluge.common.FILE_PRIORITY["Normal Priority"])
            self.popup.add_line("_High Priority",data=deluge.common.FILE_PRIORITY["High Priority"])
            self.popup.add_line("H_ighest Priority",data=deluge.common.FILE_PRIORITY["Highest Priority"])

    def __mark_unmark(self,idx):
        """
        Selects or unselects file or a catalog(along with contained files)
        """
        fc = self.__get_contained_files_count(idx=idx)
        if idx not in self.marked:
            #Not selected, select it
            self.__mark_tree(self.file_list, idx)
        elif self.marked[idx] < fc:
            #Partially selected, unselect all contents
            self.__unmark_tree(self.file_list, idx)
        else:
            #Selected, unselect it
            self.__unmark_tree(self.file_list, idx)

    def __mark_tree(self, file_list, idx, mark_all = False):
        """
        Given file_list of TorrentDetail and index of file or folder,
        recursively selects all files contained
        as well as marks folders higher in hierarchy as partially selected
        """
        total_marked = 0
        for element in file_list:
            marked = 0
            #Select the file if it's the one we want or
            # if it's inside a directory that got selected
            if (element[1] == idx) or mark_all:
                #If it's a folder then select everything inside
                if element[3]:
                    marked = self.__mark_tree(element[3], idx, True)
                    self.marked[element[1]] = marked
                else:
                    marked = 1
                    self.marked[element[1]] = 1
            else:
                #Does not match but the item to be selected might be inside, recurse
                if element[3]:
                    marked = self.__mark_tree(element[3], idx, False)
                    #Partially select the folder if it contains files that were selected
                    if marked > 0:
                        self.marked[element[1]] = marked
                else:
                    if element[1] in self.marked:
                        #It's not the element we want but it's marked so count it
                        marked = 1
            #Count and then return total amount of files selected in all subdirectories
            total_marked += marked

        return total_marked

    def __unmark_tree(self, file_list, idx, unmark_all = False):
        """
        Given file_list of TorrentDetail and index of file or folder,
        recursively deselects all files contained
        as well as marks folders higher in hierarchy as unselected or partially selected
        """
        total_marked = 0
        for element in file_list:
            marked = 0
            #It's either the item we want to select or
            # a contained item, deselect it
            if (element[1] == idx) or unmark_all:
                if element[1] in self.marked:
                    del self.marked[element[1]]
                    #Deselect all contents if it's a catalog
                    if element[3]:
                        self.__unmark_tree(element[3], idx, True)
            else:
                #Not file we wanted but it might be inside this folder, recurse inside
                if element[3]:
                    marked = self.__unmark_tree(element[3], idx, False)
                    #If none of the contents remain selected, unselect this folder as well
                    if marked == 0:
                        if element[1] in self.marked:
                            del self.marked[element[1]]
                    #Otherwise update selection count
                    else:
                        self.marked[element[1]] = marked
                else:
                    if element[1] in self.marked:
                        marked = 1

            #Count and then return selection count so we can update
            # directories higher up in the hierarchy
            total_marked += marked
        return total_marked

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

        if not self.torrent_state:
            # actions below only makes sense if there is a torrent state
            return

        # Navigate the torrent list
        if c == curses.KEY_UP:
            self.file_list_up()
        elif c == curses.KEY_PPAGE:
            self.file_list_up(self._listing_space-2)
        elif c == curses.KEY_HOME:
            self.file_off = 0
            self.current_file_idx = 0
        elif c == curses.KEY_DOWN:
            self.file_list_down()
        elif c == curses.KEY_NPAGE:
            self.file_list_down(self._listing_space-2)
        elif c == curses.KEY_END:
            self.current_file_idx = self.__get_file_list_length() - 1
            self.file_off = self.current_file_idx - (self._listing_space - 3)
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
                if chr(c) == 'm':
                    if self.current_file:
                        self.__mark_unmark(self.current_file[1])
                elif chr(c) == 'c':
                    self.marked = {}
                elif chr(c) == 'a':
                    torrent_actions_popup(self,[self.torrentid],details=False)
                    return
                elif chr(c) == 'o':
                    torrent_actions_popup(self,[self.torrentid],action=ACTION.TORRENT_OPTIONS)
                    return
                elif chr(c) == 'h':
                    self.popup = Popup(self,"Help",init_lines=self.__help_lines, height_req=0.75)

        self.refresh()
