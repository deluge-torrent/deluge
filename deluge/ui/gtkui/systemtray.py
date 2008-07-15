#
# systemtray.py
#
# Copyright (C) 2007, 2008 Andrew Resch ('andar') <andrewresch@gmail.com>
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

import gtk
import pkg_resources

import deluge.component as component
from deluge.ui.client import aclient as client
import deluge.common
from deluge.configmanager import ConfigManager
from deluge.log import LOG as log

class SystemTray(component.Component):
    def __init__(self):
        component.Component.__init__(self, "SystemTray", interval=4000)
        self.window = component.get("MainWindow")
        self.config = ConfigManager("gtkui.conf")
        # List of widgets that need to be hidden when not connected to a host
        self.hide_widget_list = [
            "menuitem_add_torrent",
            "menuitem_pause_all",
            "menuitem_resume_all",
            "menuitem_download_limit",
            "menuitem_upload_limit",
            "menuitem_quitdaemon",
            "separatormenuitem1",
            "separatormenuitem2",
            "separatormenuitem3",
            "separatormenuitem4"
        ]
        self.config.register_set_function("enable_system_tray", 
            self.on_enable_system_tray_set)

        self.max_download_speed = -1.0
        self.download_rate = 0.0
        self.max_upload_speed = -1.0
        self.upload_rate = 0.0

        self.config_value_changed_dict = {
            "max_download_speed": self._on_max_download_speed,
            "max_upload_speed": self._on_max_upload_speed
        }
            
    def enable(self):
        """Enables the system tray icon."""
        log.debug("Enabling the system tray icon..")
        self.tray_glade = gtk.glade.XML(
            pkg_resources.resource_filename("deluge.ui.gtkui", 
                                            "glade/tray_menu.glade"))

        if deluge.common.windows_check():
            self.tray = gtk.status_icon_new_from_pixbuf(
                deluge.common.get_logo(32))
        else:
            try:
                self.tray = gtk.status_icon_new_from_icon_name("deluge")
            except:
                log.warning("Update PyGTK to 2.10 or greater for SystemTray..")
                return
            
        self.tray.connect("activate", self.on_tray_clicked)
        self.tray.connect("popup-menu", self.on_tray_popup)
        
        
        self.tray_glade.signal_autoconnect({
            "on_menuitem_show_deluge_activate": \
                self.on_menuitem_show_deluge_activate,
            "on_menuitem_add_torrent_activate": \
                self.on_menuitem_add_torrent_activate,
            "on_menuitem_pause_all_activate": \
                self.on_menuitem_pause_all_activate,
            "on_menuitem_resume_all_activate": \
                self.on_menuitem_resume_all_activate,
            "on_menuitem_quit_activate": self.on_menuitem_quit_activate,
            "on_menuitem_quitdaemon_activate": \
                self.on_menuitem_quitdaemon_activate
        })
        
        self.tray_menu = self.tray_glade.get_widget("tray_menu")

        self.tray_glade.get_widget("download-limit-image").set_from_file(
            deluge.common.get_pixmap("downloading16.png"))
        self.tray_glade.get_widget("upload-limit-image").set_from_file(
            deluge.common.get_pixmap("seeding16.png"))

        if self.config["classic_mode"]:
            self.hide_widget_list.remove("menuitem_quitdaemon")
            self.hide_widget_list.remove("separatormenuitem4")
            self.tray_glade.get_widget("menuitem_quitdaemon").hide()
            self.tray_glade.get_widget("separatormenuitem4").hide()
        
        if client.get_core_uri() == None:
        # Hide menu widgets because we're not connected to a host.
            for widget in self.hide_widget_list:
                self.tray_glade.get_widget(widget).hide()
            
    def start(self):
        if self.config["enable_system_tray"]:
            # Show widgets in the hide list because we've connected to a host
            for widget in self.hide_widget_list:
                self.tray_glade.get_widget(widget).show()

            # Build the bandwidth speed limit menus
            self.build_tray_bwsetsubmenu()
            
            # Get some config values
            client.get_config_value(
                self._on_max_download_speed, "max_download_speed")
            client.get_config_value(
                self._on_max_upload_speed, "max_upload_speed")
            self.send_status_request()

    def stop(self):
        try:
            # Hide widgets in hide list because we're not connected to a host
            for widget in self.hide_widget_list:
                self.tray_glade.get_widget(widget).hide()
        except Exception, e:
            log.debug("Unable to hide system tray menu widgets: %s", e)
    
    def shutdown(self):
        self.tray.set_visible(False)
    
    def send_status_request(self):
        client.get_download_rate(self._on_get_download_rate)
        client.get_upload_rate(self._on_get_upload_rate)

    def config_value_changed(self, key, value):
        """This is called when we received a config_value_changed signal from
        the core."""
        
        if key in self.config_value_changed_dict.keys():
            self.config_value_changed_dict[key](value)
            
    def _on_max_download_speed(self, max_download_speed):
        if self.max_download_speed != max_download_speed:
            self.max_download_speed = max_download_speed
            self.build_tray_bwsetsubmenu()
    
    def _on_get_download_rate(self, download_rate):
        self.download_rate = deluge.common.fsize(download_rate)
    
    def _on_max_upload_speed(self, max_upload_speed):
        if self.max_upload_speed != max_upload_speed:
            self.max_upload_speed = max_upload_speed
            self.build_tray_bwsetsubmenu()
    
    def _on_get_upload_rate(self, upload_rate):
        self.upload_rate = deluge.common.fsize(upload_rate)
                
    def update(self):
        # Set the tool tip text
        max_download_speed = self.max_download_speed
        max_upload_speed = self.max_upload_speed
        
        if max_download_speed == -1:
            max_download_speed = _("Unlimited")
        else:
            max_download_speed = "%s KiB/s" % (max_download_speed)
        if max_upload_speed == -1:
            max_upload_speed = _("Unlimited")
        else:
            max_upload_speed = "%s KiB/s" % (max_upload_speed)
        
        msg = '%s\n%s: %s (%s)\n%s: %s (%s)' % (\
            _("Deluge"), _("Down"), self.download_rate, \
            max_download_speed, _("Up"), self.upload_rate, max_upload_speed)
        
        # Set the tooltip
        self.tray.set_tooltip(msg)
        
        self.send_status_request()
        
    def build_tray_bwsetsubmenu(self):
        # Create the Download speed list sub-menu
        submenu_bwdownset = deluge.common.build_menu_radio_list(
                self.config["tray_download_speed_list"], self.tray_setbwdown,
                self.max_download_speed,
                     _("KiB/s"), show_notset=True, show_other=True)
        
        # Create the Upload speed list sub-menu
        submenu_bwupset = deluge.common.build_menu_radio_list(
                self.config["tray_upload_speed_list"], self.tray_setbwup, 
                self.max_upload_speed,
                _("KiB/s"), show_notset=True, show_other=True)
        
        # Add the sub-menus to the tray menu
        self.tray_glade.get_widget("menuitem_download_limit").set_submenu(
            submenu_bwdownset)
        self.tray_glade.get_widget("menuitem_upload_limit").set_submenu(
            submenu_bwupset)
        
        # Show the sub-menus for all to see
        submenu_bwdownset.show_all()
        submenu_bwupset.show_all()
        
    def disable(self):
        """Disables the system tray icon."""
        log.debug("Disabling the system tray icon..")
        try:
            self.tray.set_visible(False)
            del self.tray
            del self.tray_glade
            del self.tray_menu
        except Exception, e:
            log.debug("Unable to disable system tray: %s", e)
    
    def on_enable_system_tray_set(self, key, value):
        """Called whenever the 'enable_system_tray' config key is modified"""
        if value:
            self.enable()
        else:
            self.disable()
    
    def on_tray_clicked(self, icon):
        """Called when the tray icon is left clicked."""
        if self.window.active():
            self.window.hide()
        else:
            if self.config["lock_tray"]:
                if not self.unlock_tray():
                    return
            self.window.present()
    
    def on_tray_popup(self, status_icon, button, activate_time):
        """Called when the tray icon is right clicked."""
        if self.window.visible():
            self.tray_glade.get_widget("menuitem_show_deluge").set_active(True)
        else:
            self.tray_glade.get_widget("menuitem_show_deluge").set_active(False)
             
        popup_function = gtk.status_icon_position_menu
        if deluge.common.windows_check():
            popup_function = None
        self.tray_menu.popup(None, None, popup_function, 
            button, activate_time, status_icon)

    def on_menuitem_show_deluge_activate(self, menuitem):
        log.debug("on_menuitem_show_deluge_activate")
        if menuitem.get_active() and not self.window.visible():
            if self.config["lock_tray"]:
                if not self.unlock_tray():
                    return
            self.window.present()
        elif not menuitem.get_active() and self.window.visible():
            self.window.hide()
        
    def on_menuitem_add_torrent_activate(self, menuitem):
        log.debug("on_menuitem_add_torrent_activate")
        from addtorrentdialog import AddTorrentDialog
        client.add_torrent_file(AddTorrentDialog().show())
        
    def on_menuitem_pause_all_activate(self, menuitem):
        log.debug("on_menuitem_pause_all_activate")
        client.pause_all_torrents()
        
    def on_menuitem_resume_all_activate(self, menuitem):
        log.debug("on_menuitem_resume_all_activate")
        client.resume_all_torrents()
        
    def on_menuitem_quit_activate(self, menuitem):
        log.debug("on_menuitem_quit_activate")
        if self.config["lock_tray"]:
            if not self.unlock_tray():
                return

        if self.config["classic_mode"]:
            client.shutdown()

        self.window.quit()
        
    def on_menuitem_quitdaemon_activate(self, menuitem):
        log.debug("on_menuitem_quitdaemon_activate")
        if self.config["lock_tray"]:
            if not self.unlock_tray():
                return

        client.shutdown()
        self.window.quit()
        
    def tray_setbwdown(self, widget, data=None):    
        self.setbwlimit(widget, _("Download"), "max_download_speed", 
            "tray_download_speed_list", self.max_download_speed)
        
    def tray_setbwup(self, widget, data=None):
        self.setbwlimit(widget, _("Upload"), "max_upload_speed",
            "tray_upload_speed_list", self.max_upload_speed)
                
    def setbwlimit(self, widget, string, core_key, ui_key, default):
        """Sets the bandwidth limit based on the user selection."""
        value = widget.get_children()[0].get_text().rstrip(" " + _("KiB/s"))
        if value == _("Unlimited"):
            value = -1
        
        if value == _("Other..."):
            value = deluge.common.show_other_dialog(
                string + " Speed (KiB/s):", default)
            if value == None:
                return
        
        # Set the config in the core
        value = float(value)
        config_to_set = {core_key: value}
        client.set_config(config_to_set)

        self.build_tray_bwsetsubmenu()
            
    def unlock_tray(self, is_showing_dlg=[False]):
        import hashlib
        log.debug("Show tray lock dialog")
        result = False
        
        if is_showing_dlg[0]:
            return
        is_showing_dlg[0] = True
        
        entered_pass = gtk.Entry(25)
        entered_pass.set_activates_default(True)
        entered_pass.set_width_chars(25)
        entered_pass.set_visibility(False)
        entered_pass.show()
        tray_lock = gtk.Dialog(title=_("Deluge is locked"), parent=None,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, 
            gtk.RESPONSE_ACCEPT))
        label = gtk.Label(_("Deluge is password protected.\nTo show the Deluge \
window, please enter your password"))
        label.set_line_wrap(True)
        label.set_justify(gtk.JUSTIFY_CENTER)
        tray_lock.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        tray_lock.set_size_request(400, 200)
        tray_lock.set_default_response(gtk.RESPONSE_ACCEPT)
        tray_lock.vbox.pack_start(label)
        tray_lock.vbox.pack_start(entered_pass)
        tray_lock.show_all()
        if tray_lock.run() == gtk.RESPONSE_ACCEPT:
            if self.config["tray_password"] == hashlib.sha1(\
                entered_pass.get_text()).hexdigest():
                result = True
        tray_lock.destroy()
        is_showing_dlg[0] = False
        
        return result

