#
# statusbar.py
#
# Copyright (C) 2007, 2008 Andrew Resch <andrewresch@gmail.com>
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


import gtk
import gobject

from deluge.ui.client import client
import deluge.component as component
import deluge.common
import common
from deluge.configmanager import ConfigManager
from deluge.log import LOG as log

class StatusBarItem:
    def __init__(self, image=None, stock=None, text=None, callback=None, tooltip=None):
        self._widgets = []
        self._ebox = gtk.EventBox()
        self._hbox = gtk.HBox()
        self._hbox.set_spacing(5)
        self._image = gtk.Image()
        self._label = gtk.Label()
        self._hbox.add(self._image)
        self._hbox.add(self._label)
        self._ebox.add(self._hbox)

        # Add image from file or stock
        if image != None or stock != None:
            if image != None:
                self.set_image_from_file(image)
            if stock != None:
                self.set_image_from_stock(stock)

        # Add text
        if text != None:
            self.set_text(text)

        if callback != None:
            self.set_callback(callback)

        if tooltip:
            self.set_tooltip(tooltip)

        self.show_all()

    def set_callback(self, callback):
        self._ebox.connect("button-press-event", callback)

    def show_all(self):
        self._ebox.show()
        self._hbox.show()
        self._image.show()
        self._label.show()

    def set_image_from_file(self, image):
        self._image.set_from_file(image)

    def set_image_from_stock(self, stock):
        self._image.set_from_stock(stock, gtk.ICON_SIZE_MENU)

    def set_text(self, text):
        if self._label.get_text() != text:
            self._label.set_text(text)

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
        component.Component.__init__(self, "StatusBar", interval=3)
        self.window = component.get("MainWindow")
        self.statusbar = self.window.main_glade.get_widget("statusbar")
        self.config = ConfigManager("gtkui.conf")

        # Status variables that are updated via callback
        self.max_connections = -1
        self.num_connections = 0
        self.max_download_speed = -1.0
        self.download_rate = ""
        self.max_upload_speed = -1.0
        self.upload_rate = ""
        self.dht_nodes = 0
        self.dht_status = False
        self.health = False
        self.download_protocol_rate = 0.0
        self.upload_protocol_rate = 0.0

        self.config_value_changed_dict = {
            "max_connections_global": self._on_max_connections_global,
            "max_download_speed": self._on_max_download_speed,
            "max_upload_speed": self._on_max_upload_speed,
            "dht": self._on_dht
        }
        self.current_warnings = []
        # Add a HBox to the statusbar after removing the initial label widget
        self.hbox = gtk.HBox()
        self.hbox.set_spacing(10)
        frame = self.statusbar.get_children()[0]
        frame.remove(frame.get_children()[0])
        frame.add(self.hbox)
        self.statusbar.show_all()
        # Create the not connected item
        self.not_connected_item = StatusBarItem(
            stock=gtk.STOCK_STOP, text=_("Not Connected"),
            callback=self._on_notconnected_item_clicked)
        # Show the not connected status bar
        self.show_not_connected()

        # Hide if necessary
        self.visible(self.config["show_statusbar"])

        client.register_event_handler("ConfigValueChangedEvent", self.on_configvaluechanged_event)

    def start(self):
        # Add in images and labels
        self.remove_item(self.not_connected_item)

        self.connections_item = self.add_item(
            stock=gtk.STOCK_NETWORK,
            callback=self._on_connection_item_clicked,
            tooltip=_("Connections"))

        self.download_item = self.add_item(
            image=deluge.common.get_pixmap("downloading16.png"),
            callback=self._on_download_item_clicked,
            tooltip=_("Download Speed"))

        self.upload_item = self.add_item(
            image=deluge.common.get_pixmap("seeding16.png"),
            callback=self._on_upload_item_clicked,
            tooltip=_("Upload Speed"))

        self.traffic_item = self.add_item(
            image=deluge.common.get_pixmap("traffic16.png"),
            callback=self._on_traffic_item_clicked,
            tooltip=_("Protocol Traffic Download/Upload"))

        self.dht_item = StatusBarItem(
            image=deluge.common.get_pixmap("dht16.png"), tooltip=_("DHT Nodes"))

        self.diskspace_item = self.add_item(
                stock=gtk.STOCK_HARDDISK,
                callback=self._on_diskspace_item_clicked,
                tooltip=_("Free Disk Space"))

        self.health_item = self.add_item(
                stock=gtk.STOCK_DIALOG_ERROR,
                text=_("No Incoming Connections!"),
                callback=self._on_health_icon_clicked)

        self.health = False

        # Get some config values
        client.core.get_config_value(
            "max_connections_global").addCallback(self._on_max_connections_global)
        client.core.get_config_value(
            "max_download_speed").addCallback(self._on_max_download_speed)
        client.core.get_config_value(
            "max_upload_speed").addCallback(self._on_max_upload_speed)
        client.core.get_config_value("dht").addCallback(self._on_dht)

        self.send_status_request()

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
        except Exception, e:
            log.debug("Unable to remove StatusBar item: %s", e)
        self.show_not_connected()

    def visible(self, visible):
        if visible:
            self.statusbar.show()
        else:
            self.statusbar.hide()

        self.config["show_statusbar"] = visible

    def show_not_connected(self):
        self.hbox.pack_start(
            self.not_connected_item.get_eventbox(), expand=False, fill=False)

    def add_item(self, image=None, stock=None, text=None, callback=None, tooltip=None):
        """Adds an item to the status bar"""
        # The return tuple.. we return whatever widgets we add
        item = StatusBarItem(image, stock, text, callback, tooltip)
        self.hbox.pack_start(item.get_eventbox(), expand=False, fill=False)
        return item

    def remove_item(self, item):
        """Removes an item from the statusbar"""
        if item.get_eventbox() in self.hbox.get_children():
            try:
                self.hbox.remove(item.get_eventbox())
            except Exception, e:
                log.debug("Unable to remove widget: %s", e)

    def add_timeout_item(self, seconds=3, image=None, stock=None, text=None, callback=None):
        """Adds an item to the StatusBar for seconds"""
        item = self.add_item(image, stock, text, callback)
        # Start a timer to remove this item in seconds
        gobject.timeout_add(seconds * 1000, self.remove_item, item)

    def display_warning(self, text, callback=None):
        """Displays a warning to the user in the status bar"""
        if text not in self.current_warnings:
            item = self.add_item(
                stock=gtk.STOCK_DIALOG_WARNING, text=text, callback=callback)
            self.current_warnings.append(text)
            gobject.timeout_add(3000, self.remove_warning, item)

    def remove_warning(self, item):
        self.current_warnings.remove(item.get_text())
        self.remove_item(item)

    def clear_statusbar(self):
        def remove(child):
            self.hbox.remove(child)
        self.hbox.foreach(remove)

    def send_status_request(self):
        # Sends an async request for data from the core
        client.core.get_num_connections().addCallback(self._on_get_num_connections)
        keys = [
            "upload_rate",
            "download_rate",
            "payload_upload_rate",
            "payload_download_rate"]

        if self.dht_status:
            keys.append("dht_nodes")

        if not self.health:
            keys.append("has_incoming_connections")

        client.core.get_session_status(keys).addCallback(self._on_get_session_status)
        client.core.get_free_space().addCallback(self._on_get_free_space)

    def on_configvaluechanged_event(self, key, value):
        """
        This is called when we receive a ConfigValueChangedEvent from
        the core.
        """

        if key in self.config_value_changed_dict.keys():
            self.config_value_changed_dict[key](value)

    def _on_max_connections_global(self, max_connections):
        self.max_connections = max_connections
        self.update_connections_label()

    def _on_get_num_connections(self, num_connections):
        self.num_connections = num_connections
        self.update_connections_label()

    def _on_dht(self, value):
        self.dht_status = value
        if value:
            self.hbox.pack_start(
                self.dht_item.get_eventbox(), expand=False, fill=False)
            self.send_status_request()
        else:
            self.remove_item(self.dht_item)

    def _on_get_session_status(self, status):
        self.download_rate = deluge.common.fspeed(status["payload_download_rate"])
        self.upload_rate = deluge.common.fspeed(status["payload_upload_rate"])
        self.download_protocol_rate = (status["download_rate"] - status["payload_download_rate"]) / 1024
        self.upload_protocol_rate = (status["upload_rate"] - status["payload_upload_rate"]) / 1024
        self.update_download_label()
        self.update_upload_label()
        self.update_traffic_label()

        if "dht_nodes" in status:
            self.dht_nodes = status["dht_nodes"]
            self.update_dht_label()

        if "has_incoming_connections" in status:
            self.health = status["has_incoming_connections"]
            if self.health:
                self.remove_item(self.health_item)

    def _on_get_free_space(self, space):
        self.diskspace_item.set_text(deluge.common.fsize(space))

    def _on_max_download_speed(self, max_download_speed):
        self.max_download_speed = max_download_speed
        self.update_download_label()

    def _on_max_upload_speed(self, max_upload_speed):
        self.max_upload_speed = max_upload_speed
        self.update_upload_label()

    def update_connections_label(self):
        # Set the max connections label
        if self.max_connections < 0:
            label_string = "%s" % self.num_connections
        else:
            label_string = "%s (%s)" % (self.num_connections, self.max_connections)

        self.connections_item.set_text(label_string)

    def update_dht_label(self):
        # Set the max connections label
        self.dht_item.set_text("%s" % (self.dht_nodes))

    def update_download_label(self):
        # Set the download speed label
        if self.max_download_speed <= 0:
            label_string = self.download_rate
        else:
            label_string = "%s (%s %s)" % (
                self.download_rate, self.max_download_speed, _("KiB/s"))

        self.download_item.set_text(label_string)

    def update_upload_label(self):
        # Set the upload speed label
        if self.max_upload_speed <= 0:
            label_string = self.upload_rate
        else:
            label_string = "%s (%s %s)" % (
                self.upload_rate, self.max_upload_speed, _("KiB/s"))

        self.upload_item.set_text(label_string)

    def update_traffic_label(self):
        label_string = "%.2f/%.2f %s" % (self.download_protocol_rate, self.upload_protocol_rate, _("KiB/s"))
        self.traffic_item.set_text(label_string)

    def update(self):
        # Send status request
        self.send_status_request()

    def _on_download_item_clicked(self, widget, event):
        menu = common.build_menu_radio_list(
            self.config["tray_download_speed_list"],
            self._on_set_download_speed,
            self.max_download_speed,
            _("KiB/s"), show_notset=True, show_other=True)
        menu.show_all()
        menu.popup(None, None, None, event.button, event.time)

    def _on_set_download_speed(self, widget):
        log.debug("_on_set_download_speed")

        if widget.get_name() == "unlimited":
            value = -1
        elif widget.get_name() == "other":
            value = common.show_other_dialog(
                _("Set Maximum Download Speed"), _("KiB/s"), None, "downloading.svg", self.max_download_speed)
            if value == None:
                return
        else:
            value = float(widget.get_children()[0].get_text().split(" ")[0])

        log.debug("value: %s", value)

        # Set the config in the core
        if value != self.max_download_speed:
            client.core.set_config({"max_download_speed": value})

    def _on_upload_item_clicked(self, widget, event):
        menu = common.build_menu_radio_list(
            self.config["tray_upload_speed_list"],
            self._on_set_upload_speed,
            self.max_upload_speed,
            _("KiB/s"), show_notset=True, show_other=True)
        menu.show_all()
        menu.popup(None, None, None, event.button, event.time)

    def _on_set_upload_speed(self, widget):
        log.debug("_on_set_upload_speed")

        if widget.get_name() == "unlimited":
            value = -1
        elif widget.get_name() == "other":
            value = common.show_other_dialog(
                _("Set Maximum Upload Speed"), _("KiB/s"), None, "seeding.svg", self.max_upload_speed)
            if value == None:
                return
        else:
            value = float(widget.get_children()[0].get_text().split(" ")[0])

        log.debug("value: %s", value)

        # Set the config in the core
        if value != self.max_upload_speed:
            client.core.set_config({"max_upload_speed": value})

    def _on_connection_item_clicked(self, widget, event):
        menu = common.build_menu_radio_list(
            self.config["connection_limit_list"],
            self._on_set_connection_limit,
            self.max_connections, show_notset=True, show_other=True)
        menu.show_all()
        menu.popup(None, None, None, event.button, event.time)

    def _on_set_connection_limit(self, widget):
        log.debug("_on_set_connection_limit")

        if widget.get_name() == "unlimited":
            value = -1
        elif widget.get_name() == "other":
            value = common.show_other_dialog(
                _("Set Maximum Connections"), "", gtk.STOCK_NETWORK, None, self.max_connections)
            if value == None:
                return
        else:
            value = int(widget.get_children()[0].get_text().split(" ")[0])

        log.debug("value: %s", value)

        # Set the config in the core
        if value != self.max_connections:
            client.core.set_config({"max_connections_global": value})

    def _on_health_icon_clicked(self, widget, event):
        component.get("Preferences").show("Network")

    def _on_notconnected_item_clicked(self, widget, event):
        component.get("ConnectionManager").show()

    def _on_traffic_item_clicked(self, widget, event):
        component.get("Preferences").show("Network")

    def _on_diskspace_item_clicked(self, widget, event):
        component.get("Preferences").show("Downloads")
