#
# core.py
#
# Copyright (C) 2008-2009 Fredrik Eriksson <feeder@winterbird.org>
# Copyright (C) 2009 David Mohr <david@mcbf.net>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
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

import logging
import feedparser # for parsing rss feeds
import threading  # for threaded updates
import re         # for regular expressions
from twisted.internet.task import LoopingCall

from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export

log = logging.getLogger(__name__)

DEFAULT_PREFS = {
    "feeds": {},
    "filters": {},
    "updatetime": 15,
    "history": []
}

# Helper classes

class Feed:
    """
    Class for the Feed object (containging feed configurations)
    """
    def __init__(self):
        self.url = ""
        self.cookies = {}
        self.updatetime = 15

    def get_config(self):
        try:
            tmp = self.cookies
        except Exception, e:
            log.debug("Old feed without cookies... updating")
            self.cookies = {}
        return {'url': self.url, 'updatetime': self.updatetime, 'cookies': self.cookies}

    def set_config(self, config):
        self.url = config['url']
        self.updatetime = config['updatetime']
        self.cookies = config['cookies']


class Filter:
    """
    Class for the Filter object (containing filter configurations)
    """

    def __init__(self):
        self.regex = ""
        self.feeds = [] #TODO activate filter per feed
        self.all_feeds = True
        self.active = True

        # by default, set the configuration to match
        # the per-torrent settings in deluge
        def_conf = component.get("Core").get_config()
        self.max_download_speed = def_conf['max_download_speed_per_torrent']
        self.max_upload_speed = def_conf['max_upload_speed_per_torrent']
        self.max_connections = def_conf['max_connections_per_torrent']
        self.max_upload_slots = def_conf['max_upload_slots_per_torrent']
        self.prioritize_first_last_pieces = def_conf['prioritize_first_last_pieces']
        self.auto_managed = def_conf['auto_managed']
        self.download_location = def_conf['download_location']

        self.stop_at_ratio = def_conf['stop_seed_at_ratio']
        self.stop_ratio = def_conf['stop_seed_ratio']
        self.remove_at_ratio = def_conf['remove_seed_at_ratio']

    def get_config(self):
        def_conf = component.get("Core").get_config()

        try:
            tmp = self.active
        except Exception, e:
            log.debug("Old filter detected (pre 0.3), updating...")
            self.active = True

        try:
            tmp = self.stop_at_ratio
            tmp = self.stop_ratio
            tmp = self.remove_at_ratio
        except:
            log.debug("Old filter detected (pre 0.4), updating...")
            self.stop_at_ratio = def_conf['stop_seed_at_ratio']
            self.stop_ratio = def_conf['stop_seed_ratio']
            self.remove_at_ratio = def_conf['remove_seed_at_ratio']

        conf = {
            'regex': self.regex,
            'feeds': self.feeds,
            'all_feeds': self.all_feeds,
            'active' : self.active,
            'max_download_speed': self.max_download_speed,
            'max_upload_speed': self.max_upload_speed,
            'max_connections': self.max_connections,
            'max_upload_slots': self.max_upload_slots,
            'prioritize_first_last_pieces': self.prioritize_first_last_pieces,
            'auto_managed': self.auto_managed,
            'download_location':self.download_location,
            'remove_at_ratio':self.remove_at_ratio,
            'stop_ratio': self.stop_ratio,
            'stop_at_ratio': self.stop_at_ratio }

        return conf

    def set_config(self, conf):
        self.regex = conf['regex']
        self.feeds = conf['feeds']
        self.all_feeds = conf['all_feeds']
        self.active = conf['active']
        self.max_download_speed = int(conf['max_download_speed'])
        self.max_upload_speed = int(conf['max_upload_speed'])
        self.max_connections = int(conf['max_connections'])
        self.max_upload_slots = int(conf['max_upload_slots'])
        self.prioritize_first_last_pieces = conf['prioritize_first_last_pieces']
        self.auto_managed = conf['auto_managed']
        self.download_location = conf['download_location']
        self.remove_at_ratio = conf['remove_at_ratio']
        self.stop_ratio = float(conf['stop_ratio'])
        self.stop_at_ratio = conf['stop_at_ratio']


class Core(CorePluginBase):
    def enable(self):
        self.config = deluge.configmanager.ConfigManager("feeder.conf", DEFAULT_PREFS)
        self.feeds = {}
        self.timers = {}
        self.history = self.config['history']
        self.time = 0

        # Setting default timer to configured update time
        for feed in self.config['feeds']:
            self.timers[feed] = LoopingCall(self.update_feed, feed)
            self.timers[feed].start( self.config['feeds'][feed].updatetime * 60)


    def disable(self):
        self.config['history'] = self.history
        self.config.save()


    def update(self):
      pass



#=================Exported functions==================

    @export
    def set_config(self, config):
        """sets the config dictionary"""
        for key in config.keys():
            self.config[key] = config[key]
        self.config.save()

####################Configuration Getters##################

    @export
    def get_config(self):
        """returns the config dictionary"""
        return self.config.config

    @export
    def get_feed_config(self, feedname):
        """Returns configuration for a feed"""
        return self.config['feeds'][feedname].get_config()

    @export
    def get_filter_config(self, filtername):
        """Returns a configuration for a filter"""
        return self.config['filters'][filtername].get_config()

####################Information Getters####################

    @export
    def get_feeds(self):
        """Returns a list of the configured feeds"""
        feeds = []
        for feedname in self.config['feeds']:
            feeds.append(feedname)
        feeds.sort(key=string.lower)
        return feeds

    @export
    def get_filters(self):
        """Returns a list of all available filters"""
        filters = []
        for filter in self.config['filters']:
            filters.append(filter)
        filters.sort(key=string.lower)
        return filters

    @export
    def get_items(self, feedname):
        """Returns a dictionary with feedname:link"""
        try:
            items = {}
            feed = self.feeds[feedname]
            for entry in feed['entries']:
                items[entry.title] = entry.link
        except Exception, e:
            items = {}
            log.warning("Feed '%s' not loaded", feedname)
        return items

    @export
    def test_filter(self, regex):
        filters = { "to_test":Filter() }
        conf = filters["to_test"].get_config()
        conf["regex"] = regex
        filters["to_test"].set_config(conf)
        hits = {}
        for feed in self.feeds:
            hits.update(self.run_filters(feed, filters, test=True))
        return hits

    @export
    def add_feed(self, config):
        """adds/updates a feed and, for whatever reason, sets the default timeout"""

        # save the feedname and remove it from the config
        feedname = config['name']
        del config['name']

        # check if the feed already exists and save config
        try:
            conf = self.config['feeds'][feedname].get_config()
            del self.config['feeds'][feedname]
        except Exception, e:
            conf = {}

        # update configuration
        for var in config:
            conf[var] = config[var]

        # save as default update time
        try:
           self.config['updatetime'] = config['updatetime']
        except Exception, e:
            log.warning("updatetime not set when adding feed %s", feedname)

        # Create the new feed
        newfeed = Feed()
        newfeed.set_config(conf)

        # Add a timer (with default timer for now, since we can't get ttl just yet)...
        self.timers[feedname] = LoopingCall(self.update_feed, feedname)

        # Save the new feed
        self.config['feeds'].update({feedname: newfeed })
        self.config.save()

        # Start the timeout, which will also update the new feed
        self.timers[feedname].start(newfeed.updatetime * 60)

    @export
    def remove_feed(self, feedname):
        """Remove a feed"""
        if self.feeds.has_key(feedname): # Check if we have the feed saved and remove it
            del self.feeds[feedname]
        if self.timers.has_key(feedname): # Check if we have a timer for this feed and remove it
            self.timers[feedname].stop()
            del self.timers[feedname]
        if self.config['feeds'].has_key(feedname): # Check if we have the feed in the configuration and remove it
            del self.config['feeds'][feedname]
        self.config.save()

    @export
    def add_filter(self, name):
        """Adds a new filter to the configuration"""
        if not self.config['filters'].has_key(name): # we don't want to add a filter that already exists
            self.config['filters'][name] = Filter()
            self.config.save()

    @export
    def set_filter_config(self, filtername, conf):
        """Changes the options for a filter"""
        oldconf = self.config['filters'][filtername].get_config()
        for item in conf:
            oldconf[item] = conf[item]

        self.config['filters'][filtername].set_config(oldconf)
        self.config.save()
        for feed in self.config['feeds']: # we would like to check if the filter now matches something new
            self.run_filters(feed)

    @export
    def remove_filter(self, name):
        """Removes a filter"""
        if self.config['filters'].has_key(name): # Can't remove a filter that doesn't exists
            del self.config['filters'][name]
            self.config.save()

#=================Internal functions================

    def update_feed(self, feedname):
        """Start a thread to update a single feed"""
        threading.Thread(
            target=self.update_feed_thread,
            args=(self.on_feed_updated, feedname)).start()

        # Need to return true to not destoy timer...
        return True

    def update_feed_thread(self, callback, feedname):
        """updates a feed"""
        feed = self.config['feeds'][feedname]
        try:
            self.feeds[feedname] = feedparser.parse(feed.url)
        except Exception, e:
            log.warning("Error parsing feed %s: %s", feedname, e)
        else:
            callback(feedname)

    def on_feed_updated(self, feedname):
        """Run stuff when a feed has been updated"""

        # Not all feeds contain a ttl value, but if it does
        # we would like to obey it
        try:
            if not self.feeds[feedname].ttl == self.config['feeds'][feedname].updatetime:
                log.debug("feed '%s' request a ttl of %s, updating timer", feedname, self.feeds[feedname].ttl)
                self.config['feeds'][feedname].updatetime = self.feeds[feedname].ttl
                self.timers[feedname].stop()
                self.timers[feedname].start(self.config['feeds'][feedname].updatetime * 60)
        except Exception, e:
            log.debug("feed '%s' has no ttl set, will use default timer", feedname)

        # Run filters on the feed
        self.run_filters(feedname)

    def run_filters(self, feedname, filters={}, test=False):
        """Test all available filters on the given feed"""
        if not filters:
            filters = self.config['filters']
        log.debug("will test filters %s", filters)
        hits = {}
        # Test every entry...
        for entry in self.feeds[feedname]['entries']:
            # ...and every filter
            for filter in filters:
                # We need to be able to run feeds saved before implementation of actiave/deactivate filter (pre 0.3) TODO
                try:
                    if not filters[filter].active:
                        continue
                except:
                    log.debug("old filter, will assume filter is activated")

                if filters[filter].regex == "": # we don't want a empty regex...
                    log.warning("Filter '%s' has not been configured, ignoring!", filter)
                    continue

                # if the filter isn't supposed to be run on this feed we don't want to run it...
#                if filter.all_feeds or self.config['filters'][filter].feeds.has_element(feedname) : # ...apparently has_element doesn't work on arrays... TODO
                if self.test_filter(entry, filters[filter].regex):
                    if test:
                        hits[entry.title] = entry.link
                    else:
                        opts = filters[filter].get_config()
                        #remove filter options that should not be passed on to the torrent.
                        del opts['regex']
                        del opts['feeds']
                        del opts['all_feeds']

                        # history patch from Darrell Enns, slightly modified :)
                        # check history to prevent multiple adds of the same torrent
                        log.debug("testing %s", entry.link)
                        if not entry.link in self.history:
                            self.add_torrent(entry.link, opts, self.feeds[feedname].cookies)
                            self.history.append(entry.link)

                            #limit history to 50 entries
                            if len(self.history)>50:
                                self.history=self.history[-50:]
                                log.debug("wrapping history")
                        else:
                            log.debug("'%s' is in history, will not download", entry.link)
        return hits


    def test_filter(self, entry, filter):
        """Tests a filter to a given rss entry"""
        f = re.compile(filter, re.IGNORECASE)
        if f.search(entry.title) or f.search(entry.link):
            log.debug("RSS item '%s' matches filter '%s'", entry.title, filter)
            return True
        else:
            return False

    def add_torrent(self, url, torrent_options, headers):
        log.debug("Attempting to add torrent %s", url)
        component.get("Core").add_torrent_url(url, torrent_options, headers)
