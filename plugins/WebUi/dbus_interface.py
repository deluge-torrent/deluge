# -*- coding: utf-8 -*-
# Dbus Ipc for experimental web interface
#
# dbus_interface.py
#
# Copyright (C) Martijn Voncken 2007 <mvoncken@gmail.com>
# Contains copy and pasted code from other parts of deluge,see deluge AUTHORS
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, write to:
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
#
#  In addition, as a special exception, the copyright holders give
#  permission to link the code of portions of this program with the OpenSSL
#  library.
#  You must obey the GNU General Public License in all respects for all of
#  the code used other than OpenSSL. If you modify file(s) with this
#  exception, you may extend this exception to your version of the file(s),
#  but you are not obligated to do so. If you do not wish to do so, delete
#  this exception statement from your version. If you delete this exception
#  statement from all source files in the program, then also delete it here.


import os
import gtk
import dbus
import deluge.common as common
from dbus_pythonize import pythonize
import base64
from md5 import md5
import random
random.seed()

dbus_interface="org.deluge_torrent.dbusplugin"
dbus_service="/org/deluge_torrent/DelugeDbusPlugin"


class DbusManager(dbus.service.Object):
    def __init__(self, core, interface,config,config_file):
        self.core = core
        self.interface = interface
        self.config = config
        self.config_file = config_file
        self.bus = dbus.SessionBus()
        bus_name = dbus.service.BusName(dbus_interface,bus=self.bus)
        dbus.service.Object.__init__(self, bus_name,dbus_service)

    #
    #todo : add:  get_interface_version in=i,get_config_value in=s out=s
    #

    @dbus.service.method(dbus_interface=dbus_interface,
        in_signature="",out_signature="as")
    def get_torrent_state(self):
        """Returns a list of torrent_ids in the session.
        same as 0.6, but returns type "as" instead of a pickle
        """
        torrent_list =  [str(key) for key in self.core.unique_IDs]
        return torrent_list

    @dbus.service.method(dbus_interface=dbus_interface,
        in_signature="sas",out_signature="a{sv}")
    def get_torrent_status(self, torrent_id, keys):
        """return torrent metadata of a single torrent as a dict
        0.6  returns a pickle, this returns a dbus-type.
        +added some more values to the dict
        """

        torrent_id = int(torrent_id)
        # Convert the array of strings to a python list of strings
        nkeys = [str(key) for key in keys]

        state = self.core.get_torrent_state(torrent_id)
        torrent = self.core.unique_IDs[torrent_id]

        status = {
            "name": state["name"],
            "total_size": state["total_size"],
            "num_pieces": state["num_pieces"],
            "state": state['state'],
            "paused": self.core.is_user_paused(torrent_id),
            "progress": int(state["progress"] * 100),
            "next_announce": state["next_announce"],
            "total_payload_download":state["total_payload_download"],
            "total_payload_upload": state["total_payload_upload"],
            "download_payload_rate": state["download_rate"],
            "upload_payload_rate": state["upload_rate"],
            "num_peers": state["num_peers"],
            "num_seeds": state["num_seeds"],
            "total_wanted": state["total_wanted"],
            "eta": common.estimate_eta(state),
            "ratio": self.interface.manager.calc_ratio(torrent_id,state),
            #non 0.6 values follow here:
            "message":  self.interface.get_message_from_state(state),
            "tracker_status": state.get("tracker_status","?"),
            "uploaded_memory": torrent.uploaded_memory,
        }
        #more non 0.6 values
        for key in ["total_seeds", "total_peers","is_seed", "total_done",
                "total_download", "total_upload", "download_rate",
                "upload_rate", "num_files", "piece_length", "distributed_copies"
                ,"next_announce","tracker"]:
            status[key] = state[key]

        #print 'all_keys:',sorted(status.keys())

        status_subset = {}
        for key in keys:
            if key in status:
                status_subset[key] = status[key]
            else:
                print 'mbus error,no key named:', key
        return status_subset

    @dbus.service.method(dbus_interface=dbus_interface,
        in_signature="s",out_signature="")
    def pause_torrent(self, torrent_id):
        """same as 0.6 interface"""
        torrent_id = int(torrent_id)
        self.core.set_user_pause(torrent_id,True)

    @dbus.service.method(dbus_interface=dbus_interface,
        in_signature="s", out_signature="")
    def resume_torrent(self, torrent_id):
        """same as 0.6 interface"""
        torrent_id = int(torrent_id)
        self.core.set_user_pause(torrent_id,False)

    @dbus.service.method(dbus_interface=dbus_interface,
        in_signature="sbb", out_signature="")
    def remove_torrent(self, torrent_id, data_also, torrent_also):
        """remove a torrent,and optionally data and torrent
        additions compared to 0.6 interface: (data_also, torrent_also)
        """
        torrent_id = int(torrent_id)
        self.core.remove_torrent(torrent_id, bool(data_also)
            ,bool( torrent_also))
        #this should not be needed:
        self.interface.torrent_model_remove(torrent_id)

    @dbus.service.method(dbus_interface=dbus_interface,
        in_signature="s", out_signature="b")
    def add_torrent_url(self, url):
        """not available in deluge 0.6 interface"""
        filename = fetch_url(url)
        self._add_torrent(filename)
        return True

    @dbus.service.method(dbus_interface=dbus_interface,
        in_signature="ss", out_signature="b")
    def add_torrent_filecontent(self, name, filecontent_b64):
        """not available in deluge 0.6 interface"""
        #name = fillename without directory
        name =  name.replace('\\','/')
        name = 'deluge_' + str(random.random()) + '_'  + name.split('/')[-1]

        filename = os.path.join(self.config.get("torrent_dir"),name)
        filecontent = base64.b64decode(filecontent_b64)
        f = open(filename,"wb") #no with statement, that's py 2.5+
        f.write(filecontent)
        f.close()
        print 'write:',filename
        self._add_torrent(filename)
        return True

    @dbus.service.method(dbus_interface=dbus_interface,
        in_signature="s",out_signature="v")
    def get_webui_config(self,key):
        """
        return data from wevbui config.
        not in 0.6
        """
        retval = self.config.get(str(key))
        #print 'get webui config:', str(key), retval
        if retval == None:
            retval = False #dbus does not accept None  :(

        return retval

    @dbus.service.method(dbus_interface=dbus_interface,
        in_signature="sv",out_signature="")
    def set_webui_config(self, key, value):
        """
        return data from wevbui config.
        not in 0.6
        """
        #print 'set webui config:', str(key), pythonize(value)
        self.config.set(str(key), pythonize(value))
        self.config.save(self.config_file)

    @dbus.service.method(dbus_interface=dbus_interface,
        in_signature="s",out_signature="b")
    def check_pwd(self, pwd):
        m = md5()
        m.update(self.config.get('pwd_salt'))
        m.update(pwd)
        return (m.digest() == self.config.get('pwd_md5'))

    #internal
    def _add_torrent(self, filename):
        #dbus types break pickle, again.....
        filename = unicode(filename)
        target = self.config.get("download_dir")

        torrent_id = self.core.add_torrent(filename, target,
            self.interface.config.get("use_compact_storage"))

        #update gtk-ui This should not be needed!!
        gtk.gdk.threads_enter()
        try:
            self.interface.torrent_model_append(torrent_id)
        except:
            pass
        #finally is 2.5 only!
        gtk.gdk.threads_leave()

        return True

def fetch_url(url):
    import urllib

    try:
        filename, headers = urllib.urlretrieve(url)
    except IOError:
        raise Exception( "Network error while trying to fetch torrent from %s"
            % url)
    else:
        if (filename.endswith(".torrent") or
           headers["content-type"]=="application/x-bittorrent"):
            return filename
        else:
            raise Exception("URL doesn't appear to be a valid torrent file:%s"
                %  url)

    return None
