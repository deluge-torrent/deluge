#
# systemtray.py
#
# Copyright (C) 2007 Andrew Resch ('andar') <andrewresch@gmail.com>
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

import deluge.ui.component as component
import deluge.ui.client as client
import deluge.common
from deluge.configmanager import ConfigManager
from deluge.log import LOG as log

class SystemTray(component.Component):
    def __init__(self):
        component.Component.__init__(self, "SystemTray")
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
    
    def enable(self):
        """Enables the system tray icon."""
        log.debug("Enabling the system tray icon..")
        self.tray = gtk.status_icon_new_from_icon_name("deluge")
        self.tray.connect("activate", self.on_tray_clicked)
        self.tray.connect("popup-menu", self.on_tray_popup)
        
        self.tray_glade = gtk.glade.XML(
            pkg_resources.resource_filename("deluge.ui.gtkui", 
                                            "glade/tray_menu.glade"))
        
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

    def stop(self):
        try:
            # Hide widgets in hide list because we're not connected to a host
            for widget in self.hide_widget_list:
                self.tray_glade.get_widget(widget).hide()
        except Exception, e:
            log.debug("Unable to hide system tray menu widgets: %s", e)
            
    def build_tray_bwsetsubmenu(self):
        # Create the Download speed list sub-menu
        submenu_bwdownset = self.build_menu_radio_list(
                self.config["tray_download_speed_list"], self.tray_setbwdown,
                client.get_config_value("max_download_speed"),
                     _("KiB/s"), show_notset=True, show_other=True)
        
        # Create the Upload speed list sub-menu
        submenu_bwupset = self.build_menu_radio_list(
                self.config["tray_upload_speed_list"], self.tray_setbwup, 
                client.get_config_value("max_upload_speed"),
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
        if self.window.visible():
            if self.window.active():
                self.window.hide()
            else:
                self.window.present()
                # Force UI update as we don't update it while minimized
                self.window.update()
        else:
            if self.config["lock_tray"] == True:
                self.unlock_tray("mainwinshow")
            else:
                self.window.show()
                # Force UI update as we don't update it while in tray
                self.window.update()
    
    def on_tray_popup(self, status_icon, button, activate_time):
        """Called when the tray icon is right clicked."""
        if self.window.visible():
            self.tray_glade.get_widget("menuitem_show_deluge").set_active(True)
        else:
            self.tray_glade.get_widget("menuitem_show_deluge").set_active(False)
             
        self.tray_menu.popup(None, None, gtk.status_icon_position_menu, 
            button, activate_time, status_icon)

    def on_menuitem_show_deluge_activate(self, menuitem):
        log.debug("on_menuitem_show_deluge_activate")
        if menuitem.get_active() and not self.window.visible():
            if self.config["lock_tray"] == True:
                self.unlock_tray("mainwinshow")
            else:
                self.window.show()
        elif not menuitem.get_active() and self.window.visible():
            self.window.hide()
        
    def on_menuitem_add_torrent_activate(self, menuitem):
        log.debug("on_menuitem_add_torrent_activate")
        from addtorrentdialog import AddTorrentDialog
        client.add_torrent_file(AddTorrentDialog().run())
        
    def on_menuitem_pause_all_activate(self, menuitem):
        log.debug("on_menuitem_pause_all_activate")
        self.core.pause_all_torrents()
        
    def on_menuitem_resume_all_activate(self, menuitem):
        log.debug("on_menuitem_resume_all_activate")
        self.core.resume_all_torrents()
        
    def on_menuitem_quit_activate(self, menuitem):
        log.debug("on_menuitem_quit_activate")
        if self.window.visible():
            self.window.quit()
        else:
            if self.config["lock_tray"] == True:
                self.unlock_tray("quitui")
            else:
                self.window.quit()

    def on_menuitem_quitdaemon_activate(self, menuitem):
        log.debug("on_menuitem_quitdaemon_activate")
        if self.window.visible():
            self.window.quit()
            client.shutdown()
        else:
            if self.config["lock_tray"] == True:
                self.unlock_tray("quitdaemon")
            else:
                self.window.quit()
                client.shutdown()
        
    def build_menu_radio_list(self, value_list, callback, pref_value=None, 
        suffix=None, show_notset=False, notset_label=None, notset_lessthan=0, 
        show_other=False, show_activated=False, activated_label=None):
        # Build a menu with radio menu items from a list and connect them to 
        # the callback. The pref_value is what you would like to test for the 
        # default active radio item.
        if notset_label is None:
            notset_label = _("Unlimited")

        if activated_label is None:
            activated_label = _("Activated")

        menu = gtk.Menu()
        group = None
        if show_activated is False:
            for value in sorted(value_list):
                if suffix != None:
                    menuitem = gtk.RadioMenuItem(group, str(value) + " " + \
                        suffix)
                else:
                    menuitem = gtk.RadioMenuItem(group, str(value))
            
                group = menuitem

                if value == pref_value and pref_value != None:
                    menuitem.set_active(True)

                if callback != None:
                    menuitem.connect("toggled", callback)

                menu.append(menuitem)

        if show_activated is True:
            for value in sorted(value_list):
                menuitem = gtk.RadioMenuItem(group, str(activated_label))
            
                group = menuitem

                if value == pref_value and pref_value != None:
                    menuitem.set_active(True)

                if callback != None:
                    menuitem.connect("toggled", callback)

                menu.append(menuitem)

        if show_notset:
            menuitem = gtk.RadioMenuItem(group, notset_label)
            if pref_value < notset_lessthan and pref_value != None:
                menuitem.set_active(True)
            if show_activated and pref_value == 1:
                menuitem.set_active(True)
            menuitem.connect("toggled", callback)
            menu.append(menuitem)
            
        # Add the Other... menuitem
        if show_other is True:
            menuitem = gtk.SeparatorMenuItem()
            menu.append(menuitem)
            menuitem = gtk.MenuItem(_("Other..."))
            menuitem.connect("activate", callback)
            menu.append(menuitem)
                    
        return menu
        
    def tray_setbwdown(self, widget, data=None):    
        self.setbwlimit(widget, _("Download"), "max_download_speed", 
            "tray_download_speed_list")
        
    def tray_setbwup(self, widget, data=None):
        self.setbwlimit(widget, _("Upload"), "max_upload_speed",
            "tray_upload_speed_list")
                
    def setbwlimit(self, widget, string, core_key, ui_key):
        """Sets the bandwidth limit based on the user selection."""
        value = widget.get_children()[0].get_text().rstrip(" " + 
                        _("KiB/s"))
        if value == _("Unlimited"):
            value = -1
        
        if value == _("Other..."):
            dialog_glade = gtk.glade.XML(
                pkg_resources.resource_filename("deluge.ui.gtkui", 
                                            "glade/dgtkpopups.glade"))
            speed_dialog = dialog_glade.get_widget("speed_dialog")
            spin_title = dialog_glade.get_widget("spin_title")
            spin_title.set_text(_("%s Speed (KiB/s):" % string))
            spin_speed = dialog_glade.get_widget("spin_speed")
            spin_speed.set_value(
                client.get_config_value(core_key))
            spin_speed.select_region(0, -1)
            response = speed_dialog.run()
            if response == 1: # OK Response
                value = spin_speed.get_value()
            else:
                speed_dialog.destroy()
                return
            speed_dialog.destroy()
        
        # Set the config in the core
        value = float(value)
        config_to_set = {core_key: value}
        client.set_config(config_to_set)

        # Update the tray speed limit list
        if value not in self.config[ui_key] and value >= 0:
            # We prepend this value and remove the last value in the list
            self.config[ui_key].insert(0, value)
            self.config[ui_key].pop()
            # Re-build the menu
            self.build_tray_bwsetsubmenu()
            # Update the UI
            self.window.update()
            
    def unlock_tray(self, comingnext, is_showing_dlg=[False]):
        import sha
        log.debug("Show tray lock dialog")
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
            if self.config["tray_password"] == sha.new(entered_pass.get_text())\
                .hexdigest():
                if comingnext == "mainwinshow":
                    log.debug("Showing main window via tray")
                    self.window.show()
                elif comingnext == "quitdaemon":
                    client.shutdown()
                    self.window.hide()
                    self.window.quit()
                elif comingnext == "quitui":
                    log.debug("Quiting UI via tray")
                    self.window.hide()
                    self.window.quit()
        tray_lock.destroy()
        is_showing_dlg[0] = False
        return True

