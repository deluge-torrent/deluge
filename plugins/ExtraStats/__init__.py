# Copyright (C) 2007 - Micah Bucy <eternalsword@gmail.com>
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.

### Initialization ###

plugin_name = "Extra Stats"
plugin_author = "Micah Bucy"
plugin_version = "0.1"
plugin_description = _("""
Adds info to tray tooltip.
Adds these stats.
total bytes downloaded
total bytes uploaded
overall ratio
torrents completed

All of these stats come in pairs:
across sessions stat and within session stat.
By default, all pairs enabled, but can be disabled in plugin preferences.

session data always shows up within parenthesis
eg.  Total Downloaded: 5 GiB (4 MiB)
would be 5 GiB across sessions and 4 MiB within session
""")

def deluge_init(deluge_path):
    global path
    path = deluge_path

def enable(core, interface):
    global path
    return ExtraStats(path, core, interface)

### The Plugin ###
import gtk
import os
import time

import deluge
from deluge import common

class ExtraStats:
    def __init__(self, path, core, interface):
        print "Found ExtraStats plugin..."
        self.manager = core
        # Create an options file and try to load existing Values
        self.config_file = os.path.join(deluge.common.CONFIG_DIR, "extra_stats.conf")
        self.config = deluge.pref.Preferences(self.config_file, False,
                          {'enable_downloaded': True,
                           'enable_uploaded': True,
                           'enable_ratio': True,
                           'enable_finished': True,
                           'enable_running_time': True,
                           })
        try:
            self.config.load()
        except IOError:
            # File does not exist
            pass
        self.glade = gtk.glade.XML(os.path.join(path, "stats_preferences.glade"))
        self.dialog = self.glade.get_widget("dialog")
        self.dialog.set_position(gtk.WIN_POS_CENTER)
        self.glade.signal_autoconnect({
                                        'on_button_cancel_clicked': self.cancel_clicked,
                                        'on_button_ok_clicked': self.ok_clicked
                                      })
        self.statsdir = os.path.join(common.CONFIG_DIR, 'extra_stats')
        self.tray_message = ""
        self.all_downloaded = None
        self.all_uploaded = None
        self.all_finished = None
        self.all_running_time = None
        self.finished = 0
        self.start_time = long(time.time())
        self.prepare_stats()
        self.manager.connect_event(self.manager.constants['EVENT_FINISHED'], self.handle_event)

    def prepare_stats(self):
        if not os.path.isdir(self.statsdir):
            os.mkdir(self.statsdir)
        if not os.path.isdir(self.statsdir):
            os.mkdir(self.statsdir)
        stats_state = os.path.join(self.statsdir, "stats.state")
        try:
            stats_file = open(stats_state, "r")
        except:
            self.all_downloaded = 0
            self.all_uploaded = 0
            self.all_finished = 0
            for unique_id in self.manager.unique_IDs.keys():
                self.all_uploaded += long(self.manager.unique_IDs[unique_id].uploaded_memory)
                state = self.manager.get_torrent_state(unique_id)
                self.all_downloaded += long(state["total_done"])
                if state['is_seed']:
                    self.all_finished += 1
            self.all_running_time = 0
        else:
            readlines = stats_file.readlines() 
            self.all_downloaded = long(readlines[0])
            self.all_uploaded = long(readlines[1])
            self.all_finished = int(readlines[2])
            self.all_running_time = long(readlines[3])
            stats_file.close()

    def configure(self, window):
        self.glade.get_widget("chk_downloaded").set_active(self.config.get("enable_downloaded"))
        self.glade.get_widget("chk_uploaded").set_active(self.config.get("enable_uploaded"))
        self.glade.get_widget("chk_ratio").set_active(self.config.get("enable_ratio"))
        self.glade.get_widget("chk_finished").set_active(self.config.get("enable_finished"))
        self.glade.get_widget("chk_running_time").set_active(self.config.get("enable_running_time"))
        self.dialog.set_transient_for(window)
        self.dialog.show()

    def get_tray_message(self):
        return self.tray_message

    def unload(self):
        self.save_stats_state(self.get_stats())
        self.manager.disconnect_event(self.manager.constants['EVENT_FINISHED'], self.handle_event)
        self.config.save(self.config_file)

    def handle_event(self, event):
        if event['message'] == "torrent has finished downloading":
            self.finished += 1
            self.all_finished += 1
            self.update()

    def get_stats(self):
        state = self.manager.get_state()
        ses_downloaded = long(state['total_downloaded'])
        ses_uploaded = long(state['total_uploaded'])
        ses_running_time = long(time.time()) - self.start_time
        all_downloaded = ses_downloaded + self.all_downloaded
        all_uploaded = ses_uploaded + self.all_uploaded
        all_running_time =  ses_running_time + self.all_running_time
        
        return (ses_downloaded, ses_uploaded, ses_running_time, 
                all_downloaded, all_uploaded, all_running_time)

    def save_stats_state(self, stats_array):
        all_downloaded, all_uploaded, all_running_time = stats_array[3:] 
        
        stats_state = os.path.join(self.statsdir, "stats.state")
        stats_file = open(stats_state, "w")
        stats_file.writelines([str(all_downloaded)+'\n',
            str(all_uploaded)+'\n', str(self.all_finished)+'\n', 
            str(all_running_time)+'\n'])
        stats_file.close()

    def update(self):
        stats_array = self.get_stats()
        ses_downloaded, ses_uploaded, ses_running_time, \
        all_downloaded, all_uploaded, all_running_time = stats_array 

        if ses_running_time%100 == 0:
            # Store state approximately every 100 updates.
            self.save_stats_state(stats_array)

        downloaded = ""
        if self.config.get("enable_downloaded"):
            downloaded = "%s: %s (%s)\n" % (
                _("Total Downloaded"), common.fsize(all_downloaded),
                common.fsize(ses_downloaded))

        uploaded = ""
        if self.config.get("enable_uploaded"):
            uploaded = "%s: %s (%s)\n" % (
                _("Total Uploaded"), common.fsize(all_uploaded),
                common.fsize(ses_uploaded))

        overall_ratio = ""
        if self.config.get("enable_ratio"):
            if ses_downloaded == 0:
                ses_ratio = _("Undefined")
            else:
                ses_ratio = "%.3f" % (float(ses_uploaded)/float(ses_downloaded))
            if all_downloaded == 0:
                all_ratio = _("Undefined")
            else:
                all_ratio = "%.3f" % (float(all_uploaded)/float(all_downloaded))
            overall_ratio = "%s: %s (%s)\n" % (
                _("Overall Ratio"), all_ratio, ses_ratio)

        finished = ""
        if self.config.get("enable_finished"):
            finished = "%s: %s (%s)\n" % (
                _("Torrents Completed"), str(self.all_finished),
                str(self.finished))

        running_time = ""
        if self.config.get("enable_running_time"):
            running_time = "%s: %s (%s)\n" % (
                _("Running Time"), common.ftime(all_running_time),
                common.ftime(ses_running_time))

        # Copy to self.tray_message without last new line char
        self.tray_message = (downloaded + uploaded + overall_ratio + \
                             finished + running_time)[:-1]

    def ok_clicked(self, src):
        self.dialog.hide()
        self.config.set("enable_downloaded", self.glade.get_widget("chk_downloaded").get_active())
        self.config.set("enable_uploaded", self.glade.get_widget("chk_uploaded").get_active())
        self.config.set("enable_ratio", self.glade.get_widget("chk_ratio").get_active())
        self.config.set("enable_finished", self.glade.get_widget("chk_finished").get_active())
        self.config.set("enable_running_time", self.glade.get_widget("chk_running_time").get_active())

    def cancel_clicked(self, src):
        self.dialog.hide()
