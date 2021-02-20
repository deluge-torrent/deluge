# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#


"""The torrent details component shows info about the selected torrent."""
from __future__ import unicode_literals

import logging
from collections import namedtuple

from gi.repository.Gtk import (
    CheckMenuItem,
    Menu,
    MenuItem,
    PositionType,
    RadioMenuItem,
    SeparatorMenuItem,
)

import deluge.component as component
from deluge.ui.client import client

from .common import load_pickled_state_file, save_pickled_state_file

log = logging.getLogger(__name__)

TabWidget = namedtuple('TabWidget', ('obj', 'func', 'status_keys'))


class Tab(object):
    def __init__(self, name=None, child_widget=None, tab_label=None):
        self._name = name
        self.is_visible = True
        self.position = -1
        self.weight = -1

        self.main_builder = component.get('MainWindow').get_builder()
        self._child_widget = (
            self.main_builder.get_object(child_widget) if child_widget else None
        )
        self._tab_label = self.main_builder.get_object(tab_label) if tab_label else None

        self.tab_widgets = {}
        self.status_keys = []

    def get_name(self):
        return self._name

    def get_child_widget(self):
        parent = self._child_widget.get_parent()
        if parent is not None:
            parent.remove(self._child_widget)

        return self._child_widget

    def get_tab_label(self):
        parent = self._tab_label.get_parent()
        log.debug('parent: %s', parent)
        if parent is not None:
            parent.remove(self._tab_label)

        return self._tab_label

    def widget_status_as_fstr(self, widget, status):
        """Use TabWidget status_key and func to format status string.

        Args:
            widget (TabWidget): A tuple of widget object, func and status_keys.
            status (dict): Torrent status dict.

        Returns:
            str: The formatted status string.
        """
        try:
            if widget.func is None:
                txt = status[widget.status_keys[0]]
            else:
                args = [status[key] for key in widget.status_keys]
                txt = widget.func(*args)
        except KeyError as ex:
            log.warning('Unable to get status value: %s', ex)
            txt = ''
        return txt

    def add_tab_widget(self, widget_id, format_func, status_keys):
        """Create TabWidget item in tab_widgets dictionary.

        Args:
            widget_id (str): The widget id used to retrieve widget from mainwindow builder.
            format_func (str): A func name related to widget e.g. string label formatter.
            status_keys (list): List of status keys to lookup for the widget.

        """
        widget_obj = self.main_builder.get_object(widget_id)
        self.status_keys.extend(status_keys)
        # Store the widget in a tab_widgets dict with name as key for faster lookup.
        self.tab_widgets[widget_id] = TabWidget(widget_obj, format_func, status_keys)


class TorrentDetails(component.Component):
    def __init__(self):
        component.Component.__init__(self, 'TorrentDetails', interval=2)
        main_builder = component.get('MainWindow').get_builder()
        self.config = component.get('MainWindow').config

        self.notebook = main_builder.get_object('torrent_info')
        self.notebook.set_tab_pos(
            getattr(PositionType, self.config['tabsbar_tab_pos'].upper())
        )

        # This is the menu item we'll attach the tabs checklist menu to
        self.menu_tabs = main_builder.get_object('menu_tabs')

        self.notebook.connect('switch-page', self._on_switch_page)

        # Tabs holds references to the Tab objects by their name
        self.tabs = {}

        # Add the default tabs
        from .details_tab import DetailsTab
        from .files_tab import FilesTab
        from .options_tab import OptionsTab
        from .peers_tab import PeersTab
        from .status_tab import StatusTab
        from .trackers_tab import TrackersTab

        default_tabs = {
            'Status': StatusTab,
            'Details': DetailsTab,
            'Files': FilesTab,
            'Peers': PeersTab,
            'Options': OptionsTab,
            'Trackers': TrackersTab,
        }

        # tab_name, visible
        default_order = [
            ('Status', True),
            ('Details', True),
            ('Options', True),
            ('Files', True),
            ('Peers', True),
            ('Trackers', True),
        ]

        self.translate_tabs = {
            'All': _('_All'),
            'Status': _('_Status'),
            'Details': _('_Details'),
            'Files': _('Fi_les'),
            'Peers': _('_Peers'),
            'Options': _('_Options'),
            'Trackers': _('_Trackers'),
        }

        # Get the state from saved file
        state = self.load_state()

        if state:
            for item in state:
                if not isinstance(item, tuple):
                    log.debug('Old tabs.state, using default..')
                    state = None
                    break

        # The state is a list of tab_names in the order they should appear
        if state is None:
            # Set the default order
            state = default_order

        # We need to rename the tab in the state for backwards compat
        self.state = [
            (tab_name.replace('Statistics', 'Status'), visible)
            for tab_name, visible in state
        ]

        for tab in default_tabs.values():
            self.add_tab(tab(), generate_menu=False)

        # Generate the checklist menu
        self.generate_menu()

        self.visible(self.config['show_tabsbar'])

    def tab_insert_position(self, weight):
        """Returns the position a tab with a given weight should be inserted in"""
        # Determine insert position based on weight
        # weights is a list of visible tab names in weight order

        weights = sorted(
            (tab.weight, name) for name, tab in self.tabs.items() if tab.is_visible
        )

        log.debug('weights: %s', weights)
        log.debug('weight of tab: %s', weight)

        position = -1
        for w, name in weights:
            if w >= weight:
                position = self.tabs[name].position
                log.debug('Found pos %d', position)
                break
        return position

    def add_tab(self, tab, generate_menu=True, visible=None):
        name = tab.get_name()

        # find position of tab in self.state, this is the tab weight
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
            # add the tab at position guided by the weight
            insert_pos = self.tab_insert_position(weight)
            log.debug('Trying to insert tab at %d', insert_pos)
            pos = self.notebook.insert_page(
                tab.get_child_widget(), tab.get_tab_label(), insert_pos
            )
            log.debug('Tab inserted at %d', pos)
            tab.position = pos
            if not self.notebook.get_property('visible'):
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
        """Sync the positions in the tab, with the position stored in the tab object"""
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
        log.debug('n_pages: %s', self.notebook.get_n_pages())
        for n in range(self.notebook.get_n_pages() - 1, -1, -1):
            self.notebook.remove_page(n)

        for tab in self.tabs:
            self.tabs[tab].is_visible = False
        log.debug('n_pages: %s', self.notebook.get_n_pages())
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
        for name, tab in self.tabs.items():
            show = show or tab.is_visible

        self.visible(show)

    def show_tab(self, tab_name, generate_menu=True):
        log.debug(
            '%s\n%s\n%s',
            self.tabs[tab_name].get_child_widget(),
            self.tabs[tab_name].get_tab_label(),
            self.tabs[tab_name].position,
        )

        position = self.tab_insert_position(self.tabs[tab_name].weight)

        log.debug('position: %s', position)
        self.notebook.insert_page(
            self.tabs[tab_name].get_child_widget(),
            self.tabs[tab_name].get_tab_label(),
            position,
        )
        self.tabs[tab_name].is_visible = True
        self.regenerate_positions()
        if generate_menu:
            self.generate_menu()
        self.visible(True)

    def create_tab_pos_menuitem(self):
        """Returns a menu to select which side of the notebook the tabs should be shown"""
        tab_pos_menu = Menu()
        tab_pos_menuitem = MenuItem.new_with_label(_('Position'))
        group = []
        for pos in ('top', 'right', 'bottom', 'left'):
            menuitem = RadioMenuItem.new_with_mnemonic(group, _(pos.capitalize()))
            group = menuitem.get_group()
            menuitem.connect('toggled', self._on_tabs_pos_toggled, pos)
            menuitem.set_active(pos == self.notebook.get_tab_pos().value_nick)
            tab_pos_menu.append(menuitem)
        tab_pos_menuitem.set_submenu(tab_pos_menu)
        return tab_pos_menuitem

    def generate_menu(self):
        """Generates the checklist menu for all the tabs and attaches it"""
        menu = Menu()

        # Create 'All' menuitem and a separator
        menuitem = CheckMenuItem.new_with_mnemonic(self.translate_tabs['All'])
        menuitem.set_name('All')

        all_tabs = True
        for key in self.tabs:
            if not self.tabs[key].is_visible:
                all_tabs = False
                break
        menuitem.set_active(all_tabs)
        menuitem.connect('toggled', self._on_menuitem_toggled)

        menu.append(menuitem)

        menuitem = SeparatorMenuItem()
        menu.append(menuitem)

        # Create a list in order of tabs to create menu
        menuitem_list = []
        for tab_name in self.tabs:
            menuitem_list.append((self.tabs[tab_name].weight, tab_name))
        menuitem_list.sort()

        for pos, name in menuitem_list:
            menuitem = CheckMenuItem.new_with_mnemonic(self.translate_tabs[name])
            menuitem.set_name(name)
            menuitem.set_active(self.tabs[name].is_visible)
            menuitem.connect('toggled', self._on_menuitem_toggled)
            menu.append(menuitem)

        menu.append(SeparatorMenuItem())
        menu.append(self.create_tab_pos_menuitem())

        self.menu_tabs.set_submenu(menu)
        self.menu_tabs.show_all()

    def visible(self, visible):
        self.notebook.show() if visible else self.notebook.hide()
        self.config['show_tabsbar'] = visible

    def set_tab_visible(self, tab_name, visible):
        """Sets the tab to visible"""
        log.debug('set_tab_visible name: %s visible: %s', tab_name, visible)
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
        if len(component.get('TorrentView').get_selected_torrents()) == 0:
            # No torrents selected, so just clear
            self.clear()

        if self.notebook.get_property('visible'):
            if page_num is None:
                page_num = self.notebook.get_current_page()
            try:
                # Get the tab name
                name = None
                for tab in self.tabs:
                    if (
                        self.tabs[tab].position == page_num
                        and self.tabs[tab].is_visible
                    ):
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
        except Exception as ex:
            log.debug('Unable to clear torrentdetails: %s', ex)

    def _on_switch_page(self, notebook, page, page_num):
        self.update(page_num)
        client.force_call(False)

    def _on_menuitem_toggled(self, widget):
        # Get the tab name
        name = widget.get_name()
        if name == 'All':
            if widget.get_active():
                self.show_all_tabs()
            else:
                self.hide_all_tabs()
            return

        self.set_tab_visible(name, widget.get_active())

    def _on_tabs_pos_toggled(self, widget, position):
        self.config['tabsbar_tab_pos'] = position
        self.notebook.set_tab_pos(getattr(PositionType, position.upper()))

    def save_state(self):
        """We save the state, which is basically the tab_index list"""
        # Update the visiblity status of all tabs
        # Leave tabs we dont know anything about it the state as they
        # might come from a plugin
        for i, (name, visible) in enumerate(self.state):
            log.debug('Testing name: %s', name)
            if name in self.tabs:
                self.state[i] = (name, self.tabs[name].is_visible)
                log.debug('Set to %s', self.state[i])
        state = self.state

        save_pickled_state_file('tabs.state', state)

    def load_state(self):
        return load_pickled_state_file('tabs.state')
