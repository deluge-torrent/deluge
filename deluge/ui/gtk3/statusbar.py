# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2008 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import division, unicode_literals

import logging

from gi.repository import Gtk
from gi.repository.GLib import timeout_add

import deluge.component as component
from deluge.common import fsize, fspeed, get_pixmap
from deluge.configmanager import ConfigManager
from deluge.ui.client import client

from .common import build_menu_radio_list
from .dialogs import OtherDialog

log = logging.getLogger(__name__)


class StatusBarItem(object):
    def __init__(
        self,
        image=None,
        stock=None,
        icon=None,
        text=None,
        markup=False,
        callback=None,
        tooltip=None,
    ):
        self._widgets = []
        self._ebox = Gtk.EventBox()
        self._hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, spacing=3)
        self._image = Gtk.Image()
        self._label = Gtk.Label()
        if image or icon or stock:
            self._hbox.add(self._image)
        self._hbox.add(self._label)
        self._ebox.add(self._hbox)

        # Add image from file or stock
        if image:
            self.set_image_from_file(image)
        if stock:
            self.set_image_from_stock(stock)
        if icon:
            self.set_image_from_icon(icon)

        # Add text
        if markup:
            self.set_markup(text)
        else:
            self.set_text(text)

        if callback is not None:
            self.set_callback(callback)

        if tooltip:
            self.set_tooltip(tooltip)

        self.show_all()

    def set_callback(self, callback):
        self._ebox.connect('button-press-event', callback)

    def show_all(self):
        self._ebox.show()
        self._hbox.show()
        self._image.show()

    def set_image_from_file(self, image):
        self._image.set_from_file(image)

    def set_image_from_stock(self, stock):
        self._image.set_from_stock(stock, Gtk.IconSize.MENU)

    def set_image_from_icon(self, icon):
        self._image.set_from_icon_name(icon, Gtk.IconSize.MENU)

    def set_text(self, text):
        if not text:
            self._label.hide()
        elif self._label.get_text() != text:
            self._label.set_text(text)
            self._label.show()

    def set_markup(self, text):
        if not text:
            self._label.hide()
        elif self._label.get_text() != text:
            self._label.set_markup(text)
            self._label.show()

    def set_tooltip(self, tip):
        if self._ebox.get_tooltip_text() != tip:
            self._ebox.set_tooltip_text(tip)

    def get_widgets(self):
        return self._widgets

    def get_eventbox(self):
        return self._ebox

    def get_text(self):
        return self._label.get_text()


class StatusBar(component.Component):
    def __init__(self):
        component.Component.__init__(self, 'StatusBar', interval=3)
        main_builder = component.get('MainWindow').get_builder()
        self.statusbar = main_builder.get_object('statusbar')
        self.config = ConfigManager('gtk3ui.conf')

        # Status variables that are updated via callback
        self.max_connections_global = -1
        self.num_connections = 0
        self.max_download_speed = -1.0
        self.download_rate = ''
        self.max_upload_speed = -1.0
        self.upload_rate = ''
        self.dht_nodes = 0
        self.dht_status = False
        self.health = False
        self.download_protocol_rate = 0.0
        self.upload_protocol_rate = 0.0

        self.config_value_changed_dict = {
            'max_connections_global': self._on_max_connections_global,
            'max_download_speed': self._on_max_download_speed,
            'max_upload_speed': self._on_max_upload_speed,
            'dht': self._on_dht,
        }
        self.current_warnings = []
        # Add hbox to the statusbar after removing the initial label widget
        self.hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, spacing=10)
        self.hbox.set_margin_top(2)
        self.hbox.set_margin_bottom(3)
        frame = self.statusbar.get_children()[0]
        frame.remove(frame.get_children()[0])
        frame.add(self.hbox)
        self.statusbar.show_all()
        # Create the not connected item
        self.not_connected_item = StatusBarItem(
            icon='network-offline-symbolic',
            text=_('Not Connected'),
            callback=self._on_notconnected_item_clicked,
        )
        # Show the not connected status bar
        self.show_not_connected()

        # Hide if necessary
        self.visible(self.config['show_statusbar'])

        client.register_event_handler(
            'ConfigValueChangedEvent', self.on_configvaluechanged_event
        )

    def start(self):
        # Add in images and labels
        self.remove_item(self.not_connected_item)

        self.connections_item = self.add_item(
            icon='network-transmit-receive-symbolic',
            callback=self._on_connection_item_clicked,
            tooltip=_('Connections (Limit)'),
            pack_start=True,
        )

        self.download_item = self.add_item(
            image=get_pixmap('downloading16.png'),
            callback=self._on_download_item_clicked,
            tooltip=_('Download Speed (Limit)'),
            pack_start=True,
        )

        self.upload_item = self.add_item(
            image=get_pixmap('seeding16.png'),
            callback=self._on_upload_item_clicked,
            tooltip=_('Upload Speed (Limit)'),
            pack_start=True,
        )

        self.traffic_item = self.add_item(
            image=get_pixmap('traffic16.png'),
            callback=self._on_traffic_item_clicked,
            tooltip=_('Protocol Traffic (Down:Up)'),
            pack_start=True,
        )

        self.dht_item = StatusBarItem(
            image=get_pixmap('dht16.png'), tooltip=_('DHT Nodes')
        )

        self.diskspace_item = self.add_item(
            icon='drive-harddisk-symbolic',
            callback=self._on_diskspace_item_clicked,
            tooltip=_('Free Disk Space'),
            pack_start=True,
        )

        self.external_ip_item = self.add_item(
            tooltip=_('External IP Address'),
            text=_('<b>IP</b> <small>%s</small>') % _('n/a'),
            markup=True,
            pack_start=True,
        )

        self.health_item = self.add_item(
            icon='network-error-symbolic',
            text=_('<b><small>Port Issue</small></b>'),
            markup=True,
            tooltip=_('No incoming connections, check port forwarding'),
            callback=self._on_health_icon_clicked,
        )

        self.health = False

        def update_config_values(configs):
            self._on_max_connections_global(configs['max_connections_global'])
            self._on_max_download_speed(configs['max_download_speed'])
            self._on_max_upload_speed(configs['max_upload_speed'])
            self._on_dht(configs['dht'])

        # Get some config values
        client.core.get_config_values(
            ['max_connections_global', 'max_download_speed', 'max_upload_speed', 'dht']
        ).addCallback(update_config_values)

    def stop(self):
        # When stopped, we just show the not connected thingy
        try:
            self.remove_item(self.connections_item)
            self.remove_item(self.dht_item)
            self.remove_item(self.download_item)
            self.remove_item(self.upload_item)
            self.remove_item(self.not_connected_item)
            self.remove_item(self.health_item)
            self.remove_item(self.traffic_item)
            self.remove_item(self.diskspace_item)
            self.remove_item(self.external_ip_item)
        except Exception as ex:
            log.debug('Unable to remove StatusBar item: %s', ex)
        self.show_not_connected()

    def visible(self, visible):
        if visible:
            self.statusbar.show()
        else:
            self.statusbar.hide()

        self.config['show_statusbar'] = visible

    def show_not_connected(self):
        self.hbox.pack_start(self.not_connected_item.get_eventbox(), False, False, 0)

    def add_item(
        self,
        image=None,
        stock=None,
        icon=None,
        text=None,
        markup=False,
        callback=None,
        tooltip=None,
        pack_start=False,
    ):
        """Adds an item to the status bar"""
        # The return tuple.. we return whatever widgets we add
        item = StatusBarItem(image, stock, icon, text, markup, callback, tooltip)
        if pack_start:
            self.hbox.pack_start(item.get_eventbox(), False, False, 0)
        else:
            self.hbox.pack_end(item.get_eventbox(), False, False, 0)
        return item

    def remove_item(self, item):
        """Removes an item from the statusbar"""
        if item.get_eventbox() in self.hbox.get_children():
            try:
                self.hbox.remove(item.get_eventbox())
            except Exception as ex:
                log.debug('Unable to remove widget: %s', ex)

    def add_timeout_item(
        self, seconds=3, image=None, stock=None, icon=None, text=None, callback=None
    ):
        """Adds an item to the StatusBar for seconds"""
        item = self.add_item(image, stock, icon, text, callback)
        # Start a timer to remove this item in seconds
        timeout_add(seconds * 1000, self.remove_item, item)

    def display_warning(self, text, callback=None):
        """Displays a warning to the user in the status bar"""
        if text not in self.current_warnings:
            item = self.add_item(
                icon='dialog-warning-symbolic', text=text, callback=callback
            )
            self.current_warnings.append(text)
            timeout_add(3000, self.remove_warning, item)

    def remove_warning(self, item):
        self.current_warnings.remove(item.get_text())
        self.remove_item(item)

    def clear_statusbar(self):
        def remove(child):
            self.hbox.remove(child)

        self.hbox.foreach(remove)

    def send_status_request(self):
        # Sends an async request for data from the core
        keys = [
            'num_peers',
            'upload_rate',
            'download_rate',
            'payload_upload_rate',
            'payload_download_rate',
        ]

        if self.dht_status:
            keys.append('dht_nodes')

        if not self.health:
            keys.append('has_incoming_connections')

        client.core.get_session_status(keys).addCallback(self._on_get_session_status)
        client.core.get_free_space().addCallback(self._on_get_free_space)
        client.core.get_external_ip().addCallback(self._on_get_external_ip)

    def on_configvaluechanged_event(self, key, value):
        """
        This is called when we receive a ConfigValueChangedEvent from
        the core.
        """
        if key in self.config_value_changed_dict:
            self.config_value_changed_dict[key](value)

    def _on_max_connections_global(self, max_connections):
        self.max_connections_global = max_connections
        self.update_connections_label()

    def _on_dht(self, value):
        self.dht_status = value
        if value:
            self.hbox.pack_start(self.dht_item.get_eventbox(), False, False, 0)
            self.send_status_request()
        else:
            self.remove_item(self.dht_item)

    def _on_get_session_status(self, status):
        self.download_rate = fspeed(
            status['payload_download_rate'], precision=0, shortform=True
        )
        self.upload_rate = fspeed(
            status['payload_upload_rate'], precision=0, shortform=True
        )
        self.download_protocol_rate = (
            status['download_rate'] - status['payload_download_rate']
        ) // 1024
        self.upload_protocol_rate = (
            status['upload_rate'] - status['payload_upload_rate']
        ) // 1024
        self.num_connections = status['num_peers']
        self.update_download_label()
        self.update_upload_label()
        self.update_traffic_label()
        self.update_connections_label()

        if 'dht_nodes' in status:
            self.dht_nodes = status['dht_nodes']
            self.update_dht_label()

        if 'has_incoming_connections' in status:
            self.health = status['has_incoming_connections']
            if self.health:
                self.remove_item(self.health_item)

    def _on_get_free_space(self, space):
        if space >= 0:
            self.diskspace_item.set_markup(
                '<small>%s</small>' % fsize(space, shortform=True)
            )
        else:
            self.diskspace_item.set_markup(
                '<span foreground="red">' + _('Error') + '</span>'
            )

    def _on_max_download_speed(self, max_download_speed):
        self.max_download_speed = max_download_speed
        self.update_download_label()

    def _on_max_upload_speed(self, max_upload_speed):
        self.max_upload_speed = max_upload_speed
        self.update_upload_label()

    def _on_get_external_ip(self, external_ip):
        ip = external_ip if external_ip else _('n/a')
        self.external_ip_item.set_markup(_('<b>IP</b> <small>%s</small>') % ip)

    def update_connections_label(self):
        # Set the max connections label
        if self.max_connections_global < 0:
            label_string = '%s' % self.num_connections
        else:
            label_string = '%s <small>(%s)</small>' % (
                self.num_connections,
                self.max_connections_global,
            )

        self.connections_item.set_markup(label_string)

        if self.num_connections:
            self.connections_item.set_image_from_icon(
                'network-transmit-receive-symbolic'
            )
        else:
            self.connections_item.set_image_from_icon('network-idle-symbolic')

    def update_dht_label(self):
        # Set the max connections label
        self.dht_item.set_markup('<small>%s</small>' % (self.dht_nodes))

    def update_download_label(self):
        # Set the download speed label
        if self.max_download_speed <= 0:
            label_string = self.download_rate
        else:
            label_string = '%s <small>(%i %s)</small>' % (
                self.download_rate,
                self.max_download_speed,
                _('K/s'),
            )

        self.download_item.set_markup(label_string)

    def update_upload_label(self):
        # Set the upload speed label
        if self.max_upload_speed <= 0:
            label_string = self.upload_rate
        else:
            label_string = '%s <small>(%i %s)</small>' % (
                self.upload_rate,
                self.max_upload_speed,
                _('K/s'),
            )

        self.upload_item.set_markup(label_string)

    def update_traffic_label(self):
        label_string = '<small>%i:%i %s</small>' % (
            self.download_protocol_rate,
            self.upload_protocol_rate,
            _('K/s'),
        )
        self.traffic_item.set_markup(label_string)

    def update(self):
        self.send_status_request()

    def set_limit_value(self, widget, core_key):
        log.debug('_on_set_unlimit_other %s', core_key)
        other_dialog_info = {
            'max_download_speed': (
                _('Download Speed Limit'),
                _('Set the maximum download speed'),
                _('K/s'),
                'downloading.svg',
                self.max_download_speed,
            ),
            'max_upload_speed': (
                _('Upload Speed Limit'),
                _('Set the maximum upload speed'),
                _('K/s'),
                'seeding.svg',
                self.max_upload_speed,
            ),
            'max_connections_global': (
                _('Incoming Connections'),
                _('Set the maximum incoming connections'),
                '',
                'network-transmit-receive-symbolic',
                self.max_connections_global,
            ),
        }

        def set_value(value):
            log.debug('value: %s', value)
            if value is None:
                return
            elif value == 0:
                value = -1
            # Set the config in the core
            if value != getattr(self, core_key):
                client.core.set_config({core_key: value})

        if widget.get_name() == 'unlimited':
            set_value(-1)
        elif widget.get_name() == 'other':

            def dialog_finished(response_id):
                if response_id == Gtk.ResponseType.OK:
                    set_value(dialog.get_value())

            dialog = OtherDialog(*other_dialog_info[core_key])
            dialog.run().addCallback(set_value)
        else:
            value = widget.get_children()[0].get_text().split(' ')[0]
            set_value(value)

    def _on_download_item_clicked(self, widget, event):
        self.menu = build_menu_radio_list(
            self.config['tray_download_speed_list'],
            self._on_set_download_speed,
            self.max_download_speed,
            _('K/s'),
            show_notset=True,
            show_other=True,
        )
        self.menu.show_all()
        self.menu.popup(None, None, None, None, event.button, event.time)

    def _on_set_download_speed(self, widget):
        log.debug('_on_set_download_speed')
        self.set_limit_value(widget, 'max_download_speed')

    def _on_upload_item_clicked(self, widget, event):
        self.menu = build_menu_radio_list(
            self.config['tray_upload_speed_list'],
            self._on_set_upload_speed,
            self.max_upload_speed,
            _('K/s'),
            show_notset=True,
            show_other=True,
        )
        self.menu.show_all()
        self.menu.popup(None, None, None, None, event.button, event.time)

    def _on_set_upload_speed(self, widget):
        log.debug('_on_set_upload_speed')
        self.set_limit_value(widget, 'max_upload_speed')

    def _on_connection_item_clicked(self, widget, event):
        self.menu = build_menu_radio_list(
            self.config['connection_limit_list'],
            self._on_set_connection_limit,
            self.max_connections_global,
            show_notset=True,
            show_other=True,
        )
        self.menu.show_all()
        self.menu.popup(None, None, None, None, event.button, event.time)

    def _on_set_connection_limit(self, widget):
        log.debug('_on_set_connection_limit')
        self.set_limit_value(widget, 'max_connections_global')

    def _on_health_icon_clicked(self, widget, event):
        component.get('Preferences').show('network')

    def _on_notconnected_item_clicked(self, widget, event):
        component.get('ConnectionManager').show()

    def _on_traffic_item_clicked(self, widget, event):
        component.get('Preferences').show('network')

    def _on_diskspace_item_clicked(self, widget, event):
        component.get('Preferences').show('downloads')
