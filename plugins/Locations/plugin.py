# -*- coding: utf-8 -*-
# Locations plugin for Deluge - keep different settings for each location.
# Copyright (C) 2007 - Kristoffer Lundén <kristoffer.lunden@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os, re
import deluge.common, deluge.pref

LOCATION_KEYS = [
	"listen_on",
    "random_port",
	"max_active_torrents",
	"proxy_type",
	"peer_proxy",
	"tracker_proxy",
	"dht_proxy",
	"proxy_hostname",
	"proxy_username",
	"proxy_password",
	"proxy_port",
	"auto_end_seeding",
	"auto_seed_ratio",
	"end_seed_ratio",
	"max_connections_global",
	"max_connections_per_torrent",
	"max_download_rate",
	"max_download_rate_bps",
	"max_number_downloads",
	"max_upload_slots_global",
	"max_upload_slots_per_torrent",
	"max_upload_rate",
	"max_upload_rate_bps",
	"max_uploads",
    "max_upload_speed",
    "max_download_speed",
	"use_natpmp",
	"use_upnp",
	"use_utpex",
    "web_proxy_type",
    "peer_proxy_type",
    "dht_proxy_type",
    "tracker_proxy_type",
    "peer_proxy",
    "tracker_proxy",
    "dht_proxy",
    "peer_proxy_hostname",
    "peer_proxy_username",
    "peer_proxy_password",
    "peer_proxy_port",
    "dht_proxy_hostname",
    "dht_proxy_username",
    "dht_proxy_password",
    "dht_proxy_port",
    "web_proxy_hostname",
    "web_proxy_username",
    "web_proxy_password",
    "web_proxy_port",
    "tracker_proxy_hostname",
    "tracker_proxy_username",
    "tracker_proxy_password",
    "tracker_proxy_port"
]


class plugin_Locations:

  def __init__(self, path, deluge_core, deluge_interface):

    self.path = path
    self.core = deluge_core
    self.interface = deluge_interface

    #self.do_debug = True
    self.do_debug = False

    self.current_mac = None
    self.timeout = 0

    self.pref = self.core.get_config()

    self.config_dir = deluge.common.CONFIG_DIR + "/Locations"
    if not os.path.exists(self.config_dir):
      os.mkdir(self.config_dir)

  # update will be called every UPDATE_INTERVAL (usually about 1 second)
  # we use a timeout to listen every minute instead
  def update(self):
    self.timeout = self.timeout - 1
    #self.debug(self.timeout)

    if self.timeout > 0:
  		return
    
    self.debug("Time to check for MAC")
    self.timeout = 60

    self.update_mac()

  def update_mac(self):    
    mac = self.find_gateway_mac()

    if mac is not None:
      if mac != self.current_mac:
        # MAC address have changed (possibly from None)
        self.save_prefs(self.current_mac)
        self.load_prefs(mac)
        self.current_mac = mac

  # unload is called when the plugin is removed or Deluge is shut down
  # save preferences for current MAC
  def unload(self):
    self.save_prefs(self.current_mac)

  # Find out MAC address of Gateway via standard files. Needs testing.
  def find_gateway_mac(self):
    try:
      routes = open('/proc/net/route')
      for ln in routes:
        gateway = ln.split()[2]
        #self.debug(gateway)
        if gateway != "00000000" and re.match(r"[0-9a-fA-F]{8}", gateway):
          ip  = str(int(gateway[6:8],16)) + '.'
          ip += str(int(gateway[4:6],16)) + '.'
          ip += str(int(gateway[2:4],16)) + '.'
          ip += str(int(gateway[0:2],16))
          self.debug("Gateway found: " + ip)
          arp = open('/proc/net/arp', 'rb')
          for line in arp:
            split = line.split()
            if split[0] == ip and split[3] != "00:00:00:00:00:00" and re.match(r"((?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2})", split[3]):
              mac = split[3]
              self.debug("MAC found: " + mac)
              return mac
          arp.close()
      routes.close()
    except IOError:
      pass
    return None

  # Save preferences to MAC specific file
  def save_prefs(self, mac):
    if mac is None:
      return
    self.debug("Saving prefs for %s" % (mac))
    config_file = self.config_filename(mac)
    conf = deluge.pref.Preferences(config_file, False)
    for key in LOCATION_KEYS:
      if self.pref.has_key(key):
        conf.set(key, self.pref.get(key))
    conf.save()  

  # Load preferences from MAC specific file
  def load_prefs(self, mac):
    if mac is None:
      return
    self.debug("Loading prefs for %s" % (mac))
    config_file = self.config_filename(mac)
    conf = deluge.pref.Preferences(config_file, False)
    for key in LOCATION_KEYS:
      if conf.has_key(key):
        self.pref.set(key, conf.get(key))
    self.interface.apply_prefs()

  def config_filename(self, mac):
    mac_esc = re.sub(":","_",mac)
    return "%s/%s.conf" % (self.config_dir, mac_esc)

  def debug(self, text):
    if self.do_debug:
      print "Locations: %s" % (text)
