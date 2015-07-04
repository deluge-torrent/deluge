# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging

import deluge.component as component
import gi
from deluge.configmanager import ConfigManager
from gi.repository import Gtk

gi.require_version('Gtk', '3.0')


log = logging.getLogger(__name__)


class ToolBar(component.Component):
    def __init__(self):
        component.Component.__init__(self, "ToolBar")
        log.debug("ToolBar Init..")
        self.window = component.get("MainWindow")
        self.toolbar = self.window.get_builder().get_object("toolbar")
        self.config = ConfigManager("gtkui.conf")
        # Connect main window Signals #
        self.window.connect_signals({
            "on_toolbutton_add_clicked": self.on_toolbutton_add_clicked,
            "on_toolbutton_remove_clicked": self.on_toolbutton_remove_clicked,
            "on_toolbutton_pause_clicked": self.on_toolbutton_pause_clicked,
            "on_toolbutton_resume_clicked": self.on_toolbutton_resume_clicked,
            "on_toolbutton_preferences_clicked": self.on_toolbutton_preferences_clicked,
            "on_toolbutton_connectionmanager_clicked": self.on_toolbutton_connectionmanager_clicked,
            "on_toolbutton_queue_up_clicked": self.on_toolbutton_queue_up_clicked,
            "on_toolbutton_queue_down_clicked": self.on_toolbutton_queue_down_clicked
        })
        self.change_sensitivity = [
            "toolbutton_add",
            "toolbutton_remove",
            "toolbutton_pause",
            "toolbutton_resume",
            "toolbutton_queue_up",
            "toolbutton_queue_down",
            "toolbutton_filter",
            "find_menuitem"
        ]

        # Hide if necessary
        self.visible(self.config["show_toolbar"])

    def start(self):
        self.window.get_builder().get_object("toolbutton_connectionmanager").set_visible(
            not self.config["classic_mode"])

        for widget in self.change_sensitivity:
            self.window.get_builder().get_object(widget).set_sensitive(True)

    def stop(self):
        for widget in self.change_sensitivity:
            self.window.get_builder().get_object(widget).set_sensitive(False)

    def visible(self, visible):
        if visible:
            self.toolbar.show()
        else:
            self.toolbar.hide()

        self.config["show_toolbar"] = visible

    def add_toolbutton(self, callback, label=None, image=None, stock=None, tooltip=None):
        """Adds a toolbutton to the toolbar"""
        toolbutton = Gtk.ToolButton()
        if stock is not None:
            toolbutton.set_stock_id(stock)
        if label is not None:
            toolbutton.set_label(label)
        if image is not None:
            toolbutton.set_icon_widget(image)
        if tooltip is not None:
            toolbutton.set_tooltip_text(tooltip)

        toolbutton.connect("clicked", callback)
        self.toolbar.insert(toolbutton, -1)
        toolbutton.show_all()

        return toolbutton

    def add_separator(self, position=None):
        """Adds a separator toolitem"""
        sep = Gtk.SeparatorToolItem()
        if position is not None:
            self.toolbar.insert(sep, position)
        else:
            self.toolbar.insert(sep, -1)

        sep.show()

        return sep

    def remove(self, widget):
        """Removes a widget from the toolbar"""
        self.toolbar.remove(widget)

    # Callbacks (Uses the menubar's callback) #

    def on_toolbutton_add_clicked(self, data):
        log.debug("on_toolbutton_add_clicked")
        component.get("MenuBar").on_menuitem_addtorrent_activate(data)

    def on_toolbutton_remove_clicked(self, data):
        log.debug("on_toolbutton_remove_clicked")
        component.get("MenuBar").on_menuitem_remove_activate(data)

    def on_toolbutton_pause_clicked(self, data):
        log.debug("on_toolbutton_pause_clicked")
        component.get("MenuBar").on_menuitem_pause_activate(data)

    def on_toolbutton_resume_clicked(self, data):
        log.debug("on_toolbutton_resume_clicked")
        component.get("MenuBar").on_menuitem_resume_activate(data)

    def on_toolbutton_preferences_clicked(self, data):
        log.debug("on_toolbutton_preferences_clicked")
        component.get("MenuBar").on_menuitem_preferences_activate(data)

    def on_toolbutton_connectionmanager_clicked(self, data):
        log.debug("on_toolbutton_connectionmanager_clicked")
        component.get("MenuBar").on_menuitem_connectionmanager_activate(data)

    def on_toolbutton_queue_up_clicked(self, data):
        log.debug("on_toolbutton_queue_up_clicked")
        component.get("MenuBar").on_menuitem_queue_up_activate(data)

    def on_toolbutton_queue_down_clicked(self, data):
        log.debug("on_toolbutton_queue_down_clicked")
        component.get("MenuBar").on_menuitem_queue_down_activate(data)
