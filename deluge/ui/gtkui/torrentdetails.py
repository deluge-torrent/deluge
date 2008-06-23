#
# torrentdetails.py
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

"""The torrent details component shows info about the selected torrent."""

import gtk, gtk.glade
import os
import os.path
import cPickle

import deluge.component as component
from deluge.ui.client import aclient as client
from deluge.configmanager import ConfigManager

from deluge.log import LOG as log

class Tab:
    def __init__(self):
        pass
        
    def get_name(self):
        return self._name
    
    def get_child_widget(self):
        parent = self._child_widget.get_parent()
        if parent is not None:
            parent.remove(self._child_widget)
            
        return self._child_widget
        
    def get_tab_label(self):
        parent = self._tab_label.get_parent()
        if parent is not None:
            parent.remove(self._tab_label)
            
        return self._tab_label
        
class TorrentDetails(component.Component):
    def __init__(self):
        component.Component.__init__(self, "TorrentDetails", interval=2000)
        self.window = component.get("MainWindow")
        glade = self.window.main_glade
        
        self.notebook = glade.get_widget("torrent_info")

        # This is the menu item we'll attach the tabs checklist menu to
        self.menu_tabs = glade.get_widget("menu_tabs")
        
        self.notebook.connect("switch-page", self._on_switch_page)

        # Tab index is a list of tab names in the order which they presented
        # to the user.
        self.tab_index = []
        
        # Tabs holds references to the Tab objects by their name
        self.tabs = {}
        
        # tab_name: (tab_object, position)
        self.hidden_tabs = {}

        # Add the default tabs
        from statistics_tab import StatisticsTab
        from details_tab import DetailsTab
        from files_tab import FilesTab
        from peers_tab import PeersTab
        from options_tab import OptionsTab

        default_tabs = {
            "Statistics": StatisticsTab,
            "Details": DetailsTab,
            "Files": FilesTab,
            "Peers": PeersTab,
            "Options": OptionsTab
            }
        
        default_order = [
            "Statistics",
            "Details",
            "Files",
            "Peers",
            "Options"            
        ]
        
        # Get the state from saved file
        state = self.load_state()
        
        # The state is a list of tab_names in the order they should appear
        if state == None:
            # Set the default order
            state = default_order
        
        # Add the tabs in the order from the state
        for tab_name in state:
            self.add_tab(default_tabs[tab_name]())
    
        if len(state) < len(default_order):
            # We have hidden tabs and need to add them to the hidden_tabs dict
            for i, tab_name in enumerate(default_order):
                if tab_name not in state:
                    self.hidden_tabs[tab_name] = (default_tabs[tab_name](), i)
         
        # Generate the checklist menu
        self.generate_menu()
                    
    def add_tab(self, tab_object, position=-1, generate_menu=True):
        """Adds a tab object to the notebook."""
        self.tabs[tab_object.get_name()] = tab_object
        pos = self.notebook.insert_page(
            tab_object.get_child_widget(),
            tab_object.get_tab_label(),
            position)
        self.tab_index.insert(pos, tab_object.get_name())
        if generate_menu:
            self.generate_menu()
        
        if not self.notebook.get_property("visible"):
            # If the notebook isn't visible, show it
            self.visible(True)
    
    def remove_tab(self, tab_name):
        """Removes a tab by name."""
        index = self.tab_index.index(tab_name)
        self.notebook.remove_page(index)
        del self.tabs[tab_name]
        del self.tab_index[index]
        self.generate_menu()
        
        # If there are no tabs visible, then do not show the notebook
        if len(self.tabs) == 0:
            self.visible(False)
        
    def generate_menu(self):
        """Generates the checklist menu for all the tabs and attaches it"""
        menu = gtk.Menu()
        # Create 'All' menuitem and a separator
        menuitem = gtk.CheckMenuItem("All")
        menuitem.connect("toggled", self._on_menuitem_toggled)
        if len(self.hidden_tabs) > 0:
            menuitem.set_active(False)
        else:
            menuitem.set_active(True)

        menu.append(menuitem)
        
        menuitem = gtk.SeparatorMenuItem()
        menu.append(menuitem)
        
        # Add all the tabs to the menu
        for tab in self.tab_index:
            menuitem = gtk.CheckMenuItem(tab)
            menuitem.connect("toggled", self._on_menuitem_toggled)
            menuitem.set_active(True)
            menu.append(menuitem)
        
        # Add all hidden_tabs to the menu too
        for tab in self.hidden_tabs.keys():
            menuitem = gtk.CheckMenuItem(tab)
            menuitem.connect("toggled", self._on_menuitem_toggled)
            menuitem.set_active(False)
            # Try to keep position in sync
            menu.insert(menuitem, self.hidden_tabs[tab][1] + 2)
        
        self.menu_tabs.set_submenu(menu)
        self.menu_tabs.show_all()
        
    def visible(self, visible):
        if visible:
            self.notebook.show()
        else:
            self.notebook.hide()
            self.window.vpaned.set_position(-1)
    
    def set_tab_visible(self, tab_name, visible):
        """Sets the tab to visible"""
        log.debug("set_tab_visible name: %s visible: %s", tab_name, visible)
        if visible:
            # We need to show tab, make sure it's not already shown
            if tab_name not in self.hidden_tabs.keys():
                return
            # Add the tab back to the notebook
            self.add_tab(self.hidden_tabs[tab_name][0], self.hidden_tabs[tab_name][1], generate_menu=False)
            del self.hidden_tabs[tab_name]
        else:
            # Check to see if tab is already hidden
            if tab_name in self.hidden_tabs.keys():
                return
            # Remove the tab from the notebook and store it in hidden_tabs
            self.hidden_tabs[tab_name] = (self.tabs[tab_name], self.tab_index.index(tab_name))
            self.remove_tab(tab_name)
                         
    def stop(self):
        # Save the state of the tabs
        for tab in self.tabs:
            try:
                self.tabs[tab].save_state()
            except AttributeError:
                pass
            
        self.clear()
        # Save tabs state
        self.save_state()

    def update(self, page_num=None):
        if len(component.get("TorrentView").get_selected_torrents()) == 0:
            # No torrents selected, so just clear
            self.clear()
        
        if self.notebook.get_property("visible"):
            if page_num == None:
                page_num = self.notebook.get_current_page()
            try:
                # Get the tab name
                name = self.tab_index[page_num]
            except IndexError:
                return
            # Update the tab that is in view
            log.debug("tab_name: %s", name)
            self.tabs[name].update()
                    
    def clear(self):
        # Get the tab name
        try:
            name = self.tab_index[self.notebook.get_current_page()]
            self.tabs[name].clear()
        except Exception, e:
            log.debug("Unable to clear torrentdetails: %s", e)

    def _on_switch_page(self, notebook, page, page_num):
        self.update(page_num)
        client.force_call(False)

    def _on_menuitem_toggled(self, widget):
        # Get the tab name
        name = widget.get_child().get_text()
        if name == "All":
            if self.menu_tabs.get_submenu() is not None:
                # Widget has been changed to active which means we need to 
                # show all the tabs.
                for tab in self.menu_tabs.get_submenu().get_children():
                    if isinstance(tab, gtk.SeparatorMenuItem):
                        continue
                    if tab.get_child().get_text() == "All" or tab is gtk.SeparatorMenuItem:
                        continue
                    
                    tab.set_active(widget.get_active())
            return
                
        self.set_tab_visible(name, widget.get_active())
        
    def save_state(self):
        """We save the state, which is basically the tab_index list"""
        filename = "tabs.state"
        state = self.tab_index
        
        # Get the config location for saving the state file
        config_location = ConfigManager("gtkui.conf")["config_location"]

        try:
            log.debug("Saving TorrentDetails state file: %s", filename)
            state_file = open(os.path.join(config_location, filename), "wb")
            cPickle.dump(state, state_file)
            state_file.close()
        except IOError, e:
            log.warning("Unable to save state file: %s", e)

    def load_state(self):
        filename = "tabs.state"
        # Get the config location for loading the state file
        config_location = ConfigManager("gtkui.conf")["config_location"]
        state = None
        
        try:
            log.debug("Loading TorrentDetails state file: %s", filename)
            state_file = open(os.path.join(config_location, filename), "rb")
            state = cPickle.load(state_file)
            state_file.close()
        except (EOFError, IOError), e:
            log.warning("Unable to load state file: %s", e)
        
        return state
