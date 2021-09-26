# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging

from deluge.common import is_ip
from deluge.decorators import overrides
from deluge.i18n import get_languages
from deluge.ui.client import client
from deluge.ui.common import DISK_CACHE_KEYS
from deluge.ui.console.widgets import BaseInputPane, BaseWindow
from deluge.ui.console.widgets.fields import FloatSpinInput, TextInput
from deluge.ui.console.widgets.popup import PopupsHandler

log = logging.getLogger(__name__)


class BasePreferencePane(BaseInputPane, BaseWindow, PopupsHandler):
    def __init__(self, name, preferences):
        PopupsHandler.__init__(self)
        self.preferences = preferences
        BaseWindow.__init__(
            self,
            '%s' % name,
            self.pane_width,
            preferences.height,
            posy=1,
            posx=self.pane_x_pos,
        )
        BaseInputPane.__init__(self, preferences, border_off_east=1)
        self.name = name

        # have we scrolled down in the list
        self.input_offset = 0

    @overrides(BaseInputPane)
    def handle_read(self, c):
        if self.popup:
            ret = self.popup.handle_read(c)
            if self.popup and self.popup.closed():
                self.pop_popup()
            self.refresh()
            return ret
        return BaseInputPane.handle_read(self, c)

    @property
    def visible_content_pane_height(self):
        y, x = self.visible_content_pane_size
        return y

    @property
    def pane_x_pos(self):
        return self.preferences.sidebar_width

    @property
    def pane_width(self):
        return self.preferences.width

    @property
    def cols(self):
        return self.pane_width

    @property
    def rows(self):
        return self.preferences.height

    def is_active_pane(self):
        return self.preferences.is_active_pane(self)

    def create_pane(self, core_conf, console_config):
        pass

    def add_config_values(self, conf_dict):
        for ipt in self.inputs:
            if ipt.has_input():
                # Need special cases for in/out ports or proxy since they are tuples or dicts.
                if ipt.name == 'listen_ports_to' or ipt.name == 'listen_ports_from':
                    conf_dict['listen_ports'] = (
                        self.infrom.get_value(),
                        self.into.get_value(),
                    )
                elif ipt.name == 'out_ports_to' or ipt.name == 'out_ports_from':
                    conf_dict['outgoing_ports'] = (
                        self.outfrom.get_value(),
                        self.outto.get_value(),
                    )
                elif ipt.name == 'listen_interface':
                    listen_interface = ipt.get_value().strip()
                    if is_ip(listen_interface) or not listen_interface:
                        conf_dict['listen_interface'] = listen_interface
                elif ipt.name == 'outgoing_interface':
                    outgoing_interface = ipt.get_value().strip()
                    conf_dict['outgoing_interface'] = outgoing_interface
                elif ipt.name.startswith('proxy_'):
                    if ipt.name == 'proxy_type':
                        conf_dict.setdefault('proxy', {})['type'] = ipt.get_value()
                    elif ipt.name == 'proxy_username':
                        conf_dict.setdefault('proxy', {})['username'] = ipt.get_value()
                    elif ipt.name == 'proxy_password':
                        conf_dict.setdefault('proxy', {})['password'] = ipt.get_value()
                    elif ipt.name == 'proxy_hostname':
                        conf_dict.setdefault('proxy', {})['hostname'] = ipt.get_value()
                    elif ipt.name == 'proxy_port':
                        conf_dict.setdefault('proxy', {})['port'] = ipt.get_value()
                    elif ipt.name == 'proxy_hostnames':
                        conf_dict.setdefault('proxy', {})[
                            'proxy_hostnames'
                        ] = ipt.get_value()
                    elif ipt.name == 'proxy_peer_connections':
                        conf_dict.setdefault('proxy', {})[
                            'proxy_peer_connections'
                        ] = ipt.get_value()
                    elif ipt.name == 'proxy_tracker_connections':
                        conf_dict.setdefault('proxy', {})[
                            'proxy_tracker_connections'
                        ] = ipt.get_value()
                elif ipt.name == 'force_proxy':
                    conf_dict.setdefault('proxy', {})['force_proxy'] = ipt.get_value()
                elif ipt.name == 'anonymous_mode':
                    conf_dict.setdefault('proxy', {})[
                        'anonymous_mode'
                    ] = ipt.get_value()
                else:
                    conf_dict[ipt.name] = ipt.get_value()

                if hasattr(ipt, 'get_child'):
                    c = ipt.get_child()
                    conf_dict[c.name] = c.get_value()

    def update_values(self, conf_dict):
        for ipt in self.inputs:
            if ipt.has_input():
                try:
                    ipt.set_value(conf_dict[ipt.name])
                except KeyError:  # just ignore if it's not in dict
                    pass
                if hasattr(ipt, 'get_child'):
                    try:
                        c = ipt.get_child()
                        c.set_value(conf_dict[c.name])
                    except KeyError:  # just ignore if it's not in dict
                        pass

    def render(self, mode, screen, width, focused):
        height = self.get_content_height()
        self.ensure_content_pane_height(height)
        self.screen.erase()

        if focused and self.active_input == -1:
            self.move_active_down(1)

        self.render_inputs(focused=focused)

    @overrides(BaseWindow)
    def refresh(self):
        BaseWindow.refresh(self)
        if self.popup:
            self.popup.refresh()

    def update(self, active):
        pass


class InterfacePane(BasePreferencePane):
    def __init__(self, preferences):
        BasePreferencePane.__init__(self, ' %s ' % _('Interface'), preferences)

    @overrides(BasePreferencePane)
    def create_pane(self, core_conf, console_config):
        self.add_header(_('General options'))

        self.add_checked_input(
            'ring_bell',
            _('Ring system bell when a download finishes'),
            console_config['ring_bell'],
        )
        self.add_header('Console UI', space_above=True)
        self.add_checked_input(
            'separate_complete',
            _('List complete torrents after incomplete regardless of sorting order'),
            console_config['torrentview']['separate_complete'],
        )
        self.add_checked_input(
            'move_selection',
            _('Move selection when moving torrents in the queue'),
            console_config['torrentview']['move_selection'],
        )

        langs = get_languages()
        langs.insert(0, ('', 'System Default'))
        self.add_combo_input(
            'language', _('Language'), langs, default=console_config['language']
        )
        self.add_header(_('Command Line Mode'), space_above=True)
        self.add_checked_input(
            'ignore_duplicate_lines',
            _('Do not store duplicate input in history'),
            console_config['cmdline']['ignore_duplicate_lines'],
        )
        self.add_checked_input(
            'save_command_history',
            _('Store and load command line history in command line mode'),
            console_config['cmdline']['save_command_history'],
        )
        self.add_header('')
        self.add_checked_input(
            'third_tab_lists_all',
            _('Third tab lists all remaining torrents in command line mode'),
            console_config['cmdline']['third_tab_lists_all'],
        )
        self.add_int_spin_input(
            'torrents_per_tab_press',
            _('Torrents per tab press'),
            console_config['cmdline']['torrents_per_tab_press'],
            min_val=5,
            max_val=10000,
        )


class DownloadsPane(BasePreferencePane):
    def __init__(self, preferences):
        BasePreferencePane.__init__(self, ' %s ' % _('Downloads'), preferences)

    @overrides(BasePreferencePane)
    def create_pane(self, core_conf, console_config):
        self.add_header(_('Folders'))
        self.add_text_input(
            'download_location',
            '%s:' % _('Download To'),
            core_conf['download_location'],
            complete=True,
            activate_input=True,
            col='+1',
        )
        cmptxt = TextInput(
            self.preferences,
            'move_completed_path',
            None,
            self.move,
            self.pane_width,
            core_conf['move_completed_path'],
            False,
        )
        self.add_checkedplus_input(
            'move_completed',
            '%s:' % _('Move completed to'),
            cmptxt,
            core_conf['move_completed'],
        )
        copytxt = TextInput(
            self.preferences,
            'torrentfiles_location',
            None,
            self.move,
            self.pane_width,
            core_conf['torrentfiles_location'],
            False,
        )
        self.add_checkedplus_input(
            'copy_torrent_file',
            '%s:' % _('Copy of .torrent files to'),
            copytxt,
            core_conf['copy_torrent_file'],
        )
        self.add_checked_input(
            'del_copy_torrent_file',
            _('Delete copy of torrent file on remove'),
            core_conf['del_copy_torrent_file'],
        )

        self.add_header(_('Options'), space_above=True)
        self.add_checked_input(
            'prioritize_first_last_pieces',
            ('Prioritize first and last pieces of torrent'),
            core_conf['prioritize_first_last_pieces'],
        )
        self.add_checked_input(
            'sequential_download',
            _('Sequential download'),
            core_conf['sequential_download'],
        )
        self.add_checked_input('add_paused', _('Add Paused'), core_conf['add_paused'])
        self.add_checked_input(
            'pre_allocate_storage',
            _('Pre-Allocate disk space'),
            core_conf['pre_allocate_storage'],
        )


class NetworkPane(BasePreferencePane):
    def __init__(self, preferences):
        BasePreferencePane.__init__(self, ' %s ' % _('Network'), preferences)

    @overrides(BasePreferencePane)
    def create_pane(self, core_conf, console_config):
        self.add_header(_('Incomming Ports'))
        inrand = self.add_checked_input(
            'random_port',
            'Use Random Ports    Active Port: %d' % self.preferences.active_port,
            core_conf['random_port'],
        )
        listen_ports = core_conf['listen_ports']
        self.infrom = self.add_int_spin_input(
            'listen_ports_from',
            '    %s:' % _('From'),
            value=listen_ports[0],
            min_val=0,
            max_val=65535,
        )
        self.infrom.set_depend(inrand, inverse=True)
        self.into = self.add_int_spin_input(
            'listen_ports_to',
            '    %s:' % _('To'),
            value=listen_ports[1],
            min_val=0,
            max_val=65535,
        )
        self.into.set_depend(inrand, inverse=True)

        self.add_header(_('Outgoing Ports'), space_above=True)
        outrand = self.add_checked_input(
            'random_outgoing_ports',
            _('Use Random Ports'),
            core_conf['random_outgoing_ports'],
        )
        out_ports = core_conf['outgoing_ports']
        self.outfrom = self.add_int_spin_input(
            'out_ports_from',
            '    %s:' % _('From'),
            value=out_ports[0],
            min_val=0,
            max_val=65535,
        )
        self.outfrom.set_depend(outrand, inverse=True)
        self.outto = self.add_int_spin_input(
            'out_ports_to',
            '    %s:' % _('To'),
            value=out_ports[1],
            min_val=0,
            max_val=65535,
        )
        self.outto.set_depend(outrand, inverse=True)

        self.add_header(_('Incoming Interface'), space_above=True)
        self.add_text_input(
            'listen_interface',
            _('IP address of the interface to listen on (leave empty for default):'),
            core_conf['listen_interface'],
        )

        self.add_header(_('Outgoing Interface'), space_above=True)
        self.add_text_input(
            'outgoing_interface',
            _(
                'The network interface name or IP address for outgoing '
                'BitTorrent connections. (Leave empty for default.):'
            ),
            core_conf['outgoing_interface'],
        )

        self.add_header('TOS', space_above=True)
        self.add_text_input('peer_tos', 'Peer TOS Byte:', core_conf['peer_tos'])

        self.add_header(_('Network Extras'), space_above=True)
        self.add_checked_input('upnp', 'UPnP', core_conf['upnp'])
        self.add_checked_input('natpmp', 'NAT-PMP', core_conf['natpmp'])
        self.add_checked_input('utpex', 'Peer Exchange', core_conf['utpex'])
        self.add_checked_input('lsd', 'LSD', core_conf['lsd'])
        self.add_checked_input('dht', 'DHT', core_conf['dht'])

        self.add_header(_('Encryption'), space_above=True)
        self.add_select_input(
            'enc_in_policy',
            '%s:' % _('Inbound'),
            [_('Forced'), _('Enabled'), _('Disabled')],
            [0, 1, 2],
            core_conf['enc_in_policy'],
            active_default=True,
            col='+1',
        )
        self.add_select_input(
            'enc_out_policy',
            '%s:' % _('Outbound'),
            [_('Forced'), _('Enabled'), _('Disabled')],
            [0, 1, 2],
            core_conf['enc_out_policy'],
            active_default=True,
        )
        self.add_select_input(
            'enc_level',
            '%s:' % _('Level'),
            [_('Handshake'), _('Full Stream'), _('Either')],
            [0, 1, 2],
            core_conf['enc_level'],
            active_default=True,
        )


class BandwidthPane(BasePreferencePane):
    def __init__(self, preferences):
        BasePreferencePane.__init__(self, ' %s ' % _('Bandwidth'), preferences)

    @overrides(BasePreferencePane)
    def create_pane(self, core_conf, console_config):
        self.add_header(_('Global Bandwidth Usage'))
        self.add_int_spin_input(
            'max_connections_global',
            '%s:' % _('Maximum Connections'),
            core_conf['max_connections_global'],
            min_val=-1,
            max_val=9000,
        )
        self.add_int_spin_input(
            'max_upload_slots_global',
            '%s:' % _('Maximum Upload Slots'),
            core_conf['max_upload_slots_global'],
            min_val=-1,
            max_val=9000,
        )
        self.add_float_spin_input(
            'max_download_speed',
            '%s:' % _('Maximum Download Speed (KiB/s)'),
            core_conf['max_download_speed'],
            min_val=-1.0,
            max_val=60000.0,
        )
        self.add_float_spin_input(
            'max_upload_speed',
            '%s:' % _('Maximum Upload Speed (KiB/s)'),
            core_conf['max_upload_speed'],
            min_val=-1.0,
            max_val=60000.0,
        )
        self.add_int_spin_input(
            'max_half_open_connections',
            '%s:' % _('Maximum Half-Open Connections'),
            core_conf['max_half_open_connections'],
            min_val=-1,
            max_val=9999,
        )
        self.add_int_spin_input(
            'max_connections_per_second',
            '%s:' % _('Maximum Connection Attempts per Second'),
            core_conf['max_connections_per_second'],
            min_val=-1,
            max_val=9999,
        )
        self.add_checked_input(
            'ignore_limits_on_local_network',
            _('Ignore limits on local network'),
            core_conf['ignore_limits_on_local_network'],
        )
        self.add_checked_input(
            'rate_limit_ip_overhead',
            _('Rate Limit IP Overhead'),
            core_conf['rate_limit_ip_overhead'],
        )
        self.add_header(_('Per Torrent Bandwidth Usage'), space_above=True)
        self.add_int_spin_input(
            'max_connections_per_torrent',
            '%s:' % _('Maximum Connections'),
            core_conf['max_connections_per_torrent'],
            min_val=-1,
            max_val=9000,
        )
        self.add_int_spin_input(
            'max_upload_slots_per_torrent',
            '%s:' % _('Maximum Upload Slots'),
            core_conf['max_upload_slots_per_torrent'],
            min_val=-1,
            max_val=9000,
        )
        self.add_float_spin_input(
            'max_download_speed_per_torrent',
            '%s:' % _('Maximum Download Speed (KiB/s)'),
            core_conf['max_download_speed_per_torrent'],
            min_val=-1.0,
            max_val=60000.0,
        )
        self.add_float_spin_input(
            'max_upload_speed_per_torrent',
            '%s:' % _('Maximum Upload Speed (KiB/s)'),
            core_conf['max_upload_speed_per_torrent'],
            min_val=-1.0,
            max_val=60000.0,
        )


class OtherPane(BasePreferencePane):
    def __init__(self, preferences):
        BasePreferencePane.__init__(self, ' %s ' % _('Other'), preferences)

    @overrides(BasePreferencePane)
    def create_pane(self, core_conf, console_config):
        self.add_header(_('System Information'))
        self.add_info_field('info1', ' Help us improve Deluge by sending us your', '')
        self.add_info_field(
            'info2', ' Python version, PyGTK version, OS and processor', ''
        )
        self.add_info_field(
            'info3', ' types.  Absolutely no other information is sent.', ''
        )
        self.add_checked_input(
            'send_info',
            _('Yes, please send anonymous statistics.'),
            core_conf['send_info'],
        )
        self.add_header(_('GeoIP Database'), space_above=True)
        self.add_text_input(
            'geoip_db_location', 'Location:', core_conf['geoip_db_location']
        )


class DaemonPane(BasePreferencePane):
    def __init__(self, preferences):
        BasePreferencePane.__init__(self, ' %s ' % _('Daemon'), preferences)

    @overrides(BasePreferencePane)
    def create_pane(self, core_conf, console_config):
        self.add_header('Port')
        self.add_int_spin_input(
            'daemon_port',
            '%s:' % _('Daemon Port'),
            core_conf['daemon_port'],
            min_val=0,
            max_val=65535,
        )
        self.add_header('Connections', space_above=True)
        self.add_checked_input(
            'allow_remote', _('Allow remote connections'), core_conf['allow_remote']
        )
        self.add_header('Other', space_above=True)
        self.add_checked_input(
            'new_release_check',
            _('Periodically check the website for new releases'),
            core_conf['new_release_check'],
        )


class QueuePane(BasePreferencePane):
    def __init__(self, preferences):
        BasePreferencePane.__init__(self, ' %s ' % _('Queue'), preferences)

    @overrides(BasePreferencePane)
    def create_pane(self, core_conf, console_config):
        self.add_header(_('New Torrents'))
        self.add_checked_input(
            'queue_new_to_top', _('Queue to top'), core_conf['queue_new_to_top']
        )
        self.add_header(_('Active Torrents'), True)
        self.add_int_spin_input(
            'max_active_limit',
            '%s:' % _('Total'),
            core_conf['max_active_limit'],
            min_val=-1,
            max_val=9999,
        )
        self.add_int_spin_input(
            'max_active_downloading',
            '%s:' % _('Downloading'),
            core_conf['max_active_downloading'],
            min_val=-1,
            max_val=9999,
        )
        self.add_int_spin_input(
            'max_active_seeding',
            '%s:' % _('Seeding'),
            core_conf['max_active_seeding'],
            min_val=-1,
            max_val=9999,
        )
        self.add_checked_input(
            'dont_count_slow_torrents',
            'Ignore slow torrents',
            core_conf['dont_count_slow_torrents'],
        )
        self.add_checked_input(
            'auto_manage_prefer_seeds',
            'Prefer seeding torrents',
            core_conf['auto_manage_prefer_seeds'],
        )
        self.add_header(_('Seeding Rotation'), space_above=True)
        self.add_float_spin_input(
            'share_ratio_limit',
            '%s:' % _('Share Ratio'),
            core_conf['share_ratio_limit'],
            precision=2,
            min_val=-1.0,
            max_val=100.0,
        )
        self.add_float_spin_input(
            'seed_time_ratio_limit',
            '%s:' % _('Time Ratio'),
            core_conf['seed_time_ratio_limit'],
            precision=2,
            min_val=-1.0,
            max_val=100.0,
        )
        self.add_int_spin_input(
            'seed_time_limit',
            '%s:' % _('Time (m)'),
            core_conf['seed_time_limit'],
            min_val=1,
            max_val=10000,
        )
        seedratio = FloatSpinInput(
            self.mode,
            'stop_seed_ratio',
            '',
            self.move,
            core_conf['stop_seed_ratio'],
            precision=2,
            inc_amt=0.1,
            min_val=0.5,
            max_val=100.0,
        )
        self.add_checkedplus_input(
            'stop_seed_at_ratio',
            '%s:' % _('Share Ratio Reached'),
            seedratio,
            core_conf['stop_seed_at_ratio'],
        )
        self.add_checked_input(
            'remove_seed_at_ratio',
            _('Remove torrent (Unchecked pauses torrent)'),
            core_conf['remove_seed_at_ratio'],
        )


class ProxyPane(BasePreferencePane):
    def __init__(self, preferences):
        BasePreferencePane.__init__(self, ' %s ' % _('Proxy'), preferences)

    @overrides(BasePreferencePane)
    def create_pane(self, core_conf, console_config):
        proxy = core_conf['proxy']

        self.add_header(_('Proxy Settings'))
        self.add_header(_('Proxy'), space_above=True)
        self.add_int_spin_input(
            'proxy_type', '%s:' % _('Type'), proxy['type'], min_val=0, max_val=5
        )
        self.add_text_input('proxy_username', '%s:' % _('Username'), proxy['username'])
        self.add_text_input('proxy_password', '%s:' % _('Password'), proxy['password'])
        self.add_text_input('proxy_hostname', '%s:' % _('Hostname'), proxy['hostname'])
        self.add_int_spin_input(
            'proxy_port', '%s:' % _('Port'), proxy['port'], min_val=0, max_val=65535
        )
        self.add_checked_input(
            'proxy_hostnames', _('Proxy Hostnames'), proxy['proxy_hostnames']
        )
        self.add_checked_input(
            'proxy_peer_connections', _('Proxy Peers'), proxy['proxy_peer_connections']
        )
        self.add_checked_input(
            'proxy_tracker_connections',
            _('Proxy Trackers'),
            proxy['proxy_tracker_connections'],
        )
        self.add_header('%s' % _('Force Proxy'), space_above=True)
        self.add_checked_input('force_proxy', _('Force Proxy'), proxy['force_proxy'])
        self.add_checked_input(
            'anonymous_mode', _('Hide Client Identity'), proxy['anonymous_mode']
        )
        self.add_header('%s' % _('Proxy Type Help'), space_above=True)
        self.add_text_area(
            'proxy_text_area',
            ' 0: None   1: Socks4\n'
            ' 2: Socks5 3: Socks5 Auth\n'
            ' 4: HTTP   5: HTTP Auth\n'
            ' 6: I2P',
        )


class CachePane(BasePreferencePane):
    def __init__(self, preferences):
        BasePreferencePane.__init__(self, ' %s ' % _('Cache'), preferences)
        self.created = False

    @overrides(BasePreferencePane)
    def create_pane(self, core_conf, console_config):
        self.core_conf = core_conf

    def build_pane(self, core_conf, status):
        self.created = True
        self.add_header(_('Settings'), space_below=True)
        self.add_int_spin_input(
            'cache_size',
            '%s:' % _('Cache Size (16 KiB blocks)'),
            core_conf['cache_size'],
            min_val=0,
            max_val=99999,
        )
        self.add_int_spin_input(
            'cache_expiry',
            '%s:' % _('Cache Expiry (seconds)'),
            core_conf['cache_expiry'],
            min_val=1,
            max_val=32000,
        )
        self.add_header(' %s' % _('Write'), space_above=True)
        self.add_info_field(
            'blocks_written',
            '  %s:' % _('Blocks Written'),
            status['disk.num_blocks_written'],
        )
        self.add_info_field(
            'writes', '  %s:' % _('Writes'), status['disk.num_write_ops']
        )
        self.add_info_field(
            'write_hit_ratio',
            '  %s:' % _('Write Cache Hit Ratio'),
            '%.2f' % status['write_hit_ratio'],
        )
        self.add_header(' %s' % _('Read'))
        self.add_info_field(
            'blocks_read', '  %s:' % _('Blocks Read'), status['disk.num_blocks_read']
        )
        self.add_info_field('reads', '  %s:' % _('Reads'), status['disk.num_read_ops'])
        self.add_info_field(
            'read_hit_ratio',
            '  %s:' % _('Read Cache Hit Ratio'),
            '%.2f' % status['read_hit_ratio'],
        )
        self.add_header(' %s' % _('Size'))
        self.add_info_field(
            'cache_size_info',
            '  %s:' % _('Cache Size'),
            status['disk.disk_blocks_in_use'],
        )
        self.add_info_field(
            'read_cache_size',
            '  %s:' % _('Read Cache Size'),
            status['disk.read_cache_blocks'],
        )

    @overrides(BasePreferencePane)
    def update(self, active):
        if active:
            client.core.get_session_status(DISK_CACHE_KEYS).addCallback(
                self.update_cache_status_fields
            )

    def update_cache_status_fields(self, status):
        if not self.created:
            self.build_pane(self.core_conf, status)
        else:
            for ipt in self.inputs:
                if not ipt.has_input() and ipt.name in status:
                    ipt.set_value(status[ipt.name])
        self.preferences.refresh()
