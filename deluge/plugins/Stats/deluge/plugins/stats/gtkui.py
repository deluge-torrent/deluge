#
# gtkui.py
#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
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
import logging
from gtk.glade import XML

from twisted.internet import defer

import graph
from deluge import component
from deluge.common import fspeed
from deluge.ui.client import client
from deluge.ui.gtkui.torrentdetails import Tab
from deluge.plugins.pluginbase import GtkPluginBase

log = logging.getLogger(__name__)

class GraphsTab(Tab):
    def __init__(self, glade):
        Tab.__init__(self)
        self._name = 'Graphs'
        self.glade = glade
        self.window = self.glade.get_widget('graph_tab')
        self._child_widget = self.window
        self.notebook = self.glade.get_widget('graph_notebook')
        self.label = self.glade.get_widget('graph_label')
        self._tab_label = self.label
        self.bandwidth_graph = self.glade.get_widget('bandwidth_graph')
        self.bandwidth_graph.connect('expose_event', self.expose)
        self.window.unparent()
        self.label.unparent()

        self.graph_widget = self.bandwidth_graph
        self.graph = graph.Graph()
        self.graph.add_stat('payload_download_rate', label='Download Rate', color=graph.green)
        self.graph.add_stat('payload_upload_rate', label='Upload Rate', color=graph.blue)
        self.graph.set_left_axis(formatter=fspeed, min=10240)

    def expose(self, widget, event):
        """Redraw"""
        context = self.graph_widget.window.cairo_create()
        # set a clip region
        context.rectangle(event.area.x, event.area.y,
                           event.area.width, event.area.height)
        context.clip()

        width, height = self.graph_widget.allocation.width, self.graph_widget.allocation.height
        self.graph.draw_to_context(context, width, height)
        #Do not propagate the event
        return False

    def update(self):
        log.debug("getstat keys: %s", self.graph.stat_info.keys())
        d1 = client.stats.get_stats(self.graph.stat_info.keys())
        d1.addCallback(self.graph.set_stats)
        d2 = client.stats.get_config()
        d2.addCallback(self.graph.set_config)
        dl = defer.DeferredList([d1, d2])

        def _on_update(result):
            width, height = self.graph_widget.allocation.width, self.graph_widget.allocation.height
            rect = gtk.gdk.Rectangle(0, 0, width, height)
            self.graph_widget.window.invalidate_rect(rect, True)

        dl.addCallback(_on_update)

    def clear(self):
        pass



class GtkUI(GtkPluginBase):
    def enable(self):
        log.debug("Stats plugin enable called")
        self.glade = XML(self.get_resource("config.glade"))
        component.get("Preferences").add_page("Stats", self.glade.get_widget("prefs_box"))
        component.get("PluginManager").register_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").register_hook("on_show_prefs", self.on_show_prefs)
        self.on_show_prefs()

        self.graphs_tab = GraphsTab(XML(self.get_resource("tabs.glade")))
        self.torrent_details = component.get('TorrentDetails')
        self.torrent_details.add_tab(self.graphs_tab)

    def disable(self):
        component.get("Preferences").remove_page("Stats")
        component.get("PluginManager").deregister_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").deregister_hook("on_show_prefs", self.on_show_prefs)
        self.torrent_details.remove_tab(self.graphs_tab.get_name())

    def on_apply_prefs(self):
        log.debug("applying prefs for Stats")
        config = {
            "test":self.glade.get_widget("txt_test").get_text()
        }
        client.stats.set_config(config)

    def on_show_prefs(self):
        client.stats.get_config().addCallback(self.cb_get_config)

    def cb_get_config(self, config):
        "callback for on show_prefs"
        self.glade.get_widget("txt_test").set_text(config["test"])

    def get_resource(self, filename):
        import pkg_resources, os
        return pkg_resources.resource_filename(
            "deluge.plugins.stats", os.path.join("data", filename)
        )
