#
# preferencesmanager.py
#
# Copyright (C) 2008-2010 Andrew Resch <andrewresch@gmail.com>
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


import os
import logging
import threading
import random

from twisted.internet.task import LoopingCall

from deluge._libtorrent import lt

from deluge.event import ConfigValueChangedEvent
import deluge.configmanager
import deluge.common
import deluge.component as component

log = logging.getLogger(__name__)

DEFAULT_PREFS = {
    "send_info": False,
    "info_sent": 0.0,
    "daemon_port": 58846,
    "allow_remote": False,
    "pre_allocate_storage": False,
    "download_location": deluge.common.get_default_download_dir(),
    "listen_ports": [6881, 6891],
    "listen_interface": "",
    "random_port": True,
    "listen_random_port": None,
    "listen_use_sys_port": False,
    "listen_reuse_port": True,
    "outgoing_ports": [0, 0],
    "random_outgoing_ports": True,
    "copy_torrent_file": False,
    "del_copy_torrent_file": False,
    "torrentfiles_location": deluge.common.get_default_download_dir(),
    "plugins_location": os.path.join(deluge.configmanager.get_config_dir(), "plugins"),
    "prioritize_first_last_pieces": False,
    "sequential_download": False,
    "dht": True,
    "upnp": True,
    "natpmp": True,
    "utpex": True,
    "lt_tex": True,
    "lsd": True,
    "enc_in_policy": 1,
    "enc_out_policy": 1,
    "enc_level": 2,
    "max_connections_global": 200,
    "max_upload_speed": -1.0,
    "max_download_speed": -1.0,
    "max_upload_slots_global": 4,
    "max_half_open_connections": (lambda: deluge.common.windows_check() and
                                  (lambda: deluge.common.vista_check() and 4 or 8)() or 50)(),
    "max_connections_per_second": 20,
    "ignore_limits_on_local_network": True,
    "max_connections_per_torrent": -1,
    "max_upload_slots_per_torrent": -1,
    "max_upload_speed_per_torrent": -1,
    "max_download_speed_per_torrent": -1,
    "enabled_plugins": [],
    "add_paused": False,
    "max_active_seeding": 5,
    "max_active_downloading": 3,
    "max_active_limit": 8,
    "dont_count_slow_torrents": False,
    "queue_new_to_top": False,
    "stop_seed_at_ratio": False,
    "remove_seed_at_ratio": False,
    "stop_seed_ratio": 2.00,
    "share_ratio_limit": 2.00,
    "seed_time_ratio_limit": 7.00,
    "seed_time_limit": 180,
    "auto_managed": True,
    "move_completed": False,
    "move_completed_path": deluge.common.get_default_download_dir(),
    "move_completed_paths_list": [],
    "download_location_paths_list": [],
    "path_chooser_show_chooser_button_on_localhost": True,
    "path_chooser_auto_complete_enabled": True,
    "path_chooser_accelerator_string": "Tab",
    "path_chooser_max_popup_rows": 20,
    "path_chooser_show_hidden_files": False,
    "new_release_check": True,
    "proxy": {
        "type": 0,
        "hostname": "",
        "username": "",
        "password": "",
        "port": 8080,
        "proxy_hostnames": True,
        "proxy_peer_connections": True,
    },
    "i2p_proxy": {
        "hostname": "",
        "port": 0
    },
    "peer_tos": "0x00",
    "rate_limit_ip_overhead": True,
    "geoip_db_location": "/usr/share/GeoIP/GeoIP.dat",
    "cache_size": 512,
    "cache_expiry": 60,
    "auto_manage_prefer_seeds": False,
    "shared": False,
    "super_seeding": False,
    "priority": 0
}


class PreferencesManager(component.Component):
    def __init__(self):
        component.Component.__init__(self, "PreferencesManager")
        self.config = deluge.configmanager.ConfigManager("core.conf", DEFAULT_PREFS)
        if "proxies" in self.config:
            log.warning("Updating config file for proxy, using 'peer' values to fill new 'proxy' setting")
            self.config["proxy"].update(self.config["proxies"]['peer'])
            log.warning("New proxy config is: %s", self.config["proxy"])
            del self.config["proxies"]

    def start(self):
        self.core = component.get("Core")
        self.session = component.get("Core").session
        self.new_release_timer = None

        # Setup listen port followed by dht to ensure both use same port.
        self.__set_listen_on()
        self._on_set_dht("dht", self.config["dht"])

        # Set the initial preferences on start-up
        for key in DEFAULT_PREFS:
            # Listen port and dht already setup in correct order so skip
            # repeated running of the dht and listen port functions on startup.
            if key in ("dht", "random_port") or key.startswith("listen_"):
                continue
            self.do_config_set_func(key, self.config[key])

        self.config.register_change_callback(self._on_config_value_change)

    def stop(self):
        if self.new_release_timer and self.new_release_timer.running:
            self.new_release_timer.stop()

    # Config set functions
    def do_config_set_func(self, key, value):
        on_set_func = getattr(self, "_on_set_" + key, None)
        if on_set_func:
            on_set_func(key, value)

    def session_set_setting(self, key, value):
        settings = self.session.get_settings()
        settings[key] = value
        self.session.set_settings(settings)

    def _on_config_value_change(self, key, value):
        self.do_config_set_func(key, value)
        component.get("EventManager").emit(ConfigValueChangedEvent(key, value))

    def _on_set_torrentfiles_location(self, key, value):
        if self.config["copy_torrent_file"]:
            try:
                os.makedirs(value)
            except Exception, e:
                log.debug("Unable to make directory: %s", e)

    def _on_set_listen_ports(self, key, value):
        self.__set_listen_on()

    def _on_set_listen_interface(self, key, value):
        self.__set_listen_on()

    def _on_set_random_port(self, key, value):
        log.debug("Listen on random port set to %s", value)
        self.__set_listen_on()

    def __set_listen_on(self):
        """ Set the ports and interface address to listen for incoming connections on."""
        listen_ports = self.config["listen_ports"]
        interface = str(self.config["listen_interface"].strip())
        reuse_port = self.config["listen_reuse_port"]
        use_sys_port = self.config["listen_use_sys_port"]

        if self.config["random_port"] and self.config["listen_random_port"] is not None:
            port = self.config["listen_random_port"]
        elif self.config["random_port"]:
            port = random.randrange(49152, 65525)
            self.config["listen_random_port"] = port
            listen_ports = [port, port]
        else:
            self.config["listen_random_port"] = None

        # If a single port is set then enable re-use port flag
        if listen_ports[0] == listen_ports[1]:
            reuse_port = True

        flags = ((lt.listen_on_flags_t.listen_no_system_port if not use_sys_port else 0) |
                 (lt.listen_on_flags_t.listen_reuse_address if reuse_port else 0))

        log.debug("Listen on Interface: %s, Ports: %s-%s and Flags: reuse_port: %s, use_sys_port: %s",
                  interface, listen_ports[0], listen_ports[1], reuse_port, use_sys_port)
        try:
            self.session.listen_on(listen_ports[0], listen_ports[1], interface, flags)
        except RuntimeError as ex:
            if ex.message == "Invalid Argument":
                log.error("Error setting listen interface (must be IP Address): %s %s-%s",
                          interface, listen_ports[0], listen_ports[1])

    def _on_set_outgoing_ports(self, key, value):
        if not self.config["random_outgoing_ports"]:
            log.debug("outgoing port range set to %s-%s", value[0], value[1])
            self.session_set_setting("outgoing_ports", (value[0], value[1]))

    def _on_set_random_outgoing_ports(self, key, value):
        if value:
            self.session.outgoing_ports(0, 0)

    def _on_set_peer_tos(self, key, value):
        log.debug("setting peer_tos to: %s", value)
        try:
            self.session_set_setting("peer_tos", chr(int(value, 16)))
        except ValueError, e:
            log.debug("Invalid tos byte: %s", e)
            return

    def _on_set_dht(self, key, value):
        log.debug("dht value set to %s", value)
        if value:
            self.session.start_dht()
            self.session.add_dht_router("router.bittorrent.com", 6881)
            self.session.add_dht_router("router.utorrent.com", 6881)
            self.session.add_dht_router("router.bitcomet.com", 6881)
        else:
            self.session.stop_dht()

    def _on_set_upnp(self, key, value):
        log.debug("upnp value set to %s", value)
        if value:
            self.session.start_upnp()
        else:
            self.session.stop_upnp()

    def _on_set_natpmp(self, key, value):
        log.debug("natpmp value set to %s", value)
        if value:
            self.session.start_natpmp()
        else:
            self.session.stop_natpmp()

    def _on_set_lsd(self, key, value):
        log.debug("lsd value set to %s", value)
        if value:
            self.session.start_lsd()
        else:
            self.session.stop_lsd()

    def _on_set_utpex(self, key, value):
        log.debug("utpex value set to %s", value)
        if value:
            self.session.add_extension("ut_pex")

    def _on_set_lt_tex(self, key, value):
        log.debug("lt_tex value set to %s", value)
        if value:
            self.session.add_extension("lt_trackers")

    def _on_set_enc_in_policy(self, key, value):
        self._on_set_encryption(key, value)

    def _on_set_enc_out_policy(self, key, value):
        self._on_set_encryption(key, value)

    def _on_set_enc_level(self, key, value):
        self._on_set_encryption(key, value)

    def _on_set_encryption(self, key, value):
        log.debug("encryption value %s set to %s..", key, value)
        pe_enc_level = {0: lt.enc_level.plaintext, 1: lt.enc_level.rc4, 2: lt.enc_level.both}

        pe_settings = lt.pe_settings()
        pe_settings.out_enc_policy = \
            lt.enc_policy(self.config["enc_out_policy"])
        pe_settings.in_enc_policy = lt.enc_policy(self.config["enc_in_policy"])
        pe_settings.allowed_enc_level = lt.enc_level(pe_enc_level[self.config["enc_level"]])
        pe_settings.prefer_rc4 = True
        self.session.set_pe_settings(pe_settings)
        set = self.session.get_pe_settings()
        log.debug("encryption settings:\n\t\t\tout_policy: %s\n\t\t\
        in_policy: %s\n\t\t\tlevel: %s\n\t\t\tprefer_rc4: %s",
                  set.out_enc_policy,
                  set.in_enc_policy,
                  set.allowed_enc_level,
                  set.prefer_rc4)

    def _on_set_max_connections_global(self, key, value):
        log.debug("max_connections_global set to %s..", value)
        self.session_set_setting("connections_limit", value)

    def _on_set_max_upload_speed(self, key, value):
        log.debug("max_upload_speed set to %s..", value)
        # We need to convert Kb/s to B/s
        if value < 0:
            _value = -1
        else:
            _value = int(value * 1024)
        self.session_set_setting("upload_rate_limit", _value)

    def _on_set_max_download_speed(self, key, value):
        log.debug("max_download_speed set to %s..", value)
        # We need to convert Kb/s to B/s
        if value < 0:
            _value = -1
        else:
            _value = int(value * 1024)
        self.session_set_setting("download_rate_limit", _value)

    def _on_set_max_upload_slots_global(self, key, value):
        log.debug("max_upload_slots_global set to %s..", value)
        self.session_set_setting("unchoke_slots_limit", value)

    def _on_set_max_half_open_connections(self, key, value):
        log.debug("max_half_open_connections set to %s..", value)
        self.session_set_setting("half_open_limit", value)

    def _on_set_max_connections_per_second(self, key, value):
        log.debug("max_connections_per_second set to %s..", value)
        self.session_set_setting("connection_speed", value)

    def _on_set_ignore_limits_on_local_network(self, key, value):
        log.debug("ignore_limits_on_local_network set to %s..", value)
        self.session_set_setting("ignore_limits_on_local_network", value)

    def _on_set_share_ratio_limit(self, key, value):
        log.debug("%s set to %s..", key, value)
        self.session_set_setting("share_ratio_limit", value)

    def _on_set_seed_time_ratio_limit(self, key, value):
        log.debug("%s set to %s..", key, value)
        self.session_set_setting("seed_time_ratio_limit", value)

    def _on_set_seed_time_limit(self, key, value):
        log.debug("%s set to %s..", key, value)
        # This value is stored in minutes in deluge, but libtorrent wants seconds
        self.session_set_setting("seed_time_limit", int(value * 60))

    def _on_set_max_active_downloading(self, key, value):
        log.debug("%s set to %s..", key, value)
        self.session_set_setting("active_downloads", value)

    def _on_set_max_active_seeding(self, key, value):
        log.debug("%s set to %s..", key, value)
        self.session_set_setting("active_seeds", value)

    def _on_set_max_active_limit(self, key, value):
        log.debug("%s set to %s..", key, value)
        self.session_set_setting("active_limit", value)

    def _on_set_dont_count_slow_torrents(self, key, value):
        log.debug("%s set to %s..", key, value)
        self.session_set_setting("dont_count_slow_torrents", value)

    def _on_set_send_info(self, key, value):
        log.debug("Sending anonymous stats..")
        """sends anonymous stats home"""
        class SendInfoThread(threading.Thread):
            def __init__(self, config):
                self.config = config
                threading.Thread.__init__(self)

            def run(self):
                import time
                now = time.time()
                # check if we've done this within the last week or never
                if (now - self.config["info_sent"]) >= (60 * 60 * 24 * 7):
                    import deluge.common
                    from urllib import quote_plus
                    from urllib2 import urlopen
                    import platform
                    try:
                        url = "http://deluge-torrent.org/stats_get.php?processor=" + \
                            platform.machine() + "&python=" + platform.python_version() \
                            + "&deluge=" + deluge.common.get_version() \
                            + "&os=" + platform.system() \
                            + "&plugins=" + quote_plus(":".join(self.config["enabled_plugins"]))
                        urlopen(url)
                    except IOError, e:
                        log.debug("Network error while trying to send info: %s", e)
                    else:
                        self.config["info_sent"] = now
        if value:
            SendInfoThread(self.config).start()

    def _on_set_new_release_check(self, key, value):
        if value:
            log.debug("Checking for new release..")
            threading.Thread(target=self.core.get_new_release).start()
            if self.new_release_timer and self.new_release_timer.running:
                self.new_release_timer.stop()
            # Set a timer to check for a new release every 3 days
            self.new_release_timer = LoopingCall(
                self._on_set_new_release_check, "new_release_check", True)
            self.new_release_timer.start(72 * 60 * 60, False)
        else:
            if self.new_release_timer and self.new_release_timer.running:
                self.new_release_timer.stop()

    def _on_set_proxy(self, key, value):
        log.debug("Setting proxy to: %s", value)
        proxy_settings = lt.proxy_settings()
        proxy_settings.type = lt.proxy_type(value["type"])
        proxy_settings.username = value["username"]
        proxy_settings.password = value["password"]
        proxy_settings.hostname = value["hostname"]
        proxy_settings.port = value["port"]
        proxy_settings.proxy_hostnames = value["proxy_hostnames"]
        proxy_settings.proxy_peer_connections = value["proxy_peer_connections"]
        self.session.set_proxy(proxy_settings)

    def _on_set_i2p_proxy(self, key, value):
        log.debug("Setting I2P proxy to: %s", value)
        proxy_settings = lt.proxy_settings()
        proxy_settings.hostname = value["hostname"]
        proxy_settings.port = value["port"]
        try:
            self.session.set_i2p_proxy(proxy_settings)
        except RuntimeError as ex:
            log.error("Unable to set I2P Proxy: %s", ex)

    def _on_set_rate_limit_ip_overhead(self, key, value):
        log.debug("%s: %s", key, value)
        self.session_set_setting("rate_limit_ip_overhead", value)

    def _on_set_geoip_db_location(self, key, value):
        log.debug("%s: %s", key, value)
        # Load the GeoIP DB for country look-ups if available
        geoip_db = ""
        if os.path.exists(value):
            geoip_db = value
        elif os.path.exists(deluge.common.resource_filename("deluge", os.path.join("data", "GeoIP.dat"))):
            geoip_db = deluge.common.resource_filename(
                "deluge", os.path.join("data", "GeoIP.dat")
            )
        else:
            log.warning("Unable to find GeoIP database file!")

        if geoip_db:
            try:
                self.session.load_country_db(str(geoip_db))
            except Exception, e:
                log.error("Unable to load geoip database!")
                log.exception(e)

    def _on_set_cache_size(self, key, value):
        log.debug("%s: %s", key, value)
        self.session_set_setting("cache_size", value)

    def _on_set_cache_expiry(self, key, value):
        log.debug("%s: %s", key, value)
        self.session_set_setting("cache_expiry", value)

    def _on_auto_manage_prefer_seeds(self, key, value):
        log.debug("%s set to %s..", key, value)
        self.session_set_setting("auto_manage_prefer_seeds", value)
