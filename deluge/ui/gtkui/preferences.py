#
# preferences.py
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

import pygtk
pygtk.require('2.0')
import gtk, gtk.glade
import pkg_resources

from deluge.log import LOG as log
import deluge.ui.functions as functions

class Preferences:
    def __init__(self, window):
        self.window = window
        self.glade = gtk.glade.XML(
                    pkg_resources.resource_filename("deluge.ui.gtkui",
                                            "glade/preferences_dialog.glade"))
        self.pref_dialog = self.glade.get_widget("pref_dialog")
        self.treeview = self.glade.get_widget("treeview")
        self.notebook = self.glade.get_widget("notebook")
        self.core = functions.get_core()
        # Setup the liststore for the categories (tab pages)
        self.liststore = gtk.ListStore(int, str)
        self.treeview.set_model(self.liststore)
        render = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Categories", render, text=1)
        self.treeview.append_column(column)
        # Add the default categories
        i = 0
        for category in ["Downloads", "Network", "Bandwidth", "Other", 
            "Plugins"]:
            self.liststore.append([i, category])
            i += 1

        # Connect to the 'changed' event of TreeViewSelection to get selection
        # changes.
        self.treeview.get_selection().connect("changed", 
                                    self.on_selection_changed)
        
        self.glade.signal_autoconnect({
            "on_pref_dialog_delete_event": self.on_pref_dialog_delete_event,
            "on_button_ok_clicked": self.on_button_ok_clicked,
            "on_button_apply_clicked": self.on_button_apply_clicked,
            "on_button_cancel_clicked": self.on_button_cancel_clicked,
            "on_radio_save_all_to_toggled": self.on_toggle
        })
    
    def add_page(self, name, widget):
        """Add a another page to the notebook"""
        index = self.notebook.append_page(widget)
        self.liststore.append([index, name])
        
    def get_config(self):
        """Get the configuration from the core."""
        # Get the config dictionary from the core
        self.config = functions.get_config(self.core)
        
    def show(self):
        self.get_config()
        # Update the preferences dialog to reflect current config settings
        
        ## Downloads tab ##
        # FIXME: Add GtkUI specific prefs here
        # Core specific options for Downloads tab
        
        # This one will need to be re-evaluated if the core is running on a 
        # different machine.. We won't be able to use the local file browser to
        # choose a download location.. It will be specific to the machine core
        # is running on.
        self.glade.get_widget("download_path_button").set_filename(
            self.config["download_location"])
        self.glade.get_widget("radio_compact_allocation").set_active(
            self.config["compact_allocation"])
        self.glade.get_widget("radio_full_allocation").set_active(
            not self.config["compact_allocation"])
        self.glade.get_widget("chk_prioritize_first_last_pieces").set_active(
            self.config["prioritize_first_last_pieces"])
        
        ## Network tab ##
        self.glade.get_widget("spin_port_min").set_value(
            self.config["listen_ports"][0])
        self.glade.get_widget("spin_port_max").set_value(
            self.config["listen_ports"][1])
        self.glade.get_widget("active_port_label").set_text(
            str(functions.get_listen_port(self.core)))
        self.glade.get_widget("chk_random_port").set_active(
            self.config["random_port"])
        self.glade.get_widget("chk_dht").set_active(
            self.config["dht"])
        self.glade.get_widget("chk_upnp").set_active(
            self.config["upnp"])
        self.glade.get_widget("chk_natpmp").set_active(
            self.config["natpmp"])
        self.glade.get_widget("chk_utpex").set_active(
            self.config["utpex"])
        self.glade.get_widget("combo_encin").set_active(
            self.config["enc_in_policy"])
        self.glade.get_widget("combo_encout").set_active(
            self.config["enc_out_policy"])
        self.glade.get_widget("combo_enclevel").set_active(
            self.config["enc_level"])
        self.glade.get_widget("chk_pref_rc4").set_active(
            self.config["enc_prefer_rc4"])
            
        ## Bandwidth tab ##
        self.glade.get_widget("spin_max_connections_global").set_value(
            self.config["max_connections_global"])
        self.glade.get_widget("spin_max_download").set_value(
            self.config["max_download_speed"])
        self.glade.get_widget("spin_max_upload").set_value(
            self.config["max_upload_speed"])
        self.glade.get_widget("spin_max_upload_slots_global").set_value(
            self.config["max_upload_slots_global"])
        self.glade.get_widget("spin_max_connections_per_torrent").set_value(
            self.config["max_connections_per_torrent"])
        self.glade.get_widget("spin_max_upload_slots_per_torrent").set_value(
            self.config["max_upload_slots_per_torrent"])

        ## Other tab ##
        # All of it is UI only.
        
        # Now show the dialog
        self.pref_dialog.show()
    
    def set_config(self):
        """Sets all altered config values in the core"""
        # Get the values from the dialog
        new_config = {}
        ## Downloads tab ##
        new_config["download_location"] = \
            self.glade.get_widget("download_path_button").get_filename()
        new_config["compact_allocation"] = \
            self.glade.get_widget("radio_compact_allocation").get_active()
        new_config["prioritize_first_last_pieces"] = \
            self.glade.get_widget(
                "chk_prioritize_first_last_pieces").get_active()

        ## Network tab ##
        listen_ports = []
        listen_ports.append(
            self.glade.get_widget("spin_port_min").get_value_as_int())
        listen_ports.append(
            self.glade.get_widget("spin_port_max").get_value_as_int())
        new_config["listen_ports"] = listen_ports
        new_config["random_port"] = \
            self.glade.get_widget("chk_random_port").get_active()
        new_config["dht"] = self.glade.get_widget("chk_dht").get_active()
        new_config["upnp"] = self.glade.get_widget("chk_upnp").get_active()
        new_config["natpmp"] = self.glade.get_widget("chk_natpmp").get_active()
        new_config["utpex"] = self.glade.get_widget("chk_utpex").get_active()
        new_config["enc_in_policy"] = \
            self.glade.get_widget("combo_encin").get_active()
        new_config["enc_out_policy"] = \
            self.glade.get_widget("combo_encout").get_active()
        new_config["enc_level"] = \
            self.glade.get_widget("combo_enclevel").get_active()
        new_config["enc_prefer_rc4"] = \
            self.glade.get_widget("chk_pref_rc4").get_active()
        
        ## Bandwidth tab ##
        new_config["max_connections_global"] = \
            self.glade.get_widget(
                "spin_max_connections_global").get_value_as_int()
        new_config["max_download_speed"] = \
            self.glade.get_widget("spin_max_download").get_value()
        new_config["max_upload_speed"] = \
            self.glade.get_widget("spin_max_upload").get_value()
        new_config["max_upload_slots_global"] = \
            self.glade.get_widget(
                "spin_max_upload_slots_global").get_value_as_int()
        new_config["max_connections_per_torrent"] = \
            self.glade.get_widget(
                "spin_max_connections_per_torrent").get_value_as_int()
        new_config["max_upload_slots_per_torrent"] = \
            self.glade.get_widget(
                "spin_max_upload_slots_per_torrent").get_value_as_int()
        
        config_to_set = {}
        for key in new_config.keys():
            # The values do not match so this needs to be updated
            if self.config[key] != new_config[key]:
                config_to_set[key] = new_config[key]

        # Set each changed config value in the core
        functions.set_config(config_to_set, self.core)

        # Update the configuration
        self.config.update(config_to_set)
        
    def hide(self):
        self.pref_dialog.hide()
    
    def on_pref_dialog_delete_event(self, widget, event):
        self.hide()
        return True
    
    def on_toggle(self, widget):
        """Handles widget sensitivity based on radio/check button values."""
        value = widget.get_active()
        if widget == self.glade.get_widget('radio_save_all_to'):
            self.glade.get_widget('download_path_button').set_sensitive(value)
            
    def on_button_ok_clicked(self, data):
        log.debug("on_button_ok_clicked")
        self.set_config()
        self.hide()
        return True

    def on_button_apply_clicked(self, data):
        log.debug("on_button_apply_clicked")
        self.set_config()

    def on_button_cancel_clicked(self, data):
        log.debug("on_button_cancel_clicked")
        self.hide()
        return True
        
    def on_selection_changed(self, treeselection):
        # Show the correct notebook page based on what row is selected.
        (model, row) = treeselection.get_selected()
        self.notebook.set_current_page(model.get_value(row, 0))

