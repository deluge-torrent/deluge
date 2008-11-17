#
# gtkui.py
#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007, 2008 Andrew Resch ('andar') <andrewresch@gmail.com>
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

import gtk
import gobject
from gtk.glade import XML

import graph
from deluge import component
from deluge.log import LOG as log
from deluge.common import fspeed
from deluge.ui.client import aclient
from deluge.ui.gtkui.torrentdetails import Tab

class GraphsTab(Tab):
    def __init__(self, glade):
        Tab.__init__(self)
        self._name = 'Graphs'
        self.glade = glade
        self.window = self.glade.get_widget('graph_tab')
        self.notebook = self.glade.get_widget('graph_notebook')
        self.label = self.glade.get_widget('graph_label')
        self.bandwidth_graph = self.glade.get_widget('bandwidth_graph')
        self.bandwidth_graph.connect('expose_event', self.bandwidth_expose)
        self.window.unparent()
        self.label.unparent()

    def bandwidth_expose(self, widget, event):
        self.graph_widget = self.bandwidth_graph
        self.graph = graph.Graph()
        self.graph.add_stat('download_rate', label='Download Rate', color=graph.green)
        self.graph.add_stat('upload_rate', label='Upload Rate', color=graph.blue)
        self.graph.set_left_axis(formatter=fspeed, min=10240)
        self.update_timer = gobject.timeout_add(2000, self.update_graph)
        self.update_graph()

    def update_graph(self):
        width, height = self.graph_widget.allocation.width, self.graph_widget.allocation.height
        context = self.graph_widget.window.cairo_create()
        self.graph.async_request()
        aclient.force_call(True)
        self.graph.draw_to_context(context, width, height)
        return True

class GtkUI(object):
    def __init__(self, plugin_api, plugin_name):
        log.debug("Calling Stats UI init")
        self.plugin = plugin_api

    def enable(self):
        self.glade = XML(self.get_resource("config.glade"))
        self.plugin.add_preferences_page("Stats", self.glade.get_widget("prefs_box"))
        self.plugin.register_hook("on_apply_prefs", self.on_apply_prefs)
        self.plugin.register_hook("on_show_prefs", self.on_show_prefs)
        self.on_show_prefs()

        self.graphs_tab = GraphsTab(XML(self.get_resource("tabs.glade")))
        self.torrent_details = component.get('TorrentDetails')
        self.torrent_details.notebook.append_page(self.graphs_tab.window, self.graphs_tab.label)

    def disable(self):
        self.plugin.remove_preferences_page("Stats")
        self.plugin.deregister_hook("on_apply_prefs", self.on_apply_prefs)
        self.plugin.deregister_hook("on_show_prefs", self.on_show_prefs)

    def on_apply_prefs(self):
        log.debug("applying prefs for Stats")
        config = {
            "test":self.glade.get_widget("txt_test").get_text()
        }
        aclient.stats_set_config(None, config)

    def on_show_prefs(self):
        aclient.stats_get_config(self.cb_get_config)

    def cb_get_config(self, config):
        "callback for on show_prefs"
        self.glade.get_widget("txt_test").set_text(config["test"])

    def get_resource(self, filename):
        import pkg_resources, os
        return pkg_resources.resource_filename("stats", os.path.join("data", filename))
