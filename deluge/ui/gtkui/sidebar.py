#
# sidebar.py
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
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
import gtk.glade

import deluge.component as component
import deluge.common
from deluge.configmanager import ConfigManager
from deluge.log import LOG as log

class SideBar(component.Component):
    """
    manages the sidebar-tabs.
    purpose : plugins
    """
    def __init__(self):
        component.Component.__init__(self, "SideBar")
        self.window = component.get("MainWindow")
        glade = self.window.main_glade
        self.notebook = glade.get_widget("sidebar_notebook")
        self.hpaned = glade.get_widget("hpaned")
        self.config = ConfigManager("gtkui.conf")
        #self.hpaned_position = self.hpaned.get_position()

        # Tabs holds references to the Tab widgets by their name
        self.tabs = {}

        # Hide if necessary
        self.visible(self.config["show_sidebar"])

    def shutdown(self):
        log.debug("hpaned.position: %s", self.hpaned.get_position())
        self.config["sidebar_position"] = self.hpaned.get_position()

    def visible(self, visible):
        if visible:
            if self.config["sidebar_position"]:
                self.hpaned.set_position(self.config["sidebar_position"])
            self.notebook.show()
        else:
            self.notebook.hide()
            # Store the position for restoring upon show()
            self.config["sidebar_position"] = self.hpaned.get_position()
            self.hpaned.set_position(-1)

        self.config["show_sidebar"] = visible

    def add_tab(self, widget, tab_name, label):
        """Adds a tab object to the notebook."""
        log.debug("add tab:%s" % tab_name )
        self.tabs[tab_name] = widget
        scrolled = gtk.ScrolledWindow()
        scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled.add(widget)
        pos = self.notebook.insert_page(scrolled, gtk.Label(label), -1)
        scrolled.show_all()

        self.after_update()

    def remove_tab(self, tab_name):
        """Removes a tab by name."""
        self.notebook.remove_page(self.notebook.page_num(self.tabs[tab_name]))
        del self.tabs[tab_name]

        self.after_update()

    def after_update(self):
        # If there are no tabs visible, then do not show the notebook
        if len(self.tabs) == 0:
            self.visible(False)

        # If there is 1 tab, hide the tab-headers
        if len(self.tabs) == 1:
            self.notebook.set_show_tabs(False)
        else:
            self.notebook.set_show_tabs(True)


