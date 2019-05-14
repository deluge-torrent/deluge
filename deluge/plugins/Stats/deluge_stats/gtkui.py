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

from __future__ import division, unicode_literals

import logging

from gi.repository import Gtk
from gi.repository.Gdk import RGBA

import deluge
from deluge import component
from deluge.common import fspeed
from deluge.plugins.pluginbase import Gtk3PluginBase
from deluge.ui.client import client
from deluge.ui.gtk3.torrentdetails import Tab

from .common import get_resource
from .graph import Graph, size_formatter_scale

log = logging.getLogger(__name__)

# Gdk.RGBA textual spec
RED = 'rgb(255,0,0)'
GREEN = 'rgb(0,128,0)'
BLUE = 'rgb(0,0,255)'
DARKRED = 'rgb(139,0,0)'
ORANGE = 'rgb(255,165,0)'

DEFAULT_CONF = {
    'version': 2,
    'colors': {
        'bandwidth_graph': {'upload_rate': BLUE, 'download_rate': GREEN},
        'connections_graph': {
            'dht_nodes': ORANGE,
            'dht_cache_nodes': BLUE,
            'dht_torrents': GREEN,
            'num_connections': DARKRED,
        },
        'seeds_graph': {'num_peers': BLUE},
    },
}


def neat_time(column, cell, model, data):
    """Render seconds as seconds or minutes with label"""
    seconds = model.get_value(data, 0)
    if seconds > 60:
        text = '%d %s' % (seconds // 60, _('minutes'))
    elif seconds == 60:
        text = _('1 minute')
    elif seconds == 1:
        text = _('1 second')
    else:
        text = '%d %s' % (seconds, _('seconds'))
    cell.set_property('text', text)
    return


def int_str(number):
    return str(int(number))


def fspeed_shortform(value):
    return fspeed(value, shortform=True)


def text_to_rgba(color):
    """Turns a Color into a tuple with range 0-1 as used by the graph"""
    color_rgba = RGBA()
    color_rgba.parse(color)
    return color_rgba


class GraphsTab(Tab):
    def __init__(self, colors):
        super(GraphsTab, self).__init__()

        builder = Gtk.Builder()
        builder.add_from_file(get_resource('tabs.ui'))
        self.window = builder.get_object('graph_tab')
        self.notebook = builder.get_object('graph_notebook')
        self.label = builder.get_object('graph_label')

        self._name = 'Stats'
        self._child_widget = self.window
        self._tab_label = self.label

        self.colors = colors

        self.bandwidth_graph = builder.get_object('bandwidth_graph')
        self.bandwidth_graph.connect('draw', self.on_graph_draw)

        self.connections_graph = builder.get_object('connections_graph')
        self.connections_graph.connect('draw', self.on_graph_draw)

        self.seeds_graph = builder.get_object('seeds_graph')
        self.seeds_graph.connect('draw', self.on_graph_draw)

        self.notebook.connect('switch-page', self._on_notebook_switch_page)

        self.selected_interval = 1  # Should come from config or similar
        self.select_bandwidth_graph()

        self.window.unparent()
        self.label.unparent()

        self.intervals = None
        self.intervals_combo = builder.get_object('combo_intervals')
        cell = Gtk.CellRendererText()
        self.intervals_combo.pack_start(cell, True)
        self.intervals_combo.set_cell_data_func(cell, neat_time)
        self.intervals_combo.connect('changed', self._on_selected_interval_changed)
        self.update_intervals()

    def on_graph_draw(self, widget, context):
        self.graph.draw_to_context(
            context,
            self.graph_widget.get_allocated_width(),
            self.graph_widget.get_allocated_height(),
        )
        # Do not propagate the event
        return True

    def update(self):
        d1 = client.stats.get_stats(list(self.graph.stat_info), self.selected_interval)
        d1.addCallback(self.graph.set_stats)

        def _update_complete(result):
            self.graph_widget.queue_draw()
            return result

        d1.addCallback(_update_complete)
        return d1

    def clear(self):
        pass

    def update_intervals(self):
        client.stats.get_intervals().addCallback(self._on_intervals_changed)

    def select_bandwidth_graph(self):
        log.debug('Selecting bandwidth graph')
        self.graph_widget = self.bandwidth_graph
        self.graph = Graph()
        colors = self.colors['bandwidth_graph']
        self.graph.add_stat(
            'download_rate',
            label='Download Rate',
            color=text_to_rgba(colors['download_rate']),
        )
        self.graph.add_stat(
            'upload_rate',
            label='Upload Rate',
            color=text_to_rgba(colors['upload_rate']),
        )
        self.graph.set_left_axis(
            formatter=fspeed_shortform, min=10240, formatter_scale=size_formatter_scale
        )

    def select_connections_graph(self):
        log.debug('Selecting connections graph')
        self.graph_widget = self.connections_graph
        g = Graph()
        self.graph = g
        colors = self.colors['connections_graph']
        g.add_stat('dht_nodes', color=text_to_rgba(colors['dht_nodes']))
        g.add_stat('dht_cache_nodes', color=text_to_rgba(colors['dht_cache_nodes']))
        g.add_stat('dht_torrents', color=text_to_rgba(colors['dht_torrents']))
        g.add_stat('num_connections', color=text_to_rgba(colors['num_connections']))
        g.set_left_axis(formatter=int_str, min=10)

    def select_seeds_graph(self):
        log.debug('Selecting connections graph')
        self.graph_widget = self.seeds_graph
        self.graph = Graph()
        colors = self.colors['seeds_graph']
        self.graph.add_stat('num_peers', color=text_to_rgba(colors['num_peers']))
        self.graph.set_left_axis(formatter=int_str, min=10)

    def set_colors(self, colors):
        self.colors = colors
        # Fake switch page to update the graph colors (HACKY)
        self._on_notebook_switch_page(
            self.notebook, None, self.notebook.get_current_page()  # This is unused
        )

    def _on_intervals_changed(self, intervals):
        liststore = Gtk.ListStore(int)
        for inter in intervals:
            liststore.append([inter])
        self.intervals_combo.set_model(liststore)
        try:
            current = intervals.index(self.selected_interval)
        except Exception:
            current = 0
        # should select the value saved in config
        self.intervals_combo.set_active(current)

    def _on_selected_interval_changed(self, combobox):
        model = combobox.get_model()
        tree_iter = combobox.get_active_iter()
        self.selected_interval = model.get_value(tree_iter, 0)
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


class GtkUI(Gtk3PluginBase):
    def enable(self):
        log.debug('Stats plugin enable called')
        self.config = deluge.configmanager.ConfigManager(
            'stats.gtk3ui.conf', DEFAULT_CONF
        )

        self.builder = Gtk.Builder()
        self.builder.add_from_file(get_resource('config.ui'))

        component.get('Preferences').add_page(
            'Stats', self.builder.get_object('prefs_box')
        )
        component.get('PluginManager').register_hook(
            'on_apply_prefs', self.on_apply_prefs
        )
        component.get('PluginManager').register_hook(
            'on_show_prefs', self.on_show_prefs
        )
        self.on_show_prefs()

        self.graphs_tab = GraphsTab(self.config['colors'])
        self.torrent_details = component.get('TorrentDetails')
        self.torrent_details.add_tab(self.graphs_tab)

    def disable(self):
        component.get('Preferences').remove_page('Stats')
        component.get('PluginManager').deregister_hook(
            'on_apply_prefs', self.on_apply_prefs
        )
        component.get('PluginManager').deregister_hook(
            'on_show_prefs', self.on_show_prefs
        )
        self.torrent_details.remove_tab(self.graphs_tab.get_name())

    def on_apply_prefs(self):
        log.debug('applying prefs for Stats')
        gtkconf = {}
        for graph, colors in self.config['colors'].items():
            gtkconf[graph] = {}
            for value, color in colors.items():
                color_btn = self.builder.get_object('%s_%s_color' % (graph, value))
                try:
                    gtkconf[graph][value] = color_btn.get_color().to_string()
                except Exception:
                    gtkconf[graph][value] = DEFAULT_CONF['colors'][graph][value]
        self.config['colors'] = gtkconf
        self.graphs_tab.set_colors(self.config['colors'])

        config = {}
        client.stats.set_config(config)

    def on_show_prefs(self):
        for graph, colors in self.config['colors'].items():
            for value, color in colors.items():
                try:
                    color_btn = self.builder.get_object('%s_%s_color' % (graph, value))
                    color_btn.set_rgba(text_to_rgba(color))
                except Exception as ex:
                    log.debug('Unable to set %s %s %s: %s', graph, value, color, ex)
        client.stats.get_config().addCallback(self.cb_get_config)

    def cb_get_config(self, config):
        """Callback for on show_prefs."""
        pass
