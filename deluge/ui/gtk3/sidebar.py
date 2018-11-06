# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging

from gi.repository.Gtk import Label, PolicyType, ScrolledWindow

import deluge.component as component
from deluge.configmanager import ConfigManager

log = logging.getLogger(__name__)


class SideBar(component.Component):
    """
    manages the sidebar-tabs.
    purpose : plugins
    """

    def __init__(self):
        component.Component.__init__(self, 'SideBar')
        main_builder = component.get('MainWindow').get_builder()
        self.notebook = main_builder.get_object('sidebar_notebook')
        self.config = ConfigManager('gtk3ui.conf')

        # Tabs holds references to the Tab widgets by their name
        self.tabs = {}

        # Hide if necessary
        self.visible(self.config['show_sidebar'])

    def visible(self, visible):
        self.notebook.show() if visible else self.notebook.hide()
        self.config['show_sidebar'] = visible

    def add_tab(self, widget, tab_name, label):
        """Adds a tab object to the notebook."""
        log.debug('add tab: %s', tab_name)
        self.tabs[tab_name] = widget
        scrolled = ScrolledWindow()
        scrolled.set_policy(PolicyType.AUTOMATIC, PolicyType.AUTOMATIC)
        scrolled.add(widget)
        self.notebook.insert_page(scrolled, Label(label=label), -1)
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
