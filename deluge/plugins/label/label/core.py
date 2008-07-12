#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 2 of the License, or (at your option)
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
# 	Boston, MA    02110-1301, USA.
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

"""
torrent-label core plugin.
adds a status field for tracker.
"""

from deluge.log import LOG as log
from deluge.plugins.corepluginbase import CorePluginBase
from deluge.configmanager import ConfigManager

from urlparse import urlparse

import traceback
import re

RE_VALID = re.compile("[a-z0-9_-]*\Z")
RE_VALID = re.compile("[a-z0-9_-]*\Z")

KNOWN_STATES = ['Downloading','Seeding','Paused','Checking','Allocating','Queued','Error']
STATE = "state"
TRACKER = "tracker"
KEYWORD = "keyword"
LABEL = "label"
CONFIG_DEFAULTS = {
    "torrent_labels":{}, #torrent_id:label_id
    "labels":{}, #label_id:{name:value}
    "hide_zero_hits":False,
    "gtk_alfa":False
}
OPTIONS_KEYS = ["max_download_speed", "max_upload_speed",
    "max_connections", "max_upload_slots", "prioritize_first_last"]
NO_LABEL = "No Label"


def CheckInput(cond, message):
    if not cond:
        raise Exception(message)


class Core(CorePluginBase):
    def enable(self):
        log.info("*** Start Label plugin ***")

        self.plugin.register_status_field("tracker_host", self._status_get_tracker)
        self.plugin.register_status_field("label", self._status_get_label)

        #__init__
        core = self.plugin.get_core()
        self.config = ConfigManager("label.conf")
        self.core_cfg = ConfigManager("core.conf")
        self.set_config_defaults()

        #reduce typing, assigning some values to self...
        self.torrents = core.torrents.torrents
        self.labels = self.config.get("labels")
        self.torrent_labels = self.config.get("torrent_labels")

        log.debug("Label plugin enabled..")

    def clean_config(self):
        "remove invalid data from config-file"
        for torrent_id, label_id in list(self.torrent_labels.iteritems()):
            if (not label_id in self.labels) or (not torrent_id in self.torrents):
                log.debug("label: rm %s:%s" % (torrent_id,label_id))
                del self.torrent_labels[torrent_id]

    def save_config(self):
        self.clean_config()
        self.config.save()

    def set_config_defaults(self):
        changed = False
        for key, value in CONFIG_DEFAULTS.iteritems():
            if not key in self.config.config:
                self.config.config[key] = value
                changed = True
        if changed:
            pass
            #self.config.save()
        log.debug("label_config=%s" % self.config.config)

    def disable(self):
        # De-register the label field
        self.plugin.deregister_status_field("tracker_host")
        self.plugin.deregister_status_field("label")

    def update(self):
        pass

    ## Utils ##
    def get_tracker(self, torrent):
        """
        returns 1st tracker hostname
        save space: reduced to *.com without any subdomain dots before
        TODO: CLEANUP
        """
        log.debug(torrent)
        log.debug(torrent.trackers)
        if not torrent.trackers:
            return 'tracker-less'
        url = urlparse(torrent.trackers[0]['url'])
        if hasattr(url,'hostname'):
            host = (url.hostname or 'unknown?')
            parts = host.split(".")
            if len(parts) > 2:
                host = ".".join(parts[-2:])
            return host
        return 'No-tracker?'

    ## Filters ##
    def filter_state(self, torrents, value):
        "in/out: a list of torrent objects."
        log.debug("filter-state:%s" % value)
        for t in torrents:
            log.debug("s=%s" % t.state)
        return [t for t in torrents if t.state == value]

    def filter_tracker(self, torrents, value):
        "in/out: a list of torrent objects."
        return [t for t in torrents if self.get_tracker(t) == value]

    def filter_label(self, torrents, value):
        "in/out: a list of torrent objects."
        if value == NO_LABEL:
            value = None
            log.debug("NO_LABEL")
        return [t for t in torrents if self.torrent_labels.get(t.torrent_id) == value]

    def filter_keyword(self, torrents, value):
        value = value.lower().strip()
        "in/out: a list of torrent objects."
        return [t for t in torrents if value in t.filename.lower()]

    ## Items ##
    def get_state_filter_items(self):
        states = dict([(state, 0) for state in KNOWN_STATES])
        state_order = list(KNOWN_STATES)
        #state-simple:
        for t in self.torrents.values():
            if not t.state in state_order:
                state_order.append(t.state)
                states[t.state] = 0
            states[t.state] +=1
        #specialized-state:
            #todo: traffic.

        log.debug("hide-z:%s" % self.config["hide_zero_hits"])
        if self.config["hide_zero_hits"]:
            for state in set(KNOWN_STATES):
                log.debug(states.keys())
                if states[state] == 0 :
                    #del states[state]
                    state_order.remove(state)

        #return the filters sorted by STATES + add unknown states.
        return ([("All",len(self.torrents))] +
            [(state, states[state]) for state in state_order]
        )

    def get_tracker_filter_items(self):
        #trackers:
        trackers = {}
        for t in self.torrents.values():
            tracker = self.get_tracker(t)
            if not tracker in trackers:
                trackers[tracker] = 0
            trackers[tracker] +=1

        return [(tracker , trackers[tracker]) for tracker in sorted(trackers.keys())]

    def get_label_filter_items(self):
        no_label = 0
        labels = dict([(label_id, 0) for label_id in self.labels])
        for torrent_id in self.torrents:
            label_id = self.torrent_labels.get(torrent_id)
            if label_id:
                labels[label_id] +=1
            else:
                no_label +=1

        if self.config["hide_zero_hits"]:
            for label , count in list(labels.iteritems()):
                if count == 0:
                    del labels[label]

        return [(NO_LABEL, no_label)] + [(label_id, labels[label_id]) for label_id in sorted(labels.keys())]

    ## Public  ##
    def export_filter_items(self):
        """
        returns :
        {
            "CATEGORY" : [("filter_value",count), ...] , ...
        }
        --
        category's : ["state","tracker","label"]
        """
        result = {}

        result[STATE] = self.get_state_filter_items()
        result[TRACKER] = self.get_tracker_filter_items()
        result[LABEL] = self.get_label_filter_items()

        return result

    def export_get_labels(self):
        return sorted(self.labels.keys())

    def export_get_filtered_ids(self, filter_dict):
        """
        input : {"filter_cat":"filter_value",..}
        returns : a list of torrent_id's
        """
        torrents = self.torrents.values()
        if KEYWORD in filter_dict:
            torrents = self.filter_keyword(torrents, filter_dict[KEYWORD])

        if STATE in filter_dict and filter_dict[STATE] <> "":
            torrents = self.filter_state(torrents, filter_dict[STATE])

        if TRACKER in filter_dict:
            torrents = self.filter_tracker(torrents, filter_dict[TRACKER])

        if LABEL in filter_dict:
            torrents = self.filter_label(torrents, filter_dict[LABEL])
        return [t.torrent_id for t in torrents]


    #Labels:
    def export_add(self, label_id):
        """add a label
        see label_set_options for more options.
        """
        label_id = label_id.lower()
        CheckInput(RE_VALID.match(label_id) , _("Invalid label, valid characters:[a-z0-9_-]"))
        CheckInput(label_id, _("Empty Label"))
        CheckInput(not (label_id in self.labels) , _("Unknown Label"))


        #default to current global per-torrent settings.
        self.labels[label_id] = {
            "max_download_speed":self.core_cfg.config["max_download_speed_per_torrent"],
            "max_upload_speed":self.core_cfg.config["max_upload_speed_per_torrent"],
            "max_connections":self.core_cfg.config["max_connections_per_torrent"],
            "max_upload_slots":self.core_cfg.config["max_upload_slots_per_torrent"],
            "prioritize_first_last":self.core_cfg.config["prioritize_first_last_pieces"]
        }

    def export_remove(self, label_id):
        "remove a label"
        CheckInput(label_id in self.labels, _("Unknown Label"))
        del self.labels[label_id]
        self.clean_config()
        self.config.save()

    def export_set_options(self, label_id, options_dict , apply = False):
        """update the label options

        options_dict :
        {"max_download_speed":float(),
            "max_upload_speed":float(),
            "max_connections":int(),
            "max_upload_slots":int(),
            "prioritize_first_last":bool(),
        }

        apply : applies download-options to all torrents currently labelled by label_id
        """
        CheckInput(not (label_id in self.labels) , _("Unknown Label"))
        for key in options_dict.keys():
            if not key in OPTIONS_KEYS:
                raise Exception("label: Invalid options_dict key:%s" % key)

        self.labels[label_id].update(options_dict)

        options = self.labels[label_id]
        if apply:
            for torrent_id,label in self.torrent_labels.iteritems():
                if label_id == label:
                    torrent = self.torrents[torrent_id]
                    torrent.set_max_download_speed(options["max_download_speed"])
                    torrent.set_max_upload_speed(options["max_upload_speed"])
                    torrent.set_max_connections(options["max_connections"])
                    torrent.set_max_upload_slots(options["max_upload_slots"])
                    torrent.set_prioritize_first_last(options["prioritize_first_last"])

        self.config.save()

    def export_get_options(self, label_id):
        """returns the label options"""
        return self.labels[label_id]

    def export_set_torrent(self, torrent_id , label_id):
        """
        assign a label to a torrent
        removes a label if the label_id parameter is empty.
        """
        if label_id == NO_LABEL:
            label_id = None

        CheckInput((not label_id) or (label_id in self.labels)  , _("Unknown Label"))
        CheckInput(torrent_id in self.torrents  , _("Unknown Torrent"))

        if not label_id:
            if torrent_id in self.torrent_labels:
                del self.torrent_labels[torrent_id]
                self.clean_config()
        else:
            self.torrent_labels[torrent_id] = label_id
            #set speeds, etc:
            options = self.labels[label_id]
            torrent = self.torrents[torrent_id]
            torrent.set_max_download_speed(options["max_download_speed"])
            torrent.set_max_upload_speed(options["max_upload_speed"])
            torrent.set_max_connections(options["max_connections"])
            torrent.set_max_upload_slots(options["max_upload_slots"])
            torrent.set_prioritize_first_last(options["prioritize_first_last"])

        self.config.save()


    def export_get_global_options(self):
        "see : label_set_global_options"
        return {
            "hide_zero_hits":self.config.get("hide_zero_hits"),
            "gtk_alfa":self.config.get("gtk_alfa")
        }

    def export_set_global_options(self, options):
        """global_options:
        {
            "hide_zero":bool() #label_filter_items only returns items with more than 0 hits.
        }
        """
        for key in ["hide_zero_hits", "gtk_alfa"]:
            if options.has_key(key):
                self.config.set(key, options[key])
        self.config.save()


    ## Status fields ##
    def _status_get_tracker(self, torrent_id):
        return self.get_tracker(self.torrents[torrent_id])

    def _status_get_label(self, torrent_id):
        return self.torrent_labels.get(torrent_id) or ""

if __name__ == "__main__":
    import test

