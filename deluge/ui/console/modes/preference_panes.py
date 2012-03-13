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

from deluge.ui.console.modes.input_popup import TextInput,SelectInput,CheckedInput,IntSpinInput,FloatSpinInput,CheckedPlusInput
import deluge.ui.console.modes.alltorrents

try:
    import curses
except ImportError:
    pass

import logging
log = logging.getLogger(__name__)


class NoInput:
    def depend_skip(self):
        return False

class Header(NoInput):
    def __init__(self, parent, header, space_above, space_below):
        self.parent = parent
        self.header = "{!white,black,bold!}%s"%header
        self.space_above = space_above
        self.space_below = space_below
        self.name = header

    def render(self, screen, row, width, active, offset):
        rows = 1
        if self.space_above:
            row += 1
            rows += 1
        self.parent.add_string(row,self.header,screen,offset-1,False,True)
        if self.space_below: rows += 1
        return rows

class InfoField(NoInput):
    def __init__(self,parent,label,value,name):
        self.parent = parent
        self.label = label
        self.value = value
        self.txt = "%s %s"%(label,value)
        self.name = name

    def render(self, screen, row, width, active, offset):
        self.parent.add_string(row,self.txt,screen,offset-1,False,True)
        return 1

    def set_value(self, v):
        self.value = v
        if type(v) == float:
            self.txt = "%s %.2f"%(self.label,self.value)
        else:
            self.txt = "%s %s"%(self.label,self.value)

class BasePane:
    def __init__(self, offset, parent, width):
        self.offset = offset+1
        self.parent = parent
        self.width = width
        self.inputs = []
        self.active_input = -1

        # have we scrolled down in the list
        self.input_offset = 0

    def move(self,r,c):
        self._cursor_row = r
        self._cursor_col = c

    def add_config_values(self,conf_dict):
        for ipt in self.inputs:
            if not isinstance(ipt,NoInput):
                # gross, have to special case in/out ports since they are tuples
                if ipt.name in ("listen_ports_to","listen_ports_from",
                                "out_ports_from","out_ports_to"):
                    if ipt.name == "listen_ports_to":
                        conf_dict["listen_ports"] = (self.infrom.get_value(),self.into.get_value())
                    if ipt.name == "out_ports_to":
                        conf_dict["outgoing_ports"] = (self.outfrom.get_value(),self.outto.get_value())
                else:
                    conf_dict[ipt.name] = ipt.get_value()
                if hasattr(ipt,"get_child"):
                    c = ipt.get_child()
                    conf_dict[c.name] = c.get_value()

    def update_values(self, conf_dict):
        for ipt in self.inputs:
            if not isinstance(ipt,NoInput):
                try:
                    ipt.set_value(conf_dict[ipt.name])
                except KeyError: # just ignore if it's not in dict
                    pass
                if hasattr(ipt,"get_child"):
                    try:
                        c = ipt.get_child()
                        c.set_value(conf_dict[c.name])
                    except KeyError: # just ignore if it's not in dict
                        pass

    def render(self, mode, screen, width, active):
        self._cursor_row = -1
        if self.active_input < 0:
            for i,ipt in enumerate(self.inputs):
                if not isinstance(ipt,NoInput):
                    self.active_input = i
                    break
        drew_act = not active
        crow = 1
        for i,ipt in enumerate(self.inputs):
            if ipt.depend_skip() or i<self.input_offset:
                if active and i==self.active_input:
                    self.input_offset-=1
                    mode.refresh()
                    return 0
                continue
            act = active and i==self.active_input
            if act: drew_act = True
            crow += ipt.render(screen,crow,width, act, self.offset)
            if crow >= (mode.prefs_height):
                break

        if not drew_act:
            self.input_offset+=1
            mode.refresh()
            return 0

        if active and self._cursor_row >= 0:
            curses.curs_set(2)
            screen.move(self._cursor_row,self._cursor_col+self.offset-1)
        else:
            curses.curs_set(0)

        return crow

    # just handles setting the active input
    def handle_read(self,c):
        if not self.inputs: # no inputs added yet
            return

        if c == curses.KEY_UP:
            nc = max(0,self.active_input-1)
            while isinstance(self.inputs[nc], NoInput) or self.inputs[nc].depend_skip():
                nc-=1
                if nc <= 0: break
            if not isinstance(self.inputs[nc], NoInput) or self.inputs[nc].depend_skip():
                self.active_input = nc
        elif c == curses.KEY_DOWN:
            ilen = len(self.inputs)
            nc = min(self.active_input+1,ilen-1)
            while isinstance(self.inputs[nc], NoInput) or self.inputs[nc].depend_skip():
                nc+=1
                if nc >= ilen:
                    nc-=1
                    break
            if not isinstance(self.inputs[nc], NoInput) or self.inputs[nc].depend_skip():
                self.active_input = nc
        else:
            self.inputs[self.active_input].handle_read(c)


    def add_header(self, header, space_above=False, space_below=False):
        self.inputs.append(Header(self.parent, header, space_above, space_below))

    def add_info_field(self, label, value, name):
        self.inputs.append(InfoField(self.parent, label, value, name))

    def add_text_input(self, name, msg, dflt_val):
        self.inputs.append(TextInput(self.parent,self.move,self.width,msg,name,dflt_val,False))

    def add_select_input(self, name, msg, opts, vals, selidx):
        self.inputs.append(SelectInput(self.parent,msg,name,opts,vals,selidx))

    def add_checked_input(self, name, message, checked):
        self.inputs.append(CheckedInput(self.parent,message,name,checked))

    def add_checkedplus_input(self, name, message, child, checked):
        self.inputs.append(CheckedPlusInput(self.parent,message,name,child,checked))

    def add_int_spin_input(self, name, message, value, min_val, max_val):
        self.inputs.append(IntSpinInput(self.parent,message,name,self.move,value,min_val,max_val))

    def add_float_spin_input(self, name, message, value, inc_amt, precision, min_val, max_val):
        self.inputs.append(FloatSpinInput(self.parent,message,name,self.move,value,inc_amt,precision,min_val,max_val))


class DownloadsPane(BasePane):
    def __init__(self, offset, parent, width):
        BasePane.__init__(self,offset,parent,width)

        self.add_header("Folders")
        self.add_text_input("download_location","Download To:",parent.core_config["download_location"])
        cmptxt = TextInput(self.parent,self.move,self.width,None,"move_completed_path",parent.core_config["move_completed_path"],False)
        self.add_checkedplus_input("move_completed","Move completed to:",cmptxt,parent.core_config["move_completed"])
        autotxt = TextInput(self.parent,self.move,self.width,None,"autoadd_location",parent.core_config["autoadd_location"],False)
        self.add_checkedplus_input("autoadd_enable","Auto add .torrents from:",autotxt,parent.core_config["autoadd_enable"])
        copytxt = TextInput(self.parent,self.move,self.width,None,"torrentfiles_location",parent.core_config["torrentfiles_location"],False)
        self.add_checkedplus_input("copy_torrent_file","Copy of .torrent files to:",copytxt,parent.core_config["copy_torrent_file"])
        self.add_checked_input("del_copy_torrent_file","Delete copy of torrent file on remove",parent.core_config["del_copy_torrent_file"])

        self.add_header("Allocation",True)

        if parent.core_config["compact_allocation"]:
            alloc_idx = 1
        else:
            alloc_idx = 0
        self.add_select_input("compact_allocation",None,["Use Full Allocation","Use Compact Allocation"],[False,True],alloc_idx)
        self.add_header("Options",True)
        self.add_checked_input("prioritize_first_last_pieces","Prioritize first and last pieces of torrent",parent.core_config["prioritize_first_last_pieces"])
        self.add_checked_input("add_paused","Add torrents in paused state",parent.core_config["add_paused"])


class NetworkPane(BasePane):
    def __init__(self, offset, parent, width):
        BasePane.__init__(self,offset,parent,width)
        self.add_header("Incomming Ports")
        inrand = CheckedInput(parent,"Use Random Ports    Active Port: %d"%parent.active_port,"random_port",parent.core_config["random_port"])
        self.inputs.append(inrand)
        listen_ports = parent.core_config["listen_ports"]
        self.infrom = IntSpinInput(self.parent,"  From:","listen_ports_from",self.move,listen_ports[0],0,65535)
        self.infrom.set_depend(inrand,True)
        self.into = IntSpinInput(self.parent,"  To:  ","listen_ports_to",self.move,listen_ports[1],0,65535)
        self.into.set_depend(inrand,True)
        self.inputs.append(self.infrom)
        self.inputs.append(self.into)


        self.add_header("Outgoing Ports",True)
        outrand = CheckedInput(parent,"Use Random Ports","random_outgoing_ports",parent.core_config["random_outgoing_ports"])
        self.inputs.append(outrand)
        out_ports = parent.core_config["outgoing_ports"]
        self.outfrom = IntSpinInput(self.parent,"  From:","out_ports_from",self.move,out_ports[0],0,65535)
        self.outfrom.set_depend(outrand,True)
        self.outto = IntSpinInput(self.parent,"  To:  ","out_ports_to",self.move,out_ports[1],0,65535)
        self.outto.set_depend(outrand,True)
        self.inputs.append(self.outfrom)
        self.inputs.append(self.outto)


        self.add_header("Interface",True)
        self.add_text_input("listen_interface","IP address of the interface to listen on (leave empty for default):",parent.core_config["listen_interface"])

        self.add_header("TOS",True)
        self.add_text_input("peer_tos","Peer TOS Byte:",parent.core_config["peer_tos"])

        self.add_header("Network Extras")
        self.add_checked_input("upnp","UPnP",parent.core_config["upnp"])
        self.add_checked_input("natpmp","NAT-PMP",parent.core_config["natpmp"])
        self.add_checked_input("utpex","Peer Exchange",parent.core_config["utpex"])
        self.add_checked_input("lsd","LSD",parent.core_config["lsd"])
        self.add_checked_input("dht","DHT",parent.core_config["dht"])

        self.add_header("Encryption",True)
        self.add_select_input("enc_in_policy","Inbound:",["Forced","Enabled","Disabled"],[0,1,2],parent.core_config["enc_in_policy"])
        self.add_select_input("enc_out_policy","Outbound:",["Forced","Enabled","Disabled"],[0,1,2],parent.core_config["enc_out_policy"])
        self.add_select_input("enc_level","Level:",["Handshake","Full Stream","Either"],[0,1,2],parent.core_config["enc_level"])
        self.add_checked_input("enc_prefer_rc4","Encrypt Entire Stream",parent.core_config["enc_prefer_rc4"])


class BandwidthPane(BasePane):
    def __init__(self, offset, parent, width):
        BasePane.__init__(self,offset,parent,width)
        self.add_header("Global Bandwidth Usage")
        self.add_int_spin_input("max_connections_global","Maximum Connections:",parent.core_config["max_connections_global"],-1,9000)
        self.add_int_spin_input("max_upload_slots_global","Maximum Upload Slots:",parent.core_config["max_upload_slots_global"],-1,9000)
        self.add_float_spin_input("max_download_speed","Maximum Download Speed (KiB/s):",parent.core_config["max_download_speed"],1.0,1,-1.0,60000.0)
        self.add_float_spin_input("max_upload_speed","Maximum Upload Speed (KiB/s):",parent.core_config["max_upload_speed"],1.0,1,-1.0,60000.0)
        self.add_int_spin_input("max_half_open_connections","Maximum Half-Open Connections:",parent.core_config["max_half_open_connections"],-1,9999)
        self.add_int_spin_input("max_connections_per_second","Maximum Connection Attempts per Second:",parent.core_config["max_connections_per_second"],-1,9999)
        self.add_checked_input("ignore_limits_on_local_network","Ignore limits on local network",parent.core_config["ignore_limits_on_local_network"])
        self.add_checked_input("rate_limit_ip_overhead","Rate Limit IP Overhead",parent.core_config["rate_limit_ip_overhead"])
        self.add_header("Per Torrent Bandwidth Usage",True)
        self.add_int_spin_input("max_connections_per_torrent","Maximum Connections:",parent.core_config["max_connections_per_torrent"],-1,9000)
        self.add_int_spin_input("max_upload_slots_per_torrent","Maximum Upload Slots:",parent.core_config["max_upload_slots_per_torrent"],-1,9000)
        self.add_float_spin_input("max_download_speed_per_torrent","Maximum Download Speed (KiB/s):",parent.core_config["max_download_speed_per_torrent"],1.0,1,-1.0,60000.0)
        self.add_float_spin_input("max_upload_speed_per_torrent","Maximum Upload Speed (KiB/s):",parent.core_config["max_upload_speed_per_torrent"],1.0,1,-1.0,60000.0)

class InterfacePane(BasePane):
    def __init__(self, offset, parent, width):
        BasePane.__init__(self,offset,parent,width)
        self.add_header("General")
        self.add_checked_input("ignore_duplicate_lines","Do not store duplicate input in history",parent.console_config["ignore_duplicate_lines"])
        self.add_checked_input("move_selection","Move selection when moving torrents in the queue",parent.console_config["move_selection"])
        self.add_checked_input("third_tab_lists_all","Third tab lists all remaining torrents in legacy mode",parent.console_config["third_tab_lists_all"])
        self.add_int_spin_input("torrents_per_tab_press","Torrents per tab press",parent.console_config["torrents_per_tab_press"], 5, 100)

        self.add_header("Columns To Display", True)
        for cpn in deluge.ui.console.modes.alltorrents.column_pref_names:
            pn = "show_%s"%cpn
            self.add_checked_input(pn,
                                   deluge.ui.console.modes.alltorrents.prefs_to_names[cpn],
                                   parent.console_config[pn])
        self.add_header("Column Widths (-1 = expand)",True)
        for cpn in deluge.ui.console.modes.alltorrents.column_pref_names:
            pn = "%s_width"%cpn
            self.add_int_spin_input(pn,
                                    deluge.ui.console.modes.alltorrents.prefs_to_names[cpn],
                                    parent.console_config[pn],-1,100)

class OtherPane(BasePane):
    def __init__(self, offset, parent, width):
        BasePane.__init__(self,offset,parent,width)
        self.add_header("System Information")
        self.add_info_field(" Help us improve Deluge by sending us your","","")
        self.add_info_field(" Python version, PyGTK version, OS and processor","","")
        self.add_info_field(" types.  Absolutely no other information is sent.","","")
        self.add_checked_input("send_info","Yes, please send anonymous statistics.",parent.core_config["send_info"])
        self.add_header("GeoIP Database",True)
        self.add_text_input("geoip_db_location","Location:",parent.core_config["geoip_db_location"])

class DaemonPane(BasePane):
    def __init__(self, offset, parent, width):
        BasePane.__init__(self,offset,parent,width)
        self.add_header("Port")
        self.add_int_spin_input("daemon_port","Daemon Port:",parent.core_config["daemon_port"],0,65535)
        self.add_header("Connections",True)
        self.add_checked_input("allow_remote","Allow remote connections",parent.core_config["allow_remote"])
        self.add_header("Other",True)
        self.add_checked_input("new_release_check","Periodically check the website for new releases",parent.core_config["new_release_check"])

class QueuePane(BasePane):
    def __init__(self, offset, parent, width):
        BasePane.__init__(self,offset,parent,width)
        self.add_header("General")
        self.add_checked_input("queue_new_to_top","Queue new torrents to top",parent.core_config["queue_new_to_top"])
        self.add_header("Active Torrents",True)
        self.add_int_spin_input("max_active_limit","Total active:",parent.core_config["max_active_limit"],-1,9999)
        self.add_int_spin_input("max_active_downloading","Total active downloading:",parent.core_config["max_active_downloading"],-1,9999)
        self.add_int_spin_input("max_active_seeding","Total active seeding:",parent.core_config["max_active_seeding"],-1,9999)
        self.add_checked_input("dont_count_slow_torrents","Do not count slow torrents",parent.core_config["dont_count_slow_torrents"])
        self.add_checked_input("auto_manage_prefer_seeds","Prefer Seeding over Downloading",parent.core_config["auto_manage_prefer_seeds"])
        self.add_header("Seeding",True)
        self.add_float_spin_input("share_ratio_limit","Share Ratio Limit:",parent.core_config["share_ratio_limit"],1.0,2,-1.0,100.0)
        self.add_float_spin_input("seed_time_ratio_limit","Share Time Ratio:",parent.core_config["seed_time_ratio_limit"],1.0,2,-1.0,100.0)
        self.add_int_spin_input("seed_time_limit","Seed time (m):",parent.core_config["seed_time_limit"],-1,10000)
        seedratio = FloatSpinInput(self.parent,"","stop_seed_ratio",self.move,parent.core_config["stop_seed_ratio"],0.1,2,0.5,100.0)
        self.add_checkedplus_input("stop_seed_at_ratio","Stop seeding when share ratio reaches:",seedratio,parent.core_config["stop_seed_at_ratio"])
        self.add_checked_input("remove_seed_at_ratio","Remove torrent when share ratio reached",parent.core_config["remove_seed_at_ratio"])

class ProxyPane(BasePane):
    def __init__(self, offset, parent, width):
        BasePane.__init__(self,offset,parent,width)
        self.add_header("Proxy Settings Comming Soon")

class CachePane(BasePane):
    def __init__(self, offset, parent, width):
        BasePane.__init__(self,offset,parent,width)
        self.add_header("Settings")
        self.add_int_spin_input("cache_size","Cache Size (16 KiB blocks):",parent.core_config["cache_size"],0,99999)
        self.add_int_spin_input("cache_expiry","Cache Expiry (seconds):",parent.core_config["cache_expiry"],1,32000)
        self.add_header("Status (press 'r' to refresh status)",True)
        self.add_header(" Write")
        self.add_info_field("  Blocks Written:",self.parent.status["blocks_written"],"blocks_written")
        self.add_info_field("  Writes:",self.parent.status["writes"],"writes")
        self.add_info_field("  Write Cache Hit Ratio:","%.2f"%self.parent.status["write_hit_ratio"],"write_hit_ratio")
        self.add_header(" Read")
        self.add_info_field("  Blocks Read:",self.parent.status["blocks_read"],"blocks_read")
        self.add_info_field("  Blocks Read hit:",self.parent.status["blocks_read_hit"],"blocks_read_hit")
        self.add_info_field("  Reads:",self.parent.status["reads"],"reads")
        self.add_info_field("  Read Cache Hit Ratio:","%.2f"%self.parent.status["read_hit_ratio"],"read_hit_ratio")
        self.add_header(" Size")
        self.add_info_field("  Cache Size:",self.parent.status["cache_size"],"cache_size")
        self.add_info_field("  Read Cache Size:",self.parent.status["read_cache_size"],"read_cache_size")

    def update_cache_status(self, status):
        for ipt in self.inputs:
            if isinstance(ipt,InfoField):
                try:
                    ipt.set_value(status[ipt.name])
                except KeyError:
                    pass
