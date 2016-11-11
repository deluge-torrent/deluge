# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, 2008 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2011 Pedro Algarvio <pedro@algarvio.me>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#


from __future__ import unicode_literals

import logging
import os.path

from gi.repository import Gtk

import deluge.common
import deluge.component as component
from deluge.configmanager import ConfigManager
from deluge.ui.client import client
from deluge.ui.gtkui.dialogs import ErrorDialog, OtherDialog
from deluge.ui.gtkui.path_chooser import PathChooser

log = logging.getLogger(__name__)


class MenuBar(component.Component):

    def __init__(self):
        log.debug('MenuBar init..')
        component.Component.__init__(self, 'MenuBar')
        self.mainwindow = component.get('MainWindow')
        self.main_builder = self.mainwindow.get_builder()
        self.config = ConfigManager('gtkui.conf')

        self.builder = Gtk.Builder()
        # Get the torrent menu from the gtk builder file
        self.builder.add_from_file(deluge.common.resource_filename(
            'deluge.ui.gtkui', os.path.join('glade', 'torrent_menu.ui'),
        ))
        # Get the torrent options menu from the gtk builder file
        self.builder.add_from_file(deluge.common.resource_filename(
            'deluge.ui.gtkui', os.path.join('glade', 'torrent_menu.options.ui'),
        ))
        # Get the torrent queue menu from the gtk builder file
        self.builder.add_from_file(deluge.common.resource_filename(
            'deluge.ui.gtkui', os.path.join('glade', 'torrent_menu.queue.ui'),
        ))

        # Attach queue torrent menu
        torrent_queue_menu = self.builder.get_object('queue_torrent_menu')
        self.builder.get_object('menuitem_queue').set_submenu(torrent_queue_menu)
        # Attach options torrent menu
        torrent_options_menu = self.builder.get_object('options_torrent_menu')
        self.builder.get_object('menuitem_options').set_submenu(torrent_options_menu)

        self.builder.get_object('download-limit-image').set_from_file(deluge.common.get_pixmap('downloading16.png'))
        self.builder.get_object('upload-limit-image').set_from_file(deluge.common.get_pixmap('seeding16.png'))

        for menuitem in (
            'menuitem_down_speed', 'menuitem_up_speed',
            'menuitem_max_connections', 'menuitem_upload_slots',
        ):
            submenu = Gtk.Menu()
            item = Gtk.MenuItem(_('Set Unlimited'))
            item.set_name(menuitem)
            item.connect('activate', self.on_menuitem_set_unlimited)
            submenu.append(item)
            item = Gtk.MenuItem(_('Other...'))
            item.set_name(menuitem)
            item.connect('activate', self.on_menuitem_set_other)
            submenu.append(item)
            submenu.show_all()
            self.builder.get_object(menuitem).set_submenu(submenu)

        submenu = Gtk.Menu()
        item = Gtk.MenuItem(_('On'))
        item.connect('activate', self.on_menuitem_set_automanaged_on)
        submenu.append(item)
        item = Gtk.MenuItem(_('Off'))
        item.connect('activate', self.on_menuitem_set_automanaged_off)
        submenu.append(item)
        submenu.show_all()
        self.builder.get_object('menuitem_auto_managed').set_submenu(submenu)

        submenu = Gtk.Menu()
        item = Gtk.MenuItem(_('Disable'))
        item.connect('activate', self.on_menuitem_set_stop_seed_at_ratio_disable)
        submenu.append(item)
        item = Gtk.MenuItem(_('Enable...'))
        item.set_name('menuitem_stop_seed_at_ratio')
        item.connect('activate', self.on_menuitem_set_other)
        submenu.append(item)
        submenu.show_all()
        self.builder.get_object('menuitem_stop_seed_at_ratio').set_submenu(submenu)

        self.torrentmenu = self.builder.get_object('torrent_menu')
        self.menu_torrent = self.main_builder.get_object('menu_torrent')

        # Attach the torrent_menu to the Torrent file menu
        self.menu_torrent.set_submenu(self.torrentmenu)

        # Make sure the view menuitems are showing the correct active state
        self.main_builder.get_object('menuitem_toolbar').set_active(self.config['show_toolbar'])
        self.main_builder.get_object('menuitem_sidebar').set_active(self.config['show_sidebar'])
        self.main_builder.get_object('menuitem_statusbar').set_active(self.config['show_statusbar'])
        self.main_builder.get_object('sidebar_show_zero').set_active(self.config['sidebar_show_zero'])
        self.main_builder.get_object('sidebar_show_trackers').set_active(self.config['sidebar_show_trackers'])
        self.main_builder.get_object('sidebar_show_owners').set_active(self.config['sidebar_show_owners'])

        # Connect main window Signals #
        self.mainwindow.connect_signals(self)

        # Connect menubar signals
        self.builder.connect_signals(self)

        self.change_sensitivity = [
            'menuitem_addtorrent',
        ]

    def start(self):
        for widget in self.change_sensitivity:
            self.main_builder.get_object(widget).set_sensitive(True)

        # Only show open_folder menuitem and separator if connected to a localhost daemon.
        localhost_items = [
            'menuitem_open_folder',
            'separator4',
        ]
        if client.is_localhost():
            for widget in localhost_items:
                self.builder.get_object(widget).show()
                self.builder.get_object(widget).set_no_show_all(False)
        else:
            for widget in localhost_items:
                self.builder.get_object(widget).hide()
                self.builder.get_object(widget).set_no_show_all(True)

        self.main_builder.get_object('separatormenuitem').set_visible(not self.config['standalone'])
        self.main_builder.get_object('menuitem_quitdaemon').set_visible(not self.config['standalone'])
        self.main_builder.get_object('menuitem_connectionmanager').set_visible(not self.config['standalone'])

        # Show the Torrent menu because we're connected to a host
        self.menu_torrent.show()

        if client.get_auth_level() == deluge.common.AUTH_LEVEL_ADMIN:
            # Get known accounts to allow changing ownership
            client.core.get_known_accounts().addCallback(
                self._on_known_accounts,
            ).addErrback(self._on_known_accounts_fail)

        client.register_event_handler('TorrentStateChangedEvent', self.on_torrentstatechanged_event)
        client.register_event_handler('TorrentResumedEvent', self.on_torrentresumed_event)
        client.register_event_handler('SessionPausedEvent', self.on_sessionpaused_event)
        client.register_event_handler('SessionResumedEvent', self.on_sessionresumed_event)

    def stop(self):
        log.debug('MenuBar stopping')

        client.deregister_event_handler('TorrentStateChangedEvent', self.on_torrentstatechanged_event)
        client.deregister_event_handler('TorrentResumedEvent', self.on_torrentresumed_event)
        client.deregister_event_handler('SessionPausedEvent', self.on_sessionpaused_event)
        client.deregister_event_handler('SessionResumedEvent', self.on_sessionresumed_event)

        for widget in self.change_sensitivity:
            self.main_builder.get_object(widget).set_sensitive(False)

        # Hide the Torrent menu
        self.menu_torrent.hide()

        self.main_builder.get_object('separatormenuitem').hide()
        self.main_builder.get_object('menuitem_quitdaemon').hide()

    def update_menu(self):
        selected = component.get('TorrentView').get_selected_torrents()
        if not selected or len(selected) == 0:
            # No torrent is selected. Disable the 'Torrents' menu
            self.menu_torrent.set_sensitive(False)
            return

        self.menu_torrent.set_sensitive(True)
        # XXX: Should also update Pause/Resume/Remove menuitems.
        # Any better way than duplicating toolbar.py:update_buttons in here?

    def add_torrentmenu_separator(self):
        sep = Gtk.SeparatorMenuItem()
        self.torrentmenu.append(sep)
        sep.show()
        return sep

    # Callbacks #
    def on_torrentstatechanged_event(self, torrent_id, state):
        if state == 'Paused':
            self.update_menu()

    def on_torrentresumed_event(self, torrent_id):
        self.update_menu()

    def on_sessionpaused_event(self):
        self.update_menu()

    def on_sessionresumed_event(self):
        self.update_menu()

    # File Menu #
    def on_menuitem_addtorrent_activate(self, data=None):
        log.debug('on_menuitem_addtorrent_activate')
        component.get('AddTorrentDialog').show()

    def on_menuitem_createtorrent_activate(self, data=None):
        log.debug('on_menuitem_createtorrent_activate')
        from deluge.ui.gtkui.createtorrentdialog import CreateTorrentDialog
        CreateTorrentDialog().show()

    def on_menuitem_quitdaemon_activate(self, data=None):
        log.debug('on_menuitem_quitdaemon_activate')
        self.mainwindow.quit(shutdown=True)

    def on_menuitem_quit_activate(self, data=None):
        log.debug('on_menuitem_quit_activate')
        self.mainwindow.quit()

    # Edit Menu #
    def on_menuitem_preferences_activate(self, data=None):
        log.debug('on_menuitem_preferences_activate')
        component.get('Preferences').show()

    def on_menuitem_connectionmanager_activate(self, data=None):
        log.debug('on_menuitem_connectionmanager_activate')
        component.get('ConnectionManager').show()

    # Torrent Menu #
    def on_menuitem_pause_activate(self, data=None):
        log.debug('on_menuitem_pause_activate')
        client.core.pause_torrent(
            component.get('TorrentView').get_selected_torrents(),
        )

    def on_menuitem_resume_activate(self, data=None):
        log.debug('on_menuitem_resume_activate')
        client.core.resume_torrent(
            component.get('TorrentView').get_selected_torrents(),
        )

    def on_menuitem_updatetracker_activate(self, data=None):
        log.debug('on_menuitem_updatetracker_activate')
        client.core.force_reannounce(
            component.get('TorrentView').get_selected_torrents(),
        )

    def on_menuitem_edittrackers_activate(self, data=None):
        log.debug('on_menuitem_edittrackers_activate')
        from deluge.ui.gtkui.edittrackersdialog import EditTrackersDialog
        dialog = EditTrackersDialog(
            component.get('TorrentView').get_selected_torrent(),
            self.mainwindow.window,
        )
        dialog.run()

    def on_menuitem_remove_activate(self, data=None):
        log.debug('on_menuitem_remove_activate')
        torrent_ids = component.get('TorrentView').get_selected_torrents()
        if torrent_ids:
            from deluge.ui.gtkui.removetorrentdialog import RemoveTorrentDialog
            RemoveTorrentDialog(torrent_ids).run()

    def on_menuitem_recheck_activate(self, data=None):
        log.debug('on_menuitem_recheck_activate')
        client.core.force_recheck(
            component.get('TorrentView').get_selected_torrents(),
        )

    def on_menuitem_open_folder_activate(self, data=None):
        log.debug('on_menuitem_open_folder')

        def _on_torrent_status(status):
            timestamp = Gtk.get_current_event_time()
            path = os.path.join(status['download_location'], status['files'][0]['path'].split('/')[0])
            deluge.common.show_file(path, timestamp=timestamp)
        for torrent_id in component.get('TorrentView').get_selected_torrents():
            component.get('SessionProxy').get_torrent_status(
                torrent_id, ['download_location', 'files'],
            ).addCallback(_on_torrent_status)

    def on_menuitem_move_activate(self, data=None):
        log.debug('on_menuitem_move_activate')
        component.get('SessionProxy').get_torrent_status(
            component.get('TorrentView').get_selected_torrent(),
            ['download_location'],
        ).addCallback(self.show_move_storage_dialog)

    def show_move_storage_dialog(self, status):
        log.debug('show_move_storage_dialog')
        builder = Gtk.Builder()
        builder.add_from_file(deluge.common.resource_filename(
            'deluge.ui.gtkui', os.path.join('glade', 'move_storage_dialog.ui'),
        ))
        # Keep it referenced:
        #  https://bugzilla.gnome.org/show_bug.cgi?id=546802
        self.move_storage_dialog = builder.get_object('move_storage_dialog')
        self.move_storage_dialog.set_transient_for(self.mainwindow.window)
        self.move_storage_dialog_hbox = builder.get_object('hbox_entry')
        self.move_storage_path_chooser = PathChooser('move_completed_paths_list')
        self.move_storage_dialog_hbox.add(self.move_storage_path_chooser)
        self.move_storage_dialog_hbox.show_all()
        self.move_storage_path_chooser.set_text(status['download_location'])

        def on_dialog_response_event(widget, response_id):
            def on_core_result(result):
                # Delete references
                self.move_storage_dialog.hide()
                del self.move_storage_dialog
                del self.move_storage_dialog_hbox

            if response_id == Gtk.ResponseType.CANCEL:
                on_core_result(None)

            if response_id == Gtk.ResponseType.OK:
                log.debug(
                    'Moving torrents to %s',
                    self.move_storage_path_chooser.get_text(),
                )
                path = self.move_storage_path_chooser.get_text()
                client.core.move_storage(
                    component.get('TorrentView').get_selected_torrents(), path,
                ).addCallback(on_core_result)

        self.move_storage_dialog.connect('response', on_dialog_response_event)
        self.move_storage_dialog.show()

    def on_menuitem_queue_top_activate(self, value):
        log.debug('on_menuitem_queue_top_activate')
        client.core.queue_top(component.get('TorrentView').get_selected_torrents())

    def on_menuitem_queue_up_activate(self, value):
        log.debug('on_menuitem_queue_up_activate')
        client.core.queue_up(component.get('TorrentView').get_selected_torrents())

    def on_menuitem_queue_down_activate(self, value):
        log.debug('on_menuitem_queue_down_activate')
        client.core.queue_down(component.get('TorrentView').get_selected_torrents())

    def on_menuitem_queue_bottom_activate(self, value):
        log.debug('on_menuitem_queue_bottom_activate')
        client.core.queue_bottom(component.get('TorrentView').get_selected_torrents())

    # View Menu #
    def on_menuitem_toolbar_toggled(self, value):
        log.debug('on_menuitem_toolbar_toggled')
        component.get('ToolBar').visible(value.get_active())

    def on_menuitem_sidebar_toggled(self, value):
        log.debug('on_menuitem_sidebar_toggled')
        component.get('SideBar').visible(value.get_active())

    def on_menuitem_statusbar_toggled(self, value):
        log.debug('on_menuitem_statusbar_toggled')
        component.get('StatusBar').visible(value.get_active())

    # Help Menu #
    def on_menuitem_homepage_activate(self, data=None):
        log.debug('on_menuitem_homepage_activate')
        deluge.common.open_url_in_browser('http://deluge-torrent.org')

    def on_menuitem_faq_activate(self, data=None):
        log.debug('on_menuitem_faq_activate')
        deluge.common.open_url_in_browser('http://dev.deluge-torrent.org/wiki/Faq')

    def on_menuitem_community_activate(self, data=None):
        log.debug('on_menuitem_community_activate')
        deluge.common.open_url_in_browser('http://forum.deluge-torrent.org/')

    def on_menuitem_about_activate(self, data=None):
        log.debug('on_menuitem_about_activate')
        from deluge.ui.gtkui.aboutdialog import AboutDialog
        AboutDialog().run()

    def on_menuitem_set_unlimited(self, widget):
        log.debug('widget name: %s', widget.get_name())
        funcs = {
            'menuitem_down_speed': 'max_download_speed',
            'menuitem_up_speed': 'max_upload_speed',
            'menuitem_max_connections': 'max_connections',
            'menuitem_upload_slots': 'max_upload_slots',
        }
        if widget.get_name() in funcs:
            torrent_ids = component.get('TorrentView').get_selected_torrents()
            client.core.set_torrent_options(torrent_ids, {funcs[widget.get_name()]: -1})

    def on_menuitem_set_other(self, widget):
        log.debug('widget name: %s', widget.get_name())
        status_map = {
            'menuitem_down_speed': ['max_download_speed', 'max_download_speed'],
            'menuitem_up_speed': ['max_upload_speed', 'max_upload_speed'],
            'menuitem_max_connections': ['max_connections', 'max_connections_global'],
            'menuitem_upload_slots': ['max_upload_slots', 'max_upload_slots_global'],
            'menuitem_stop_seed_at_ratio': ['stop_ratio', 'stop_seed_ratio'],
        }

        other_dialog_info = {
            'menuitem_down_speed': [
                _('Download Speed Limit'), _('Set the maximum download speed'),
                _('KiB/s'), 'downloading.svg',
            ],
            'menuitem_up_speed': [
                _('Upload Speed Limit'), _('Set the maximum upload speed'),
                _('KiB/s'), 'seeding.svg',
            ],
            'menuitem_max_connections': [
                _('Incoming Connections'), _('Set the maximum incoming connections'),
                '', Gtk.STOCK_NETWORK,
            ],
            'menuitem_upload_slots': [
                _('Peer Upload Slots'), _('Set the maximum upload slots'),
                '', Gtk.STOCK_SORT_ASCENDING,
            ],
            'menuitem_stop_seed_at_ratio': [_('Stop Seed At Ratio'), 'Stop torrent seeding at ratio', '', None],
        }

        core_key = status_map[widget.get_name()][0]
        core_key_global = status_map[widget.get_name()][1]

        def _on_torrent_status(status):
            other_dialog = other_dialog_info[widget.get_name()]
            # Add the default using status value
            if status:
                other_dialog.append(status[core_key_global])

            def set_value(value):
                if value is not None:
                    if value == 0:
                        value += -1
                    options = {core_key: value}
                    if core_key == 'stop_ratio':
                        options['stop_at_ratio'] = True
                    client.core.set_torrent_options(torrent_ids, options)

            dialog = OtherDialog(*other_dialog)
            dialog.run().addCallback(set_value)

        torrent_ids = component.get('TorrentView').get_selected_torrents()
        if len(torrent_ids) == 1:
            core_key_global = core_key
            d = component.get('SessionProxy').get_torrent_status(torrent_ids[0], [core_key])
        else:
            d = client.core.get_config_values([core_key_global])
        d.addCallback(_on_torrent_status)

    def on_menuitem_set_automanaged_on(self, widget):
        client.core.set_torrent_options(
            component.get('TorrentView').get_selected_torrents(),
            {'auto_managed': True},
        )

    def on_menuitem_set_automanaged_off(self, widget):
        client.core.set_torrent_options(
            component.get('TorrentView').get_selected_torrents(),
            {'auto_managed': False},
        )

    def on_menuitem_set_stop_seed_at_ratio_disable(self, widget):
        client.core.set_torrent_options(
            component.get('TorrentView').get_selected_torrents(),
            {'stop_at_ratio': False},
        )

    def on_menuitem_sidebar_zero_toggled(self, widget):
        self.config['sidebar_show_zero'] = widget.get_active()
        component.get('FilterTreeView').update()

    def on_menuitem_sidebar_trackers_toggled(self, widget):
        self.config['sidebar_show_trackers'] = widget.get_active()
        component.get('FilterTreeView').update()

    def on_menuitem_sidebar_owners_toggled(self, widget):
        self.config['sidebar_show_owners'] = widget.get_active()
        component.get('FilterTreeView').update()

    def _on_known_accounts(self, known_accounts):
        known_accounts_to_log = []
        for account in known_accounts:
            account_to_log = {}
            for key, value in account.copy().items():
                if key == 'password':
                    value = '*' * len(value)
                account_to_log[key] = value
            known_accounts_to_log.append(account_to_log)
        log.debug('_on_known_accounts: %s', known_accounts_to_log)
        if len(known_accounts) <= 1:
            return

        self.builder.get_object('menuitem_change_owner').set_visible(True)

        self.change_owner_submenu = Gtk.Menu()
        self.change_owner_submenu_items = {}
        maingroup = Gtk.RadioMenuItem(None, None)

        self.change_owner_submenu_items[None] = Gtk.RadioMenuItem(group=maingroup)

        for account in known_accounts:
            username = account['username']
            item = Gtk.RadioMenuItem(group=maingroup, label=username)
            self.change_owner_submenu_items[username] = item
            self.change_owner_submenu.append(item)
            item.connect('toggled', self._on_change_owner_toggled, username)

        self.change_owner_submenu.show_all()
        self.change_owner_submenu_items[None].set_active(True)
        self.change_owner_submenu_items[None].hide()
        self.builder.get_object('menuitem_change_owner').connect(
            'activate', self._on_change_owner_submenu_active,
        )
        self.builder.get_object('menuitem_change_owner').set_submenu(self.change_owner_submenu)

    def _on_known_accounts_fail(self, reason):
        self.builder.get_object('menuitem_change_owner').set_visible(False)

    def _on_change_owner_submenu_active(self, widget):
        log.debug('_on_change_owner_submenu_active')
        selected = component.get('TorrentView').get_selected_torrents()
        if len(selected) > 1:
            self.change_owner_submenu_items[None].set_active(True)
            return

        torrent_owner = component.get('TorrentView').get_torrent_status(selected[0])['owner']
        for username, item in self.change_owner_submenu_items.items():
            item.set_active(username == torrent_owner)

    def _on_change_owner_toggled(self, widget, username):
        log.debug('_on_change_owner_toggled')
        update_torrents = []
        selected = component.get('TorrentView').get_selected_torrents()
        for torrent_id in selected:
            torrent_status = component.get('TorrentView').get_torrent_status(torrent_id)
            if torrent_status['owner'] != username:
                update_torrents.append(torrent_id)

        if update_torrents:
            log.debug('Setting torrent owner "%s" on %s', username, update_torrents)

            def failed_change_owner(failure):
                ErrorDialog(
                    _('Ownership Change Error'),
                    _('There was an error while trying changing ownership.'),
                    self.mainwindow.window, details=failure.value.logable(),
                ).run()
            client.core.set_torrent_options(
                update_torrents, {'owner': username},
            ).addErrback(failed_change_owner)
