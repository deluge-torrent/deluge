#
# preference_panes.py
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

from deluge.ui.console.modes.input_popup import TextInput,SelectInput,CheckedInput,IntSpinInput

try:
    import curses
except ImportError:
    pass

import logging
log = logging.getLogger(__name__)


class Header:
    def __init__(self, parent, header, space_above, space_below):
        self.parent = parent
        self.header = "{!white,black,bold!}%s"%header
        self.space_above = space_above
        self.space_below = space_below

    def render(self, screen, row, width, active, offset):
        rows = 1
        if self.space_above:
            row += 1
            rows += 1
        self.parent.add_string(row,self.header,screen,offset-1,False,True)
        if self.space_below: rows += 1
        return rows


class BasePane:
    def __init__(self, offset, parent, width):
        self.offset = offset+1
        self.parent = parent
        self.width = width
        self.inputs = []
        self.active_input = -1
        
    def move(self,r,c):
        self._cursor_row = r
        self._cursor_col = c

    def add_config_values(self,conf_dict):
        for ipt in self.inputs:
            if not isinstance(ipt,Header):
                conf_dict[ipt.name] = ipt.get_value()

    def update_values(self, conf_dict):
        for ipt in self.inputs:
            if not isinstance(ipt,Header):
                try:
                    ipt.set_value(conf_dict[ipt.name])
                except KeyError: # just ignore if it's not in dict
                    pass

    def render(self, mode, screen, width, active):
        self._cursor_row = -1
        if self.active_input < 0:
            for i,ipt in enumerate(self.inputs):
                if not isinstance(ipt,Header):
                    self.active_input = i
                    break                    
        crow = 1
        for i,ipt in enumerate(self.inputs):
            act = active and i==self.active_input
            crow += ipt.render(screen,crow,width, act, self.offset)

        if active and self._cursor_row >= 0:
            curses.curs_set(2)
            screen.move(self._cursor_row,self._cursor_col+self.offset-1)
        else:
            curses.curs_set(0)

    # just handles setting the active input
    def handle_read(self,c):
        if not self.inputs: # no inputs added yet
            return

        if c == curses.KEY_UP:
            nc = max(0,self.active_input-1)
            while isinstance(self.inputs[nc], Header):
                nc-=1
                if nc <= 0: break
            if not isinstance(self.inputs[nc], Header):
                self.active_input = nc
        elif c == curses.KEY_DOWN:
            ilen = len(self.inputs)
            nc = min(self.active_input+1,ilen-1)
            while isinstance(self.inputs[nc], Header):
                nc+=1
                if nc >= ilen: break
            if not isinstance(self.inputs[nc], Header):
                self.active_input = nc
        else:
            self.inputs[self.active_input].handle_read(c)


    def add_header(self, header, space_above=False, space_below=False):
        self.inputs.append(Header(self.parent, header, space_above, space_below))

    def add_text_input(self, name, msg, dflt_val):
        self.inputs.append(TextInput(self.parent,self.move,self.width,msg,name,dflt_val,False))

    def add_select_input(self, name, msg, opts, vals, selidx):
        self.inputs.append(SelectInput(self.parent,msg,name,opts,vals,selidx))

    def add_checked_input(self, name, message, checked):
        self.inputs.append(CheckedInput(self.parent,message,name,checked))

    def add_int_spin_input(self, name, message, value, min_val, max_val):
        self.inputs.append(IntSpinInput(self.parent,message,name,self.move,value,min_val,max_val))


class DownloadsPane(BasePane):
    def __init__(self, offset, parent, width):
        BasePane.__init__(self,offset,parent,width)

        self.add_header("Folders")
        self.add_text_input("download_location","Download To:",parent.core_config["download_location"])
        self.add_header("Allocation")

        if parent.core_config["compact_allocation"]:
            alloc_idx = 1
        else:
            alloc_idx = 0
        self.add_select_input("compact_allocation","Allocation:",["Use Full Allocation","Use Compact Allocation"],[False,True],alloc_idx)
        self.add_header("Options",True)
        self.add_checked_input("prioritize_first_last_pieces","Prioritize first and last pieces of torrent",parent.core_config["prioritize_first_last_pieces"])
        self.add_checked_input("add_paused","Add torrents in paused state",parent.core_config["add_paused"])


class NetworkPane(BasePane):
    def __init__(self, offset, parent, width):
        BasePane.__init__(self,offset,parent,width)

class BandwidthPane(BasePane):
    def __init__(self, offset, parent, width):
        BasePane.__init__(self,offset,parent,width)
        self.add_header("Global Bandwidth Usage")
        self.add_int_spin_input("max_connections_global","Maximum Connections:",parent.core_config["max_connections_global"],0,1000)
        self.add_int_spin_input("max_upload_slots_global","Maximum Upload Slots:",parent.core_config["max_upload_slots_global"],0,1000)
        #self.add_int_spin_input("max_download_speed","Maximum Download Speed (KiB/s):",-1,0,1000)

class InterfacePane(BasePane):
    def __init__(self, offset, parent, width):
        BasePane.__init__(self,offset,parent,width)
        # does classic mode make sense in console?
        #self.add_header("Classic Mode")
        #self.add_checked_input("classic_mode","Enable",False)
        
        # add title bar control here

class OtherPane(BasePane):
    def __init__(self, offset, parent, width):
        BasePane.__init__(self,offset,parent,width)
        self.add_header("GeoIP Database")
        self.add_text_input("geoip_db_location","Location:",parent.core_config["geoip_db_location"])

class DaemonPane(BasePane):
    def __init__(self, offset, parent, width):
        BasePane.__init__(self,offset,parent,width)
        self.add_header("Port")
        self.add_int_spin_input("daemon_port","Daemon Port:",parent.core_config["daemon_port"],0,1000)
        self.add_header("Connections",True)
        self.add_checked_input("allow_remote","Allow remote connections",parent.core_config["allow_remote"])
        self.add_header("Other",True)
        self.add_checked_input("new_release_check","Periodically check the website for new releases",parent.core_config["new_release_check"])

class QueuePane(BasePane):
    def __init__(self, offset, parent, width):
        BasePane.__init__(self,offset,parent,width)

class ProxyPane(BasePane):
    def __init__(self, offset, parent, width):
        BasePane.__init__(self,offset,parent,width)

class CachePane(BasePane):
    def __init__(self, offset, parent, width):
        BasePane.__init__(self,offset,parent,width)
