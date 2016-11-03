# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2010 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#


import logging
import os
import random
import threading

from twisted.internet.task import LoopingCall

import deluge.common
import deluge.component as component
import deluge.configmanager
from deluge._libtorrent import lt
from deluge.event import ConfigValueChangedEvent

try:
    import GeoIP
except ImportError:
    GeoIP = None

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
    "anonymous_mode": False,
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

        self.core = component.get("Core")
        self.session = component.get("Core").session
        self.new_release_timer = None

    def start(self):
        # Setup listen port followed by dht to ensure both use same port.
        self.__set_listen_on()
        self._on_set_dht("dht", self.config["dht"])

        # Set the initial preferences on start-up
        for key in DEFAULT_PREFS:
            # Listen port and dht already setup in correct order so skip running again.
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
            if log.isEnabledFor(logging.DEBUG):
                log.debug("Config key: %s set to %s..", key, value)
            on_set_func(key, value)

    def session_set_setting(self, key, value):
        try:
            self.session.apply_settings({key: value})
        except AttributeError:
            # Deprecated in libtorrent 1.1
            if key in ("enable_lsd", "enable_upnp", "enable_natpmp", "enable_dht"):
                start_stop = key.replace("enable", "start") if value else key.replace("enable", "stop")
                getattr(self.session, start_stop)()
            elif key == "dht_bootstrap_nodes":
                self.session.add_dht_router("router.bittorrent.com", 6881)
                self.session.add_dht_router("router.utorrent.com", 6881)
                self.session.add_dht_router("router.bitcomet.com", 6881)
            else:
                self.session.set_settings({key: value})

    def _on_config_value_change(self, key, value):
        if self.get_state() == "Started":
            self.do_config_set_func(key, value)
            component.get("EventManager").emit(ConfigValueChangedEvent(key, value))

    def _on_set_torrentfiles_location(self, key, value):
        if self.config["copy_torrent_file"]:
            try:
                os.makedirs(value)
            except OSError as ex:
                log.debug("Unable to make directory: %s", ex)

    def _on_set_listen_ports(self, key, value):
        self.__set_listen_on()

    def _on_set_listen_interface(self, key, value):
        self.__set_listen_on()

    def _on_set_random_port(self, key, value):
        self.__set_listen_on()

    def __set_listen_on(self):
        """ Set the ports and interface address to listen for incoming connections on."""
        if self.config["random_port"]:
            if not self.config["listen_random_port"]:
                self.config["listen_random_port"] = random.randrange(49152, 65525)
            listen_ports = [self.config["listen_random_port"]] * 2  # use single port range
        else:
            self.config["listen_random_port"] = None
            listen_ports = self.config["listen_ports"]

        interface = str(self.config["listen_interface"].strip())

        log.debug("Listen Interface: %s, Ports: %s with use_sys_port: %s",
                  interface, listen_ports, self.config["listen_use_sys_port"])
        try:
            interfaces = ["%s:%s" % (interface, port) for port in range(listen_ports[0], listen_ports[1]+1)]
            self.session.apply_setting({"listen_system_port_fallback", self.config["listen_use_sys_port"]})
            self.session.apply_setting({"listen_interfaces", interfaces})
        except AttributeError:
            # Deprecated in libtorrent 1.1
            # If a single port range then always enable re-use port flag.
            reuse_port = True if listen_ports[0] == listen_ports[1] else self.config["listen_reuse_port"]
            flags = ((lt.listen_on_flags_t.listen_no_system_port
                      if not self.config["listen_use_sys_port"] else 0) |
                     (lt.listen_on_flags_t.listen_reuse_address
                      if reuse_port else 0))
            try:
                self.session.listen_on(listen_ports[0], listen_ports[1], interface, flags)
            except RuntimeError as ex:
                if ex.message == "Invalid Argument":
                    log.error("Error setting listen interface (must be IP Address): %s %s-%s",
                              interface, listen_ports[0], listen_ports[1])

    def _on_set_outgoing_ports(self, key, value):
        self.__set_outgoing_ports()

    def _on_set_random_outgoing_ports(self, key, value):
        self.__set_outgoing_ports()

    def __set_outgoing_ports(self):
        ports = [0, 0] if self.config["random_outgoing_ports"] else self.config["outgoing_ports"]
        log.debug("Outgoing ports set to %s", ports)
        self.session_set_setting("outgoing_ports", (ports[0], ports[1]))

    def _on_set_peer_tos(self, key, value):
        try:
            self.session_set_setting("peer_tos", chr(int(value, 16)))
        except ValueError as ex:
            log.debug("Invalid tos byte: %s", ex)
            return

    def _on_set_dht(self, key, value):
        dht_bootstraps = "router.bittorrent.com:6881,router.utorrent.com:6881,router.bitcomet.com:6881"
        self.session_set_setting("dht_bootstrap_nodes", dht_bootstraps)
        self.session_set_setting("enable_dht", value)

    def _on_set_upnp(self, key, value):
        self.session_set_setting("enable_upnp", value)

    def _on_set_natpmp(self, key, value):
        self.session_set_setting("enable_natpmp", value)

    def _on_set_lsd(self, key, value):
        self.session_set_setting("enable_lsd", value)

    def _on_set_utpex(self, key, value):
        if value:
            self.session.add_extension("ut_pex")

    def _on_set_enc_in_policy(self, key, value):
        self._on_set_encryption(key, value)

    def _on_set_enc_out_policy(self, key, value):
        self._on_set_encryption(key, value)

    def _on_set_enc_level(self, key, value):
        self._on_set_encryption(key, value)

    def _on_set_encryption(self, key, value):
        # Convert Deluge enc_level values to libtorrent enc_level values.
        pe_enc_level = {0: lt.enc_level.plaintext, 1: lt.enc_level.rc4, 2: lt.enc_level.both}
        try:
            self.session.apply_setting("out_enc_policy", lt.enc_policy(self.config["enc_out_policy"]))
            self.session.apply_setting("in_enc_policy", lt.enc_policy(self.config["enc_in_policy"]))
            self.session.apply_setting("allowed_enc_level", lt.enc_level(pe_enc_level[self.config["enc_level"]]))
            self.session.apply_setting("prefer_rc4", True)
        except AttributeError:
            # Deprecated in libtorrent 1.1
            pe_settings = lt.pe_settings()
            pe_settings.out_enc_policy = lt.enc_policy(self.config["enc_out_policy"])
            pe_settings.in_enc_policy = lt.enc_policy(self.config["enc_in_policy"])
            pe_settings.allowed_enc_level = lt.enc_level(pe_enc_level[self.config["enc_level"]])
            pe_settings.prefer_rc4 = True
            self.session.set_pe_settings(pe_settings)
            pe_sess_settings = self.session.get_pe_settings()
            log.debug("encryption settings:\n\t\t\tout_policy: %s\n\t\t\
            in_policy: %s\n\t\t\tlevel: %s\n\t\t\tprefer_rc4: %s",
                      pe_sess_settings.out_enc_policy,
                      pe_sess_settings.in_enc_policy,
                      pe_sess_settings.allowed_enc_level,
                      pe_sess_settings.prefer_rc4)

    def _on_set_max_connections_global(self, key, value):
        self.session_set_setting("connections_limit", value)

    def _on_set_max_upload_speed(self, key, value):
        # We need to convert Kb/s to B/s
        value = -1 if value < 0 else int(value * 1024)
        self.session_set_setting("upload_rate_limit", value)

    def _on_set_max_download_speed(self, key, value):
        # We need to convert Kb/s to B/s
        value = -1 if value < 0 else int(value * 1024)
        self.session_set_setting("download_rate_limit", value)

    def _on_set_max_upload_slots_global(self, key, value):
        self.session_set_setting("unchoke_slots_limit", value)

    def _on_set_max_half_open_connections(self, key, value):
        self.session_set_setting("half_open_limit", value)

    def _on_set_max_connections_per_second(self, key, value):
        self.session_set_setting("connection_speed", value)

    def _on_set_ignore_limits_on_local_network(self, key, value):
        self.session_set_setting("ignore_limits_on_local_network", value)

    def _on_set_share_ratio_limit(self, key, value):
        self.session_set_setting("share_ratio_limit", value)

    def _on_set_seed_time_ratio_limit(self, key, value):
        self.session_set_setting("seed_time_ratio_limit", value)

    def _on_set_seed_time_limit(self, key, value):
        # This value is stored in minutes in deluge, but libtorrent wants seconds
        self.session_set_setting("seed_time_limit", int(value * 60))

    def _on_set_max_active_downloading(self, key, value):
        self.session_set_setting("active_downloads", value)

    def _on_set_max_active_seeding(self, key, value):
        self.session_set_setting("active_seeds", value)

    def _on_set_max_active_limit(self, key, value):
        self.session_set_setting("active_limit", value)

    def _on_set_dont_count_slow_torrents(self, key, value):
        self.session_set_setting("dont_count_slow_torrents", value)

    def _on_set_send_info(self, key, value):
        """sends anonymous stats home"""
        log.debug("Sending anonymous stats..")

        class SendInfoThread(threading.Thread):
            def __init__(self, config):
                self.config = config
                threading.Thread.__init__(self)

            def run(self):
                import time
                now = time.time()
                # check if we've done this within the last week or never
                if (now - self.config["info_sent"]) >= (60 * 60 * 24 * 7):
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
                    except IOError as ex:
                        log.debug("Network error while trying to send info: %s", ex)
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
        try:
            if key == "i2p_proxy":
                self.session.apply_settings("proxy_type", lt.proxy_type("i2p_proxy"))
                self.session.apply_settings("i2p_hostname", value["hostname"])
                self.session.apply_settings("i2p_port", value["port"])
            else:
                self.session.apply_settings("proxy_type", lt.proxy_type(value["type"]))
                self.session.apply_settings("proxy_hostname", value["hostname"])
                self.session.apply_settings("proxy_port", value["port"])
                self.session.apply_settings("proxy_username", value["username"])
                self.session.apply_settings("proxy_password", value["password"])
                self.session.apply_settings("proxy_hostnames", value["proxy_hostnames"])
                self.session.apply_settings("proxy_peer_connections", value["proxy_peer_connections"])
                self.session.apply_settings("proxy_tracker_connections", value["proxy_tracker_connections"])
        except AttributeError:
            proxy_settings = lt.proxy_settings()
            proxy_settings.hostname = value["hostname"]
            proxy_settings.port = value["port"]
            if key == "i2p_proxy":
                try:
                    self.session.set_i2p_proxy(proxy_settings)
                except RuntimeError as ex:
                    log.error("Unable to set I2P Proxy: %s", ex)
            else:
                proxy_settings.type = lt.proxy_type(value["type"])
                proxy_settings.username = value["username"]
                proxy_settings.password = value["password"]
                proxy_settings.hostname = value["hostname"]
                proxy_settings.port = value["port"]
                proxy_settings.proxy_hostnames = value["proxy_hostnames"]
                proxy_settings.proxy_peer_connections = value["proxy_peer_connections"]
                self.session.set_proxy(proxy_settings)

    def _on_set_i2p_proxy(self, key, value):
        self._on_set_proxy(key, value)

    def _on_set_rate_limit_ip_overhead(self, key, value):
        self.session_set_setting("rate_limit_ip_overhead", value)

    def _on_set_anonymous_mode(self, key, value):
        self.session_set_setting("anonymous_mode", value)

    def _on_set_geoip_db_location(self, key, geoipdb_path):
        # Load the GeoIP DB for country look-ups if available
        if os.path.exists(geoipdb_path):
            try:
                self.core.geoip_instance = GeoIP.open(geoipdb_path, GeoIP.GEOIP_STANDARD)
            except AttributeError:
                log.warning("GeoIP Unavailable")
        else:
            log.warning("Unable to find GeoIP database file: %s", geoipdb_path)

    def _on_set_cache_size(self, key, value):
        self.session_set_setting("cache_size", value)

    def _on_set_cache_expiry(self, key, value):
        self.session_set_setting("cache_expiry", value)

    def _on_auto_manage_prefer_seeds(self, key, value):
        self.session_set_setting("auto_manage_prefer_seeds", value)
