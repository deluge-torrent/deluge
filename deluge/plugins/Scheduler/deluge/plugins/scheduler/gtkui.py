# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging

from gi.repository import Gtk, Gdk

import deluge.component as component
from deluge.plugins.pluginbase import GtkPluginBase
from deluge.ui.client import client
from gi import pygtkcompat

from .common import get_resource

pygtkcompat.enable()
pygtkcompat.enable_gtk(version='3.0')

log = logging.getLogger(__name__)

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class SchedulerSelectWidget(Gtk.DrawingArea):
    def __init__(self, hover):
        Gtk.DrawingArea.__init__(self)
        self.set_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK |
                        Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)

        self.connect("draw", self.expose)
        self.connect("button_press_event", self.mouse_down)
        self.connect("button_release_event", self.mouse_up)
        self.connect("motion_notify_event", self.mouse_hover)
        self.connect("leave_notify_event", self.mouse_leave)

        self.colors = [[115.0 / 255, 210.0 / 255, 22.0 / 255],
                       [237.0 / 255, 212.0 / 255, 0.0 / 255],
                       [204.0 / 255, 0.0 / 255, 0.0 / 255]]
        self.button_state = [[0] * 7 for dummy in xrange(24)]

        self.start_point = [0, 0]
        self.hover_point = [-1, -1]
        self.hover_label = hover
        self.hover_days = DAYS
        self.mouse_press = False
        self.set_size_request(350, 150)

    def set_button_state(self, state):
        self.button_state = []
        for s in state:
            self.button_state.append(list(s))
        log.debug(self.button_state)

    # redraw the whole thing
    def expose(self, widget, event):
        self.context = self.window.cairo_create()
        alloc = Gtk.Window.get_allocation(widget)
        x, y, w, h = alloc.x, alloc.y, alloc.width, alloc.height
        width = w
        height = h
        self.context.rectangle(0, 0, width, height)
        self.context.clip()

        for y in xrange(7):
            for x in xrange(24):
                self.context.set_source_rgba(self.colors[self.button_state[x][y]][0],
                                             self.colors[self.button_state[x][y]][1],
                                             self.colors[self.button_state[x][y]][2], 0.7)
                self.context.rectangle(width * (6 * x / 145.0 + 1 / 145.0), height * (6 * y / 43.0 + 1 / 43.0),
                                       5 * width / 145.0, 5 * height / 43.0)
                self.context.fill_preserve()
                self.context.set_source_rgba(0.5, 0.5, 0.5, 0.5)
                self.context.stroke()

    # coordinates --> which box
    def get_point(self, event):
        alloc = Gtk.Window.get_allocation(self)
        x, y, w, h = alloc.x, alloc.y, alloc.width, alloc.height
        width = w
        height = h
        # size = self.window.get_size()
        x = int((event.x - width * 0.5 / 145.0) / (6 * width / 145.0))
        y = int((event.y - height * 0.5 / 43.0) / (6 * height / 43.0))

        if x > 23:
            x = 23
        elif x < 0:
            x = 0
        if y > 6:
            y = 6
        elif y < 0:
            y = 0

        return [x, y]

    # mouse down
    def mouse_down(self, widget, event):
        self.mouse_press = True
        self.start_point = self.get_point(event)

    # if the same box -> change it
    def mouse_up(self, widget, event):
        self.mouse_press = False
        end_point = self.get_point(event)

        # change color on mouseclick depending on the button
        if end_point[0] is self.start_point[0] and end_point[1] is self.start_point[1]:
            if event.button == 1:
                self.button_state[end_point[0]][end_point[1]] += 1
                if self.button_state[end_point[0]][end_point[1]] > 2:
                    self.button_state[end_point[0]][end_point[1]] = 0
            elif event.button == 3:
                self.button_state[end_point[0]][end_point[1]] -= 1
                if self.button_state[end_point[0]][end_point[1]] < 0:
                    self.button_state[end_point[0]][end_point[1]] = 2
            self.queue_draw()

    # if box changed and mouse is pressed draw all boxes from start point to end point
    # set hover text etc..
    def mouse_hover(self, widget, event):
        if self.get_point(event) != self.hover_point:
            self.hover_point = self.get_point(event)

            self.hover_label.set_text(self.hover_days[self.hover_point[1]] + " " + str(self.hover_point[0])
                                      + ":00 - " + str(self.hover_point[0]) + ":59")

            if self.mouse_press:
                points = [[self.hover_point[0], self.start_point[0]], [self.hover_point[1], self.start_point[1]]]

                for x in xrange(min(points[0]), max(points[0]) + 1):
                    for y in xrange(min(points[1]), max(points[1]) + 1):
                        self.button_state[x][y] = self.button_state[self.start_point[0]][self.start_point[1]]

                self.queue_draw()

    # clear hover text on mouse leave
    def mouse_leave(self, widget, event):
        self.hover_label.set_text("")
        self.hover_point = [-1, -1]


class GtkUI(GtkPluginBase):
    def enable(self):
        self.create_prefs_page()

        component.get("PluginManager").register_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").register_hook("on_show_prefs", self.on_show_prefs)

        self.status_item = component.get("StatusBar").add_item(
            image=get_resource("green.png"),
            text="",
            callback=self.on_status_item_clicked,
            tooltip="Scheduler")

        def on_get_state(state):
            self.status_item.set_image_from_file(get_resource(state.lower() + ".png"))

        self.state_deferred = client.scheduler.get_state().addCallback(on_get_state)
        client.register_event_handler("SchedulerEvent", self.on_scheduler_event)

    def disable(self):
        component.get("Preferences").remove_page(_("Scheduler"))
        # Remove status item
        component.get("StatusBar").remove_item(self.status_item)
        del self.status_item

        component.get("PluginManager").deregister_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").deregister_hook("on_show_prefs", self.on_show_prefs)

    def on_apply_prefs(self):
        log.debug("applying prefs for Scheduler")
        config = {}
        config["low_down"] = self.spin_download.get_value()
        config["low_up"] = self.spin_upload.get_value()
        config["low_active"] = self.spin_active.get_value_as_int()
        config["low_active_down"] = self.spin_active_down.get_value_as_int()
        config["low_active_up"] = self.spin_active_up.get_value_as_int()
        config["button_state"] = self.scheduler_select.button_state
        client.scheduler.set_config(config)

    def on_show_prefs(self):
        def on_get_config(config):
            log.debug("config: %s", config)
            self.scheduler_select.set_button_state(config["button_state"])
            self.spin_download.set_value(config["low_down"])
            self.spin_upload.set_value(config["low_up"])
            self.spin_active.set_value(config["low_active"])
            self.spin_active_down.set_value(config["low_active_down"])
            self.spin_active_up.set_value(config["low_active_up"])

        client.scheduler.get_config().addCallback(on_get_config)

    def on_scheduler_event(self, state):
        def on_state_deferred(s):
            self.status_item.set_image_from_file(get_resource(state.lower() + ".png"))

        self.state_deferred.addCallback(on_state_deferred)

    def on_status_item_clicked(self, widget, event):
        component.get("Preferences").show("Scheduler")

    # Configuration dialog
    def create_prefs_page(self):
        # Select Widget
        hover = Gtk.Label()
        self.scheduler_select = SchedulerSelectWidget(hover)

        vbox = Gtk.VBox(False, 5)
        hbox = Gtk.HBox(False, 5)
        vbox_days = Gtk.VBox()
        for day in DAYS:
            vbox_days.pack_start(Gtk.Label(day, True, True, 0))
        hbox.pack_start(vbox_days, False, False)
        hbox.pack_start(self.scheduler_select, True, True)
        frame = Gtk.Frame()
        label = Gtk.Label()
        label.set_markup("<b>Schedule</b>")
        frame.set_label_widget(label)
        frame.set_shadow_type(Gtk.ShadowType.NONE)
        frame.add(hbox)

        vbox.pack_start(frame, True, True)
        vbox.pack_start(hover, True, True, 0)

        table = Gtk.Table(3, 4)

        label = Gtk.Label(label=_("Download Limit:"))
        label.set_alignment(0.0, 0.6)
        table.attach(label, 0, 1, 0, 1, Gtk.AttachOptions.FILL)
        self.spin_download = Gtk.SpinButton()
        self.spin_download.set_numeric(True)
        self.spin_download.set_range(-1.0, 99999.0)
        self.spin_download.set_increments(1, 10)
        table.attach(self.spin_download, 1, 2, 0, 1, Gtk.AttachOptions.FILL)

        label = Gtk.Label(label=_("Upload Limit:"))
        label.set_alignment(0.0, 0.6)
        table.attach(label, 0, 1, 1, 2, Gtk.AttachOptions.FILL)
        self.spin_upload = Gtk.SpinButton()
        self.spin_upload.set_numeric(True)
        self.spin_upload.set_range(-1.0, 99999.0)
        self.spin_upload.set_increments(1, 10)
        table.attach(self.spin_upload, 1, 2, 1, 2, Gtk.AttachOptions.FILL)

        label = Gtk.Label(label=_("Active Torrents:"))
        label.set_alignment(0.0, 0.6)
        table.attach(label, 2, 3, 0, 1, Gtk.AttachOptions.FILL)
        self.spin_active = Gtk.SpinButton()
        self.spin_active.set_numeric(True)
        self.spin_active.set_range(-1, 9999)
        self.spin_active.set_increments(1, 10)
        table.attach(self.spin_active, 3, 4, 0, 1, Gtk.AttachOptions.FILL)

        label = Gtk.Label(label=_("Active Downloading:"))
        label.set_alignment(0.0, 0.6)
        table.attach(label, 2, 3, 1, 2, Gtk.AttachOptions.FILL)
        self.spin_active_down = Gtk.SpinButton()
        self.spin_active_down.set_numeric(True)
        self.spin_active_down.set_range(-1, 9999)
        self.spin_active_down.set_increments(1, 10)
        table.attach(self.spin_active_down, 3, 4, 1, 2, Gtk.AttachOptions.FILL)

        label = Gtk.Label(label=_("Active Seeding:"))
        label.set_alignment(0.0, 0.6)
        table.attach(label, 2, 3, 2, 3, Gtk.AttachOptions.FILL)
        self.spin_active_up = Gtk.SpinButton()
        self.spin_active_up.set_numeric(True)
        self.spin_active_up.set_range(-1, 9999)
        self.spin_active_up.set_increments(1, 10)
        table.attach(self.spin_active_up, 3, 4, 2, 3, Gtk.AttachOptions.FILL)

        eventbox = Gtk.EventBox()
        eventbox.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse("#EDD400"))
        eventbox.add(table)
        frame = Gtk.Frame()
        label = Gtk.Label()
        label.set_markup(_("<b>Slow Settings</b>"))
        frame.set_label_widget(label)
        frame.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse("#CDB400"))
        frame.set_border_width(2)
        frame.add(eventbox)
        vbox.pack_start(frame, False, False)

        vbox.show_all()
        component.get("Preferences").add_page(_("Scheduler"), vbox)
