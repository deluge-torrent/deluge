#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
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


"""
torrent-label core plugin.
adds a status field for tracker.
"""

from deluge.log import LOG as log
from deluge.plugins.pluginbase import CorePluginBase
from deluge.core.rpcserver import export
from deluge.configmanager import ConfigManager
import deluge.component as component
from urlparse import urlparse

import traceback
import re

RE_VALID = re.compile("[a-z0-9_\-\.]*\Z")

KNOWN_STATES = ['Downloading','Seeding','Paused','Checking','Queued','Error']
STATE = "state"
TRACKER = "tracker"
KEYWORD = "keyword"
LABEL = "label"
CONFIG_DEFAULTS = {
    "torrent_labels":{}, #torrent_id:label_id
    "labels":{}, #label_id:{name:value}
}

CORE_OPTIONS = ["auto_add_trackers"]

OPTIONS_DEFAULTS = {
    "apply_max":False,
    "max_download_speed":-1,
    "max_upload_speed":-1,
    "max_connections":-1,
    "max_upload_slots":-1,
    "prioritize_first_last":False,
    "apply_queue":False,
    "is_auto_managed":False,
    "stop_at_ratio":False,
    "stop_ratio":2.0,
    "remove_at_ratio":False,
    "apply_move_completed":False,
    "move_completed":False,
    "move_completed_path":"",
    "auto_add":False,
    "auto_add_trackers":[]
}

NO_LABEL = "No Label"


def CheckInput(cond, message):
    if not cond:
        raise Exception(message)


class Core(CorePluginBase):
    """
    self.labels = {label_id:label_options_dict}
    self.torrent_labels = {torrent_id:label_id}
    """
    def enable(self):
        log.info("*** Start Label plugin ***")
        self.plugin = component.get("CorePluginManager")
        self.plugin.register_status_field("label", self._status_get_label)
        self.torrent_manager = component.get("TorrentManager")

        #__init__
        core = component.get("Core")
        self.config = ConfigManager("label.conf", defaults=CONFIG_DEFAULTS)
        self.core_cfg = ConfigManager("core.conf")

        #reduce typing, assigning some values to self...
        self.torrents = core.torrentmanager.torrents
        self.labels = self.config["labels"]
        self.torrent_labels = self.config["torrent_labels"]

        self.clean_initial_config()

        component.get("EventManager").register_event_handler("TorrentAddedEvent", self.post_torrent_add)
        component.get("EventManager").register_event_handler("TorrentRemovedEvent", self.post_torrent_remove)

        #register tree:
        component.get("FilterManager").register_tree_field("label", self.init_filter_dict)

        log.debug("Label plugin enabled..")

    def disable(self):
        self.plugin.deregister_status_field("label")
        component.get("FilterManager").deregister_tree_field("label")

    def update(self):
        pass

    def init_filter_dict(self):
        filter_dict = dict([(label, 0) for label in self.labels.keys()])
        filter_dict['All'] = len(self.torrents.keys())
        return filter_dict

    ## Plugin hooks ##
    def post_torrent_add(self, torrent_id):
        if not self.torrent_manager.session_started:
            return
        log.debug("post_torrent_add")
        torrent = self.torrents[torrent_id]

        for label_id, options in self.labels.iteritems():
            if options["auto_add"]:
                if self._has_auto_match(torrent, options):
                    self.set_torrent(torrent_id, label_id)
                    return

    def post_torrent_remove(self, torrent_id):
        log.debug("post_torrent_remove")
        if torrent_id in self.torrent_labels:
            del self.torrent_labels[torrent_id]

    ## Utils ##
    def clean_config(self):
        """remove invalid data from config-file"""
        for torrent_id, label_id in list(self.torrent_labels.iteritems()):
            if (not label_id in self.labels) or (not torrent_id in self.torrents):
                log.debug("label: rm %s:%s" % (torrent_id,label_id))
                del self.torrent_labels[torrent_id]

    def clean_initial_config(self):
        """
        *add any new keys in OPTIONS_DEFAULTS
        *set all None values to default <-fix development config
        """
        log.debug(self.labels.keys())
        for key in self.labels.keys():
            options = dict(OPTIONS_DEFAULTS)
            options.update(self.labels[key])
            self.labels[key] = options

        for label, options in self.labels.items():
            for key, value in options.items():
                if value == None:
                    self.labels[label][key] = OPTIONS_DEFAULTS[key]

    def save_config(self):
        self.clean_config()
        self.config.save()

    @export
    def get_labels(self):
        return sorted(self.labels.keys())

    #Labels:
    @export
    def add(self, label_id):
        """add a label
        see label_set_options for more options.
        """
        label_id = label_id.lower()
        CheckInput(RE_VALID.match(label_id) , _("Invalid label, valid characters:[a-z0-9_-]"))
        CheckInput(label_id, _("Empty Label"))
        CheckInput(not (label_id in self.labels) , _("Label already exists"))

        self.labels[label_id] = dict(OPTIONS_DEFAULTS)
        self.config.save()

    @export
    def remove(self, label_id):
        """remove a label"""
        CheckInput(label_id in self.labels, _("Unknown Label"))
        del self.labels[label_id]
        self.clean_config()
        self.config.save()

    def _set_torrent_options(self, torrent_id, label_id):
        options = self.labels[label_id]
        torrent = self.torrents[torrent_id]

        if not options["move_completed_path"]:
            options["move_completed_path"] = "" #no None.

        if options["apply_max"]:
            torrent.set_max_download_speed(options["max_download_speed"])
            torrent.set_max_upload_speed(options["max_upload_speed"])
            torrent.set_max_connections(options["max_connections"])
            torrent.set_max_upload_slots(options["max_upload_slots"])
            torrent.set_prioritize_first_last(options["prioritize_first_last"])

        if options["apply_queue"]:
            torrent.set_auto_managed(options['is_auto_managed'])
            torrent.set_stop_at_ratio(options['stop_at_ratio'])
            torrent.set_stop_ratio(options['stop_ratio'])
            torrent.set_remove_at_ratio(options['remove_at_ratio'])

        if options["apply_move_completed"]:
            torrent.set_options(
                {
                    "move_completed": options["move_completed"],
                    "move_completed_path": options["move_completed_path"]
                }
            )

    def _unset_torrent_options(self, torrent_id, label_id):
        options = self.labels[label_id]
        torrent = self.torrents[torrent_id]

        if options["apply_max"]:
            torrent.set_max_download_speed(self.core_cfg.config["max_download_speed_per_torrent"])
            torrent.set_max_upload_speed(self.core_cfg.config["max_upload_speed_per_torrent"])
            torrent.set_max_connections(self.core_cfg.config["max_connections_per_torrent"])
            torrent.set_max_upload_slots(self.core_cfg.config["max_upload_slots_per_torrent"])
            torrent.set_prioritize_first_last(self.core_cfg.config["prioritize_first_last_pieces"])

        if options["apply_queue"]:
            torrent.set_auto_managed(self.core_cfg.config['auto_managed'])
            torrent.set_stop_at_ratio(self.core_cfg.config['stop_seed_at_ratio'])
            torrent.set_stop_ratio(self.core_cfg.config['stop_seed_ratio'])
            torrent.set_remove_at_ratio(self.core_cfg.config['remove_seed_at_ratio'])

        if options["apply_move_completed"]:
            torrent.set_options(
                {
                    "move_completed": self.core_cfg.config["move_completed"],
                    "move_completed_path": self.core_cfg.config["move_completed_path"]
                }
            )

    def _has_auto_match(self, torrent ,label_options):
        """match for auto_add fields"""
        for tracker_match in label_options["auto_add_trackers"]:
            for tracker in torrent.trackers:
                if tracker_match in tracker["url"]:
                    return True
        return False

    @export
    def set_options(self, label_id, options_dict):
        """update the label options

        options_dict :
        {"max_download_speed":float(),
            "max_upload_speed":float(),
            "max_connections":int(),
            "max_upload_slots":int(),
            #"prioritize_first_last":bool(),
            "apply_max":bool(),
            "move_completed_to":string() or None
        }
        """
        CheckInput(label_id in self.labels , _("Unknown Label"))
        for key in options_dict.keys():
            if not key in OPTIONS_DEFAULTS:
                raise Exception("label: Invalid options_dict key:%s" % key)

        self.labels[label_id].update(options_dict)

        #apply
        for torrent_id,label in self.torrent_labels.iteritems():
            if label_id == label and torrent_id in self.torrents:
                self._set_torrent_options(torrent_id , label_id)

        #auto add
        options = self.labels[label_id]
        if options["auto_add"]:
            for torrent_id, torrent in self.torrents.iteritems():
                if self._has_auto_match(torrent, options):
                    self.set_torrent(torrent_id , label_id)

        self.config.save()

    @export
    def get_options(self, label_id):
        """returns the label options"""
        return self.labels[label_id]

    @export
    def set_torrent(self, torrent_id , label_id):
        """
        assign a label to a torrent
        removes a label if the label_id parameter is empty.
        """
        if label_id == NO_LABEL:
            label_id = None

        CheckInput((not label_id) or (label_id in self.labels)  , _("Unknown Label"))
        CheckInput(torrent_id in self.torrents  , _("Unknown Torrent"))

        if torrent_id in self.torrent_labels:
            self._unset_torrent_options(torrent_id, self.torrent_labels[torrent_id])
            del self.torrent_labels[torrent_id]
            self.clean_config()
        if label_id:
            self.torrent_labels[torrent_id] = label_id
            self._set_torrent_options(torrent_id, label_id)

        self.config.save()

    @export
    def get_config(self):
        """see : label_set_config"""
        return dict((key, self.config[key]) for key in CORE_OPTIONS if key in self.config.config)

    @export
    def set_config(self, options):
        """global_options:"""
        if options:
            for key, value in options.items:
                if key in CORE_OPTIONS:
                    self.config[key] = value

            self.config.save()

    def _status_get_label(self, torrent_id):
        return self.torrent_labels.get(torrent_id) or ""

if __name__ == "__main__":
    import test
