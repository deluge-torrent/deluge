#
# torrentdetails.py
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
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
#   The Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor
#   Boston, MA  02110-1301, USA.
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


"""The torrent details component shows info about the selected torrent."""

import gtk, gtk.glade
import os
import os.path
import cPickle

import deluge.component as component
from deluge.ui.client import client
from deluge.configmanager import ConfigManager
import deluge.configmanager

from deluge.log import LOG as log

class Tab:
    def __init__(self):
        self.is_visible = True
        self.position = -1
        self.weight = -1

    def get_name(self):
        return self._name

    def get_child_widget(self):
        parent = self._child_widget.get_parent()
        if parent is not None:
            parent.remove(self._child_widget)

        return self._child_widget

    def get_tab_label(self):
        parent = self._tab_label.get_parent()
        log.debug("parent: %s", parent)
        if parent is not None:
            parent.remove(self._tab_label)

        return self._tab_label

class TorrentDetails(component.Component):
    def __init__(self):
        component.Component.__init__(self, "TorrentDetails", interval=2)
        self.window = component.get("MainWindow")
        glade = self.window.main_glade

        self.notebook = glade.get_widget("torrent_info")

        # This is the menu item we'll attach the tabs checklist menu to
        self.menu_tabs = glade.get_widget("menu_tabs")

        self.notebook.connect("switch-page", self._on_switch_page)

        # Tabs holds references to the Tab objects by their name
        self.tabs = {}

        # Add the default tabs
        from status_tab import StatusTab
        from details_tab import DetailsTab
        from files_tab import FilesTab
        from peers_tab import PeersTab
        from options_tab import OptionsTab

        default_tabs = {
            "Status": StatusTab,
            "Details": DetailsTab,
            "Files": FilesTab,
            "Peers": PeersTab,
            "Options": OptionsTab
            }

        # tab_name, visible
        default_order = [
            ("Status", True),
            ("Details", True),
            ("Files", True),
            ("Peers", True),
            ("Options", True)
        ]

        self.translate_tabs = {
            "All"     : _("_All"),
            "Status"  : _("_Status"),
            "Details" : _("_Details"),
            "Files"   : _("_Files"),
            "Peers"   : _("_Peers"),
            "Options" : _("_Options")
          }

        # Get the state from saved file
        state = self.load_state()

        if state:
            for item in state:
                if not isinstance(item, tuple):
                    log.debug("Old tabs.state, using default..")
                    state = None
                    break

        # The state is a list of tab_names in the order they should appear
        if state == None:
            # Set the default order
            state = default_order

        # We need to rename the tab in the state for backwards compat
        self.state = [(tab_name.replace("Statistics", "Status"), visible) for
                       tab_name, visible in state]

        for tab in default_tabs.itervalues():
            self.add_tab(tab(), generate_menu=False)

        # Generate the checklist menu
        self.generate_menu()

    def tab_insert_position(self, weight):
        """Returns the position a tab with a given weight should be inserted in"""
        # Determine insert position based on weight
        # weights is a list of visible tab names in weight order

        weights = [(tab.weight, name) for name, tab in self.tabs.iteritems() if tab.is_visible]

        weights.sort()
        log.debug("weights: %s", weights)
        log.debug("weight of tab: %s", weight)

        position = -1
        for w, name in weights:
            if w >= weight:
                position = self.tabs[name].position
                log.debug("Found pos %d" % position)
                break
        return position


    def add_tab(self, tab, generate_menu=True, visible=None):
        name = tab.get_name()

        #find position of tab in self.state, this is the tab weight
        weight = None
        for w, item in enumerate(self.state):
            if item[0] == name:
                weight = w
                if visible is None:
                    visible = item[1]
                break

        if weight is None:
            if visible is None:
                visible = True
            weight = len(self.state)
            self.state.append((name, visible))

        tab.weight = weight

        if visible:
            tab.is_visible = True
            #add the tab at position guided by the weight
            insert_pos = self.tab_insert_position(weight)
            log.debug("Trying to insert tab at %d" % insert_pos)
            pos = self.notebook.insert_page(
                tab.get_child_widget(),
                tab.get_tab_label(),
                insert_pos)
            log.debug("Tab inserted at %d" % pos)
            tab.position = pos
            if not self.notebook.get_property("visible"):
                # If the notebook isn't visible, show it
                self.visible(True)
        else:
            tab.is_visible = False

        self.tabs[name] = tab
        if name not in self.translate_tabs:
            self.translate_tabs[name] = _(name)

        self.regenerate_positions()
        if generate_menu:
            self.generate_menu()


    def regenerate_positions(self):
        """This will sync up the positions in the tab, with the position stored
        in the tab object"""
        for tab in self.tabs:
            page_num = self.notebook.page_num(self.tabs[tab]._child_widget)
            if page_num > -1:
                self.tabs[tab].position = page_num

    def remove_tab(self, tab_name):
        """Removes a tab by name."""
        self.notebook.remove_page(self.tabs[tab_name].position)
        del self.tabs[tab_name]
        self.regenerate_positions()
        self.generate_menu()

        # If there are no tabs visible, then do not show the notebook
        if len(self.tabs) == 0:
            self.visible(False)

    def hide_all_tabs(self):
        """Hides all tabs"""
        log.debug("n_pages: %s", self.notebook.get_n_pages())
        for n in xrange(self.notebook.get_n_pages() - 1, -1, -1):
            self.notebook.remove_page(n)

        for tab in self.tabs:
            self.tabs[tab].is_visible = False
        log.debug("n_pages: %s", self.notebook.get_n_pages())
        self.generate_menu()
        self.visible(False)

    def show_all_tabs(self):
        """Shows all tabs"""
        for tab in self.tabs:
            if not self.tabs[tab].is_visible:
                self.show_tab(tab, generate_menu=False)
        self.generate_menu()

    def hide_tab(self, tab_name):
        """Hides tab by name"""
        self.tabs[tab_name].is_visible = False
        self.notebook.remove_page(self.tabs[tab_name].position)
        self.regenerate_positions()
        self.generate_menu()

        show = False
        for name, tab in self.tabs.iteritems():
            show = show or tab.is_visible

        self.visible(show)

    def show_tab(self, tab_name, generate_menu=True):
        log.debug("%s\n%s\n%s", self.tabs[tab_name].get_child_widget(),
            self.tabs[tab_name].get_tab_label(),
            self.tabs[tab_name].position)

        position = self.tab_insert_position(self.tabs[tab_name].weight)

        log.debug("position: %s", position)
        self.notebook.insert_page(
            self.tabs[tab_name].get_child_widget(),
            self.tabs[tab_name].get_tab_label(),
            position)
        self.tabs[tab_name].is_visible = True
        self.regenerate_positions()
        if generate_menu:
            self.generate_menu()
        self.visible(True)

    def generate_menu(self):
        """Generates the checklist menu for all the tabs and attaches it"""
        menu = gtk.Menu()
        # Create 'All' menuitem and a separator
        menuitem = gtk.CheckMenuItem(self.translate_tabs["All"], True)
        menuitem.set_name("All")

        all_tabs = True
        for key in self.tabs:
            if not self.tabs[key].is_visible:
                all_tabs = False
                break
        menuitem.set_active(all_tabs)
        menuitem.connect("toggled", self._on_menuitem_toggled)

        menu.append(menuitem)

        menuitem = gtk.SeparatorMenuItem()
        menu.append(menuitem)

        # Create a list in order of tabs to create menu
        menuitem_list = []
        for tab_name in self.tabs:
            menuitem_list.append((self.tabs[tab_name].weight, tab_name))
        menuitem_list.sort()

        for pos, name in menuitem_list:
            menuitem = gtk.CheckMenuItem(self.translate_tabs[name], True)
            menuitem.set_name(name)
            menuitem.set_active(self.tabs[name].is_visible)
            menuitem.connect("toggled", self._on_menuitem_toggled)
            menu.append(menuitem)

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
        if visible and not self.tabs[tab_name].is_visible:
            self.show_tab(tab_name)
        elif not visible and self.tabs[tab_name].is_visible:
            self.hide_tab(tab_name)

    def start(self):
        for tab in self.tabs.values():
            try:
                tab.start()
            except AttributeError:
                pass

    def stop(self):
        self.clear()
        for tab in self.tabs.values():
            try:
                tab.stop()
            except AttributeError:
                pass


    def shutdown(self):
        # Save the state of the tabs
        for tab in self.tabs:
            try:
                self.tabs[tab].save_state()
            except AttributeError:
                pass

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
                name = None
                for tab in self.tabs:
                    if self.tabs[tab].position == page_num and self.tabs[tab].is_visible:
                        name = tab
            except IndexError:
                return
            # Update the tab that is in view
            if name:
                self.tabs[name].update()

    def clear(self):
        # Get the tab name
        try:
            page_num = self.notebook.get_current_page()
            name = None
            for tab in self.tabs:
                if self.tabs[tab].position == page_num and self.tabs[tab].is_visible:
                    name = tab
            if name:
                self.tabs[name].clear()
        except Exception, e:
            log.debug("Unable to clear torrentdetails: %s", e)

    def _on_switch_page(self, notebook, page, page_num):
        self.update(page_num)
        client.force_call(False)

    def _on_menuitem_toggled(self, widget):
        # Get the tab name
        name = widget.get_name()
        if name == "All":
            if widget.get_active():
                self.show_all_tabs()
            else:
                self.hide_all_tabs()
            return

        self.set_tab_visible(name, widget.get_active())

    def save_state(self):
        """We save the state, which is basically the tab_index list"""
        filename = "tabs.state"

        #Update the visiblity status of all tabs
        #Leave tabs we dont know anything about it the state as they
        #might come from a plugin
        for i, (name, visible) in enumerate(self.state):
            log.debug("Testing name: %s" % name)
            if name in self.tabs:
                self.state[i] = (name, self.tabs[name].is_visible)
                log.debug("Set to %s %d" % self.state[i])
        state = self.state

        # Get the config location for saving the state file
        config_location = deluge.configmanager.get_config_dir()

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
        config_location = deluge.configmanager.get_config_dir()
        state = None

        try:
            log.debug("Loading TorrentDetails state file: %s", filename)
            state_file = open(os.path.join(config_location, filename), "rb")
            state = cPickle.load(state_file)
            state_file.close()
        except (EOFError, IOError, cPickle.UnpicklingError), e:
            log.warning("Unable to load state file: %s", e)

        return state
