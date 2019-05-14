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

from __future__ import division, unicode_literals

import logging

from gi.repository import Gdk, Gtk

import deluge.component as component
from deluge.plugins.pluginbase import Gtk3PluginBase
from deluge.ui.client import client

from .common import get_resource

log = logging.getLogger(__name__)

DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


class SchedulerSelectWidget(Gtk.DrawingArea):
    def __init__(self, hover):
        super(SchedulerSelectWidget, self).__init__()
        self.set_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.LEAVE_NOTIFY_MASK
        )

        self.connect('draw', self.draw)
        self.connect('button_press_event', self.mouse_down)
        self.connect('button_release_event', self.mouse_up)
        self.connect('motion_notify_event', self.mouse_hover)
        self.connect('leave_notify_event', self.mouse_leave)

        self.colors = [
            [115 / 255, 210 / 255, 22 / 255],
            [237 / 255, 212 / 255, 0 / 255],
            [204 / 255, 0 / 255, 0 / 255],
        ]
        self.button_state = [[0] * 7 for dummy in range(24)]

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
    def draw(self, widget, context):
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()
        context.rectangle(0, 0, width, height)
        context.clip()

        for y in range(7):
            for x in range(24):
                context.set_source_rgba(
                    self.colors[self.button_state[x][y]][0],
                    self.colors[self.button_state[x][y]][1],
                    self.colors[self.button_state[x][y]][2],
                    0.5,
                )
                context.rectangle(
                    width * (6 * x / 145 + 1 / 145),
                    height * (6 * y / 43 + 1 / 43),
                    6 * width / 145,
                    5 * height / 43,
                )
                context.fill_preserve()
                context.set_source_rgba(0, 0, 0, 0.7)
                context.set_line_width(1)
                context.stroke()

    # coordinates --> which box
    def get_point(self, event):
        width = self.get_allocated_width()
        height = self.get_allocated_height()
        x = int((event.x - width * 0.5 / 145) / (6 * width / 145))
        y = int((event.y - height * 0.5 / 43) / (6 * height / 43))

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

            self.hover_label.set_text(
                self.hover_days[self.hover_point[1]]
                + ' '
                + str(self.hover_point[0])
                + ':00 - '
                + str(self.hover_point[0])
                + ':59'
            )

            if self.mouse_press:
                points = [
                    [self.hover_point[0], self.start_point[0]],
                    [self.hover_point[1], self.start_point[1]],
                ]

                for x in range(min(points[0]), max(points[0]) + 1):
                    for y in range(min(points[1]), max(points[1]) + 1):
                        self.button_state[x][y] = self.button_state[
                            self.start_point[0]
                        ][self.start_point[1]]

                self.queue_draw()

    # clear hover text on mouse leave
    def mouse_leave(self, widget, event):
        self.hover_label.set_text('')
        self.hover_point = [-1, -1]


class GtkUI(Gtk3PluginBase):
    def enable(self):
        self.create_prefs_page()

        component.get('PluginManager').register_hook(
            'on_apply_prefs', self.on_apply_prefs
        )
        component.get('PluginManager').register_hook(
            'on_show_prefs', self.on_show_prefs
        )
        self.statusbar = component.get('StatusBar')
        self.status_item = self.statusbar.add_item(
            image=get_resource('green.svg'),
            text='',
            callback=self.on_status_item_clicked,
            tooltip='Scheduler',
        )

        def on_state_deferred(state):
            self.state = state
            self.on_scheduler_event(state)

        self.on_show_prefs()

        client.scheduler.get_state().addCallback(on_state_deferred)
        client.register_event_handler('SchedulerEvent', self.on_scheduler_event)

    def disable(self):
        component.get('Preferences').remove_page(_('Scheduler'))
        # Reset statusbar dict.
        self.statusbar.config_value_changed_dict[
            'max_download_speed'
        ] = self.statusbar._on_max_download_speed
        self.statusbar.config_value_changed_dict[
            'max_upload_speed'
        ] = self.statusbar._on_max_upload_speed
        # Remove statusbar item.
        self.statusbar.remove_item(self.status_item)
        del self.status_item

        component.get('PluginManager').deregister_hook(
            'on_apply_prefs', self.on_apply_prefs
        )
        component.get('PluginManager').deregister_hook(
            'on_show_prefs', self.on_show_prefs
        )

    def on_apply_prefs(self):
        log.debug('applying prefs for Scheduler')
        config = {}
        config['low_down'] = self.spin_download.get_value()
        config['low_up'] = self.spin_upload.get_value()
        config['low_active'] = self.spin_active.get_value_as_int()
        config['low_active_down'] = self.spin_active_down.get_value_as_int()
        config['low_active_up'] = self.spin_active_up.get_value_as_int()
        config['button_state'] = self.scheduler_select.button_state
        client.scheduler.set_config(config)

    def on_show_prefs(self):
        def on_get_config(config):
            log.debug('config: %s', config)
            self.scheduler_select.set_button_state(config['button_state'])
            self.spin_download.set_value(config['low_down'])
            self.spin_upload.set_value(config['low_up'])
            self.spin_active.set_value(config['low_active'])
            self.spin_active_down.set_value(config['low_active_down'])
            self.spin_active_up.set_value(config['low_active_up'])

        client.scheduler.get_config().addCallback(on_get_config)

    def on_scheduler_event(self, state):
        self.state = state
        self.status_item.set_image_from_file(get_resource(self.state.lower() + '.svg'))
        if self.state == 'Yellow':
            # Prevent func calls in Statusbar if the config changes.
            self.statusbar.config_value_changed_dict.pop('max_download_speed', None)
            self.statusbar.config_value_changed_dict.pop('max_upload_speed', None)
            try:
                self.statusbar._on_max_download_speed(self.spin_download.get_value())
                self.statusbar._on_max_upload_speed(self.spin_upload.get_value())
            except AttributeError:
                # Skip error due to Plugin being enabled before statusbar items created on startup.
                pass
        else:
            self.statusbar.config_value_changed_dict[
                'max_download_speed'
            ] = self.statusbar._on_max_download_speed
            self.statusbar.config_value_changed_dict[
                'max_upload_speed'
            ] = self.statusbar._on_max_upload_speed

            def update_config_values(config):
                try:
                    self.statusbar._on_max_download_speed(config['max_download_speed'])
                    self.statusbar._on_max_upload_speed(config['max_upload_speed'])
                except AttributeError:
                    # Skip error due to Plugin being enabled before statusbar items created on startup.
                    pass

            client.core.get_config_values(
                ['max_download_speed', 'max_upload_speed']
            ).addCallback(update_config_values)

    def on_status_item_clicked(self, widget, event):
        component.get('Preferences').show('Scheduler')

    # Configuration dialog
    def create_prefs_page(self):
        # Select Widget
        hover = Gtk.Label()
        self.scheduler_select = SchedulerSelectWidget(hover)

        vbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, spacing=5)
        hbox = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, spacing=5)
        vbox_days = Gtk.Box.new(Gtk.Orientation.VERTICAL, spacing=0)
        for day in DAYS:
            vbox_days.pack_start(Gtk.Label(day, xalign=0), True, False, 0)
        hbox.pack_start(vbox_days, False, False, 15)
        hbox.pack_start(self.scheduler_select, True, True, 0)
        frame = Gtk.Frame()
        label = Gtk.Label()
        label.set_markup(_('<b>Schedule</b>'))
        frame.set_label_widget(label)
        frame.set_shadow_type(Gtk.ShadowType.NONE)
        frame.set_margin_left(15)
        frame.add(hbox)

        vbox.pack_start(frame, False, False, 0)
        vbox.pack_start(hover, False, False, 0)

        table = Gtk.Table(5, 2)
        table.set_margin_left(15)

        label = Gtk.Label(_('Download Limit:'))
        label.set_alignment(0.0, 0.6)
        table.attach_defaults(label, 0, 1, 0, 1)
        self.spin_download = Gtk.SpinButton()
        self.spin_download.set_numeric(True)
        self.spin_download.set_range(-1.0, 99999.0)
        self.spin_download.set_increments(1, 10)
        table.attach_defaults(self.spin_download, 1, 2, 0, 1)

        label = Gtk.Label(_('Upload Limit:'))
        label.set_alignment(0.0, 0.6)
        table.attach_defaults(label, 0, 1, 1, 2)
        self.spin_upload = Gtk.SpinButton()
        self.spin_upload.set_numeric(True)
        self.spin_upload.set_range(-1.0, 99999.0)
        self.spin_upload.set_increments(1, 10)
        table.attach_defaults(self.spin_upload, 1, 2, 1, 2)

        label = Gtk.Label(_('Active Torrents:'))
        label.set_alignment(0.0, 0.6)
        table.attach_defaults(label, 0, 1, 2, 3)
        self.spin_active = Gtk.SpinButton()
        self.spin_active.set_numeric(True)
        self.spin_active.set_range(-1, 9999)
        self.spin_active.set_increments(1, 10)
        table.attach_defaults(self.spin_active, 1, 2, 2, 3)

        label = Gtk.Label(_('Active Downloading:'))
        label.set_alignment(0.0, 0.6)
        table.attach_defaults(label, 0, 1, 3, 4)
        self.spin_active_down = Gtk.SpinButton()
        self.spin_active_down.set_numeric(True)
        self.spin_active_down.set_range(-1, 9999)
        self.spin_active_down.set_increments(1, 10)
        table.attach_defaults(self.spin_active_down, 1, 2, 3, 4)

        label = Gtk.Label(_('Active Seeding:'))
        label.set_alignment(0.0, 0.6)
        table.attach_defaults(label, 0, 1, 4, 5)
        self.spin_active_up = Gtk.SpinButton()
        self.spin_active_up.set_numeric(True)
        self.spin_active_up.set_range(-1, 9999)
        self.spin_active_up.set_increments(1, 10)
        table.attach_defaults(self.spin_active_up, 1, 2, 4, 5)

        eventbox = Gtk.EventBox()
        eventbox.add(table)
        frame = Gtk.Frame()
        label = Gtk.Label()
        label.set_markup(_('<b>Slow Settings</b>'))
        label.modify_bg(Gtk.StateFlags.NORMAL, Gdk.color_parse('#EDD400'))
        frame.set_label_widget(label)
        frame.set_margin_left(15)
        frame.set_border_width(2)
        frame.add(eventbox)
        vbox.pack_start(frame, False, False, 0)

        vbox.show_all()
        component.get('Preferences').add_page(_('Scheduler'), vbox)
