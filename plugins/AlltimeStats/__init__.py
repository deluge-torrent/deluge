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

plugin_name = _("Alltime Stats")
plugin_author = "Micah Bucy"
plugin_version = "0.1"
plugin_description = _("""
Shows alltime stats in the tray tooltip.
Tracks transfer amounts, ratio, number of torrents finished, and uptime.
Also show session uptime
""")

def deluge_init(deluge_path):
    global path
    path = deluge_path

def enable(core, interface):
    global path
    return AlltimeStats(path, core, interface)

### The Plugin ###
import gtk
import os
import time

import deluge
from deluge import common

class AlltimeStats:

    def __init__(self, path, core, interface):
        print "Loading AlltimeStats plugin..."
        self.manager = core
        self.statsdir = os.path.join(common.CONFIG_DIR, 'alltime_stats')
        self.tray_message = ""
        self.downloaded = None
        self.uploaded = None
        self.ratio = None
        self.finished = None
        self.uptime = None
        self.start_time = long(time.time())
        self.prepare_stats()
        self.manager.connect_event(self.manager.constants['EVENT_FINISHED'], self.handle_event)

    def stats_clicked(self, src):
        self.window.show_all()

    def close(self, widget, event):
        self.window.hide()

    def prepare_stats(self):
        if not os.path.isdir(self.statsdir):
            os.mkdir(self.statsdir)
        if not os.path.isdir(self.statsdir):
            os.mkdir(self.statsdir)
        stats_state = os.path.join(self.statsdir, "stats.state")
        try:
            stats_file = open(stats_state, "r")
        except:
            self.downloaded = 0
            self.uploaded = 0
            self.finished = 0
            for unique_id in self.manager.unique_IDs.keys():
                self.uploaded += long(self.manager.unique_IDs[unique_id].uploaded_memory)
                state = self.manager.get_torrent_state(unique_id)
                self.downloaded += long(state["total_done"])
                if state['is_seed']:
                    self.finished += 1
            self.uptime = 0
        else:
            readlines = stats_file.readlines() 
            self.downloaded = long(readlines[0])
            self.uploaded = long(readlines[1])
            self.finished = int(readlines[2])
            self.uptime = long(readlines[3])
            stats_file.close()
        if self.downloaded == 0:
            ratio = _("Undefined")
        else:
            ratio = "%.3f" % float(float(self.uploaded)/float(self.downloaded))
        self.tray_message = '%s: %s\n%s: %s\n%s: %s\n%s: %s\n%s: %s\n%s: %s' % (
            _("Uptime"), common.ftime(0),
            _("All-time Downloaded"), common.fsize(self.downloaded),
            _("All-time Uploaded"), common.fsize(self.uploaded),
            _("All-time Ratio"), ratio,
            _("Torrents completed"), str(self.finished),
            _("All-time Uptime"), common.ftime(self.uptime))

    def get_tray_message(self):
        return self.tray_message

    def unload(self):
        state = self.manager.get_state()
        downloaded = long(state['total_downloaded']) + self.downloaded
        uploaded = long(state['total_uploaded']) + self.uploaded
        uptime = long(time.time()) - self.start_time + self.uptime
        stats_state = os.path.join(self.statsdir, "stats.state")
        stats_file = open(stats_state, "w")
        stats_file.writelines([str(downloaded)+'\n',\
            str(uploaded)+'\n', str(self.finished)+'\n', str(uptime)+'\n'])
        stats_file.close()
        self.manager.disconnect_event(self.manager.constants['EVENT_FINISHED'], self.handle_event)

    def handle_event(self, event):
        if event['message'] == "torrent has finished downloading":
            self.finished += 1
            self.update()

    def update(self):
        state = self.manager.get_state()
        downloaded = long(state['total_downloaded']) + self.downloaded
        uploaded = long(state['total_uploaded']) + self.uploaded
        ses_uptime = long(time.time()) - self.start_time
        uptime =  ses_uptime + self.uptime
        if downloaded == 0:
            ratio = _("Undefined")
        else:
            ratio = "%.3f" % float(float(uploaded)/float(downloaded))
        self.tray_message = '%s: %s\n\n%s: %s\n%s: %s\n%s: %s\n%s: %s\n%s: %s' % (
            _("Uptime"), common.ftime(ses_uptime),
            _("All-time Downloaded"), common.fsize(downloaded),
            _("All-time Uploaded"), common.fsize(uploaded),
            _("All-time Ratio"), ratio,
            _("Torrents completed"), str(self.finished),
            _("All-time Uptime"), common.ftime(uptime))
