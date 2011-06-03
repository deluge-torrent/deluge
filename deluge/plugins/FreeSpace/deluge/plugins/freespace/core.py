#
# core.py
#
# Copyright (C) 2009-2010 Pedro Algarvio <pedro@algarvio.me>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
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
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
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


import os, statvfs
from datetime import datetime, timedelta
from twisted.internet import task
from deluge.log import getPluginLogger
from deluge.plugins.pluginbase import CorePluginBase
from deluge.event import DelugeEvent
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export

log = getPluginLogger(__name__)


class LowDiskSpaceEvent(DelugeEvent):
    """Triggered when the available space for a specific path is getting
    too low.
    """
    def __init__(self, percents_dict):
        """
        :param percents: dictionary of path keys with their respecive
                         occupation percentages.
        """
        self._args = [percents_dict]

DEFAULT_PREFS = {
    "enabled": False,
    "percent": 90
}

class Core(CorePluginBase):
    CLEANUP_TIMEOUT_SECS = 3600 # One hour

    def enable(self):
        self.config = deluge.configmanager.ConfigManager("freespace.conf",
                                                         DEFAULT_PREFS)
        self.notifications_sent = {}

        self._timer = task.LoopingCall(self.update)
        self._interval = 60 * 5 # every 5 minutes
        if self.config['enabled']:
            self._timer.start(self._interval, False)

        self._cleanup = task.LoopingCall(self.__cleanup_notifications)
        self._cleanup.start(self._interval, False)

        try:
            component.get("CorePlugin.Notifications"). \
                register_custom_email_notification(
                    "LowDiskSpaceEvent", self.__custom_email_notification
            )
        except KeyError:
            pass
        component.get("EventManager").register_event_handler(
            "PluginEnabledEvent", self.__on_plugin_enabled
        )
        component.get("EventManager").register_event_handler(
            "PluginDisabledEvent", self.__on_plugin_disabled
        )

    def disable(self):
        try:
            component.get("CorePlugin.Notifications"). \
                deregister_custom_email_notification("LowDiskSpaceEvent")
        except KeyError:
            pass
        component.get("EventManager").deregister_event_handler(
            "PluginEnabledEvent", self.__on_plugin_enabled
        )
        component.get("EventManager").deregister_event_handler(
            "PluginDisabledEvent", self.__on_plugin_disabled
        )
        self._cleanup.stop()
        if self._timer.running:
            self._timer.stop()

    def update(self):
        log.debug('Updating %s FreeSpace', self.__class__.__name__)
        nots = {}
        for path in self.__gather_paths_to_check():
            log.debug("Checking path %s", path)
            if os.path.exists(path):
                free_percent = self.__get_free_space(path)
                if (100 - free_percent) > self.config['percent']:
                    if path not in self.notifications_sent:
                        self.notifications_sent[path] = datetime.utcnow()
                        nots[path] = (100 - free_percent)
                    else:
                        log.warning("Running low on disk space on %s but "
                                    "notifications were already triggered.",
                                    path)
        if nots:
            component.get("EventManager").emit(LowDiskSpaceEvent(nots))


    @export
    def set_config(self, config):
        "sets the config dictionary"
        if not self.config['enabled'] and config['enabled']:
            self._timer.start(self._interval, False)
        elif self.config['enabled'] and not config['enabled']:
            self._timer.stop()

        for key in config.keys():
            self.config[key] = config[key]
        self.config.save()

    @export
    def get_config(self):
        "returns the config dictionary"
        return self.config.config

    def __gather_paths_to_check(self):
        self.over_percentage = {}
        torrent_manager = component.get('TorrentManager')
        paths = set()
        for torrent_id in torrent_manager.get_torrent_list():
            status = torrent_manager[torrent_id].get_status([
                'is_finished',
                'move_on_completed_path',
                'save_path'
            ])
            if not status['is_finished']:
                paths.add(status['move_on_completed_path'])
                paths.add(status['save_path'])
        return paths

    def __get_free_space(self, path):
        log.debug("Calculating free space on %s", path)
        stat = os.statvfs(path)
        free_blocks = stat[statvfs.F_BAVAIL]
        total_blocks = stat[statvfs.F_BLOCKS]
        free_percent = free_blocks * 100 / total_blocks
        return free_percent

    def __custom_email_notification(self, ocupied_percents):

        subject = _("Low Disk Space Warning")
        message = _("You're running low on disk space:\n")

        for path, ocupied_percent in ocupied_percents.iteritems():
            message += _('  %s%% ocupation in %s\n') % (ocupied_percent, path)
#                    "\"%s\"%% space occupation on %s") % (ocupied_percent, path)
        return subject, message

    def __on_plugin_enabled(self, plugin_name):
        if plugin_name == 'Notifications':
            component.get("CorePlugin.Notifications"). \
                register_custom_email_notification(
                    "LowDiskSpaceEvent", self.__custom_email_notification
            )

    def __on_plugin_disabled(self, plugin_name):
        if plugin_name == 'Notifications':
            component.get("CorePlugin.Notifications"). \
                deregister_custom_email_notification("LowDiskSpaceEvent")

    def __cleanup_notifications(self):
        now = datetime.now()
        for path, when in self.notifications_sent.copy().iteritems():
            if when <= (now -timedelta(seconds=self.CLEANUP_TIMEOUT_SECS)):
                log.debug("Removing old(%s) path from notified paths: %s",
                          when, path)
                self.notifications_sent.pop(path)
