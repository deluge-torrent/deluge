# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Ian Martin <ianmartin@cantab.net>
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2008 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging

import gtk
import gtk.glade
from gtk.glade import XML

import deluge
from deluge import component
from deluge.common import fspeed
from deluge.plugins.pluginbase import GtkPluginBase
from deluge.ui.client import client
from deluge.ui.gtkui.torrentdetails import Tab

from . import common
from .graph import Graph, size_formatter_scale

log = logging.getLogger(__name__)

DEFAULT_CONF = {'version': 1,
                'colors': {
                    'bandwidth_graph': {'upload_rate': str(gtk.gdk.Color("blue")),
                                        'download_rate': str(gtk.gdk.Color("green")),
                                        },
                    'connections_graph': {'dht_nodes': str(gtk.gdk.Color("orange")),
                                          'dht_cache_nodes': str(gtk.gdk.Color("blue")),
                                          'dht_torrents': str(gtk.gdk.Color("green")),
                                          'num_connections': str(gtk.gdk.Color("darkred")),
                                          },
                    'seeds_graph': {'num_peers': str(gtk.gdk.Color("blue")),
                                    },
                }
                }


def neat_time(column, cell, model, iter):
    """Render seconds as seconds or minutes with label"""
    seconds = model.get_value(iter, 0)
    if seconds > 60:
        text = "%d %s" % (seconds / 60, _("minutes"))
    elif seconds == 60:
        text = _("1 minute")
    elif seconds == 1:
        text = _("1 second")
    else:
        text = "%d %s" % (seconds, _("seconds"))
    cell.set_property('text', text)
    return


def int_str(number):
    return (str(int(number)))


def gtk_to_graph_color(color):
    """Turns a gtk.gdk.Color into a tuple with range 0-1 as used by the graph"""
    max_val = float(65535)
    gtk_color = gtk.gdk.Color(color)
    red = gtk_color.red / max_val
    green = gtk_color.green / max_val
    blue = gtk_color.blue / max_val
    return (red, green, blue)


class GraphsTab(Tab):
    def __init__(self, glade, colors):
        Tab.__init__(self)
        self.glade = glade
        self.window = self.glade.get_widget('graph_tab')
        self.notebook = self.glade.get_widget('graph_notebook')
        self.label = self.glade.get_widget('graph_label')

        self._name = 'Graphs'
        self._child_widget = self.window
        self._tab_label = self.label

        self.colors = colors

        self.bandwidth_graph = self.glade.get_widget('bandwidth_graph')
        self.bandwidth_graph.connect('expose_event', self.graph_expose)

        self.connections_graph = self.glade.get_widget('connections_graph')
        self.connections_graph.connect('expose_event', self.graph_expose)

        self.seeds_graph = self.glade.get_widget('seeds_graph')
        self.seeds_graph.connect('expose_event', self.graph_expose)

        self.notebook.connect('switch-page', self._on_notebook_switch_page)

        self.selected_interval = 1  # Should come from config or similar
        self.select_bandwidth_graph()

        self.window.unparent()
        self.label.unparent()

        self.intervals = None
        self.intervals_combo = self.glade.get_widget('combo_intervals')
        cell = gtk.CellRendererText()
        self.intervals_combo.pack_start(cell, True)
        self.intervals_combo.set_cell_data_func(cell, neat_time)
        self.intervals_combo.connect("changed", self._on_selected_interval_changed)
        self.update_intervals()

    def graph_expose(self, widget, event):
        context = self.graph_widget.window.cairo_create()
        # set a clip region
        context.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
        context.clip()
        self.graph.draw_to_context(context,
                                   self.graph_widget.allocation.width,
                                   self.graph_widget.allocation.height)
        # Do not propagate the event
        return False

    def update(self):
        d1 = client.stats.get_stats(self.graph.stat_info.keys(), self.selected_interval)
        d1.addCallback(self.graph.set_stats)

        def _update_complete(result):
            self.graph_widget.queue_draw()
        d1.addCallback(_update_complete)
        return True

    def clear(self):
        pass

    def update_intervals(self):
        client.stats.get_intervals().addCallback(self._on_intervals_changed)

    def select_bandwidth_graph(self):
        log.debug("Selecting bandwidth graph")
        self.graph_widget = self.bandwidth_graph
        self.graph = Graph()
        colors = self.colors['bandwidth_graph']
        self.graph.add_stat('download_rate', label='Download Rate',
                            color=gtk_to_graph_color(colors['download_rate']))
        self.graph.add_stat('upload_rate', label='Upload Rate',
                            color=gtk_to_graph_color(colors['upload_rate']))
        self.graph.set_left_axis(formatter=fspeed, min=10240,
                                 formatter_scale=size_formatter_scale)

    def select_connections_graph(self):
        log.debug("Selecting connections graph")
        self.graph_widget = self.connections_graph
        g = Graph()
        self.graph = g
        colors = self.colors['connections_graph']
        g.add_stat('dht_nodes', color=gtk_to_graph_color(colors['dht_nodes']))
        g.add_stat('dht_cache_nodes', color=gtk_to_graph_color(colors['dht_cache_nodes']))
        g.add_stat('dht_torrents', color=gtk_to_graph_color(colors['dht_torrents']))
        g.add_stat('num_connections', color=gtk_to_graph_color(colors['num_connections']))
        g.set_left_axis(formatter=int_str, min=10)

    def select_seeds_graph(self):
        log.debug("Selecting connections graph")
        self.graph_widget = self.seeds_graph
        self.graph = Graph()
        colors = self.colors['seeds_graph']
        self.graph.add_stat('num_peers', color=gtk_to_graph_color(colors['num_peers']))
        self.graph.set_left_axis(formatter=int_str, min=10)

    def set_colors(self, colors):
        self.colors = colors
        # Fake switch page to update the graph colors (HACKY)
        self._on_notebook_switch_page(self.notebook,
                                      None,  # This is unused
                                      self.notebook.get_current_page())

    def _on_intervals_changed(self, intervals):
        liststore = gtk.ListStore(int)
        for inter in intervals:
            liststore.append([inter])
        self.intervals_combo.set_model(liststore)
        try:
            current = intervals.index(self.selected_interval)
        except:
            current = 0
        # should select the value saved in config
        self.intervals_combo.set_active(current)

    def _on_selected_interval_changed(self, combobox):
        model = combobox.get_model()
        iter = combobox.get_active_iter()
        self.selected_interval = model.get_value(iter, 0)
        self.update()
        return True

    def _on_notebook_switch_page(self, notebook, page, page_num):
        p = notebook.get_nth_page(page_num)
        if p is self.bandwidth_graph:
            self.select_bandwidth_graph()
            self.update()
        elif p is self.connections_graph:
            self.select_connections_graph()
            self.update()
        elif p is self.seeds_graph:
            self.select_seeds_graph()
            self.update()
        return True


class GtkUI(GtkPluginBase):
    def enable(self):
        log.debug("Stats plugin enable called")
        self.config = deluge.configmanager.ConfigManager("stats.gtkui.conf", DEFAULT_CONF)
        self.glade = XML(common.get_resource("config.glade"))
        component.get("Preferences").add_page("Stats", self.glade.get_widget("prefs_box"))
        component.get("PluginManager").register_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").register_hook("on_show_prefs", self.on_show_prefs)
        self.on_show_prefs()

        self.graphs_tab = GraphsTab(XML(common.get_resource("tabs.glade")), self.config['colors'])
        self.torrent_details = component.get('TorrentDetails')
        self.torrent_details.add_tab(self.graphs_tab)

    def disable(self):
        component.get("Preferences").remove_page("Stats")
        component.get("PluginManager").deregister_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").deregister_hook("on_show_prefs", self.on_show_prefs)
        self.torrent_details.remove_tab(self.graphs_tab.get_name())

    def on_apply_prefs(self):
        log.debug("applying prefs for Stats")
        gtkconf = {}
        for graph, colors in self.config['colors'].items():
            gtkconf[graph] = {}
            for value, color in colors.items():
                try:
                    color_btn = self.glade.get_widget("%s_%s_color" % (graph, value))
                    gtkconf[graph][value] = str(color_btn.get_color())
                except:
                    gtkconf[graph][value] = DEFAULT_CONF['colors'][graph][value]
        self.config['colors'] = gtkconf
        self.graphs_tab.set_colors(self.config['colors'])

        config = {}
        client.stats.set_config(config)

    def on_show_prefs(self):
        for graph, colors in self.config['colors'].items():
            for value, color in colors.items():
                try:
                    color_btn = self.glade.get_widget("%s_%s_color" % (graph, value))
                    color_btn.set_color(gtk.gdk.Color(color))
                except:
                    log.debug("Unable to set %s %s %s" % (graph, value, color))
        client.stats.get_config().addCallback(self.cb_get_config)

    def cb_get_config(self, config):
        "callback for on show_prefs"
        pass
