# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
#               2008 Andrew Resch <andrewresch@gmail.com>
#               2014 Calum Lind <calumlind@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging
import os
import warnings

from gi.repository import Gtk
from gi.repository.GdkPixbuf import Pixbuf
from gi.repository.Pango import EllipsizeMode

import deluge.component as component
from deluge.common import TORRENT_STATE, decode_bytes, resource_filename
from deluge.configmanager import ConfigManager
from deluge.ui.client import client

from .common import get_pixbuf, get_pixbuf_at_size

log = logging.getLogger(__name__)

STATE_PIX = {
    'All': 'all',
    'Downloading': 'downloading',
    'Seeding': 'seeding',
    'Paused': 'inactive',
    'Checking': 'checking',
    'Queued': 'queued',
    'Error': 'alert',
    'Active': 'active',
    'Allocating': 'checking',
    'Moving': 'checking',
}

TRACKER_PIX = {'All': 'tracker_all', 'Error': 'tracker_warning'}

FILTER_COLUMN = 5


class FilterTreeView(component.Component):
    def __init__(self):
        component.Component.__init__(self, 'FilterTreeView', interval=2)
        self.config = ConfigManager('gtk3ui.conf')

        self.tracker_icons = component.get('TrackerIcons')

        self.sidebar = component.get('SideBar')
        self.treeview = Gtk.TreeView()
        self.sidebar.add_tab(self.treeview, 'filters', 'Filters')

        # set filter to all when hidden:
        self.sidebar.notebook.connect('hide', self._on_hide)

        # Create the treestore
        # cat, value, label, count, pixmap, visible
        self.treestore = Gtk.TreeStore(str, str, str, int, Pixbuf, bool)

        # Create the column and cells
        column = Gtk.TreeViewColumn('Filters')
        column.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        # icon cell
        self.cell_pix = Gtk.CellRendererPixbuf()
        column.pack_start(self.cell_pix, expand=False)
        column.add_attribute(self.cell_pix, 'pixbuf', 4)
        # label cell
        cell_label = Gtk.CellRendererText()
        cell_label.set_property('ellipsize', EllipsizeMode.END)
        column.pack_start(cell_label, expand=True)
        column.set_cell_data_func(cell_label, self.render_cell_data, None)
        # count cell
        self.cell_count = Gtk.CellRendererText()
        self.cell_count.set_property('xalign', 1.0)
        self.cell_count.set_padding(3, 0)
        column.pack_start(self.cell_count, expand=False)

        self.treeview.append_column(column)

        # Style
        self.treeview.set_show_expanders(True)
        self.treeview.set_headers_visible(False)
        self.treeview.set_level_indentation(-21)
        # Force theme to use expander-size so we don't cut out entries due to indentation hack.
        provider = Gtk.CssProvider()
        provider.load_from_data('* {-GtkTreeView-expander-size: 9;}'.encode())
        context = self.treeview.get_style_context()
        context.add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.treeview.set_model(self.treestore)
        self.treeview.get_selection().connect('changed', self.on_selection_changed)
        self.create_model_filter()

        self.treeview.connect('button-press-event', self.on_button_press_event)

        # filtertree menu
        builder = Gtk.Builder()
        builder.add_from_file(
            resource_filename(__package__, os.path.join('glade', 'filtertree_menu.ui'))
        )
        self.menu = builder.get_object('filtertree_menu')
        builder.connect_signals(self)

        self.default_menu_items = self.menu.get_children()

        # add Cat nodes:
        self.cat_nodes = {}
        self.filters = {}

    def start(self):
        self.cat_nodes = {}
        self.filters = {}
        # initial order of state filter:
        self.cat_nodes['state'] = self.treestore.append(
            None, ['cat', 'state', _('States'), 0, None, False]
        )
        for state in ['All', 'Active'] + TORRENT_STATE:
            self.update_row('state', state, 0, _(state))

        self.cat_nodes['tracker_host'] = self.treestore.append(
            None, ['cat', 'tracker_host', _('Trackers'), 0, None, False]
        )
        self.update_row('tracker_host', 'All', 0, _('All'))
        self.update_row('tracker_host', 'Error', 0, _('Error'))
        self.update_row('tracker_host', '', 0, _('None'))

        self.cat_nodes['owner'] = self.treestore.append(
            None, ['cat', 'owner', _('Owner'), 0, None, False]
        )
        self.update_row('owner', 'localclient', 0, _('Admin'))
        self.update_row('owner', '', 0, _('None'))

        # We set to this expand the rows on start-up
        self.expand_rows = True

        self.selected_path = None

    def stop(self):
        self.treestore.clear()

    def create_model_filter(self):
        self.model_filter = self.treestore.filter_new()
        self.model_filter.set_visible_column(FILTER_COLUMN)
        self.treeview.set_model(self.model_filter)

    def cb_update_filter_tree(self, filter_items):
        # create missing cat_nodes
        for cat in filter_items:
            if cat not in self.cat_nodes:
                label = _(cat)
                if cat == 'label':
                    label = _('Labels')
                self.cat_nodes[cat] = self.treestore.append(
                    None, ['cat', cat, label, 0, None, False]
                )

        # update rows
        visible_filters = []
        for cat, filters in filter_items.items():
            for value, count in filters:
                self.update_row(cat, value, count)
                visible_filters.append((cat, value))

        # hide root-categories not returned by core-part of the plugin.
        for cat in self.cat_nodes:
            self.treestore.set_value(
                self.cat_nodes[cat],
                FILTER_COLUMN,
                True if cat in filter_items else False,
            )

        # hide items not returned by core-plugin.
        for f in self.filters:
            if f not in visible_filters:
                self.treestore.set_value(self.filters[f], FILTER_COLUMN, False)

        if self.expand_rows:
            self.treeview.expand_all()
            self.expand_rows = False

        if not self.selected_path:
            self.select_default_filter()

    def update_row(self, cat, value, count, label=None):
        def on_get_icon(icon):
            if icon:
                self.set_row_image(cat, value, icon.get_filename())

        if (cat, value) in self.filters:
            row = self.filters[(cat, value)]
            self.treestore.set_value(row, 3, count)
        else:
            pix = self.get_pixmap(cat, value)

            if value == '':
                if cat == 'label':
                    label = _('No Label')
                elif cat == 'owner':
                    label = _('No Owner')
            elif not label and value:
                label = _(value)

            row = self.treestore.append(
                self.cat_nodes[cat], [cat, value, label, count, pix, True]
            )
            self.filters[(cat, value)] = row

            if cat == 'tracker_host' and value not in ('All', 'Error') and value:
                d = self.tracker_icons.fetch(value)
                d.addCallback(on_get_icon)

        self.treestore.set_value(row, FILTER_COLUMN, True)
        return row

    def render_cell_data(self, column, cell, model, row, data):
        cat = model.get_value(row, 0)
        label = decode_bytes(model.get_value(row, 2))
        count = model.get_value(row, 3)

        # Suppress Warning: g_object_set_qdata: assertion `G_IS_OBJECT (object)' failed
        original_filters = warnings.filters[:]
        warnings.simplefilter('ignore')
        try:
            pix = model.get_value(row, 4)
        finally:
            warnings.filters = original_filters

        self.cell_pix.set_property('visible', True if pix else False)

        if cat == 'cat':
            self.cell_count.set_property('visible', False)
            cell.set_padding(10, 2)
            label = '<b>%s</b>' % label
        else:
            count_txt = '<small>%s</small>' % count
            self.cell_count.set_property('markup', count_txt)
            self.cell_count.set_property('visible', True)
            cell.set_padding(2, 1)
        cell.set_property('markup', label)

    def get_pixmap(self, cat, value):
        pix = None
        if cat == 'state':
            pix = STATE_PIX.get(value, None)
        elif cat == 'tracker_host':
            pix = TRACKER_PIX.get(value, None)

        if pix:
            return get_pixbuf('%s16.png' % pix)

    def set_row_image(self, cat, value, filename):
        pix = get_pixbuf_at_size(filename, 16)
        row = self.filters[(cat, value)]
        self.treestore.set_value(row, 4, pix)
        return False

    def on_selection_changed(self, selection):
        try:
            (model, row) = self.treeview.get_selection().get_selected()
            if not row:
                log.debug('nothing selected')
                return

            cat = model.get_value(row, 0)
            value = model.get_value(row, 1)

            filter_dict = {cat: [value]}
            if value == 'All' or cat == 'cat':
                filter_dict = {}

            component.get('TorrentView').set_filter(filter_dict)

            self.selected_path = model.get_path(row)

        except Exception as ex:
            log.debug(ex)
            # paths is likely None .. so lets return None
            return None

    def update(self):
        try:
            hide_cat = []
            if not self.config['sidebar_show_trackers']:
                hide_cat.append('tracker_host')
            if not self.config['sidebar_show_owners']:
                hide_cat.append('owner')
            client.core.get_filter_tree(
                self.config['sidebar_show_zero'], hide_cat
            ).addCallback(self.cb_update_filter_tree)
        except Exception as ex:
            log.debug(ex)

    # Callbacks #
    def on_button_press_event(self, widget, event):
        """This is a callback for showing the right-click context menu."""
        x, y = event.get_coords()
        path = self.treeview.get_path_at_pos(int(x), int(y))
        if not path:
            return
        path = path[0]
        cat = self.model_filter[path][0]

        if event.button == 1:
            # Prevent selecting a category label
            if cat == 'cat':
                if self.treeview.row_expanded(path):
                    self.treeview.collapse_row(path)
                else:
                    self.treeview.expand_row(path, False)
                    if not self.selected_path:
                        self.select_default_filter()
                    else:
                        self.treeview.get_selection().select_path(self.selected_path)
                return True

        elif event.button == 3:
            # assign current cat, value to self:
            x, y = event.get_coords()
            path = self.treeview.get_path_at_pos(int(x), int(y))
            if not path:
                return
            row = self.model_filter.get_iter(path[0])
            self.cat = self.model_filter.get_value(row, 0)
            self.value = self.model_filter.get_value(row, 1)
            self.count = self.model_filter.get_value(row, 3)

            # Show the pop-up menu
            self.set_menu_sensitivity()
            self.menu.hide()
            self.menu.popup(None, None, None, None, event.button, event.time)
            self.menu.show()

            if cat == 'cat':
                # Do not select the row
                return True

    def set_menu_sensitivity(self):
        # select-all/pause/resume
        sensitive = self.cat != 'cat' and self.count != 0
        for item in self.default_menu_items:
            item.set_sensitive(sensitive)

    def select_all(self):
        """For use in popup menu."""
        component.get('TorrentView').treeview.get_selection().select_all()

    def on_select_all(self, event):
        self.select_all()

    def on_pause_all(self, event):
        self.select_all()
        func = getattr(component.get('MenuBar'), 'on_menuitem_%s_activate' % 'pause')
        func(event)

    def on_resume_all(self, event):
        self.select_all()
        func = getattr(component.get('MenuBar'), 'on_menuitem_%s_activate' % 'resume')
        func(event)

    def _on_hide(self, *args):
        self.select_default_filter()

    def select_default_filter(self):
        row = self.filters[('state', 'All')]
        path = self.treestore.get_path(row)
        self.treeview.get_selection().select_path(path)
