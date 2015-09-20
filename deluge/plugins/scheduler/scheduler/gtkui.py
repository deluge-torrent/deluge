#
# gtkui.py
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
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

import gtk

from deluge.log import LOG as log
from deluge.ui.client import client
from deluge.plugins.pluginbase import GtkPluginBase
import deluge.component as component
import deluge.common

from common import get_resource

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

class SchedulerSelectWidget(gtk.DrawingArea):
    def __init__(self, hover):
        gtk.DrawingArea.__init__(self)
        self.set_events(gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK | gtk.gdk.POINTER_MOTION_MASK | gtk.gdk.LEAVE_NOTIFY_MASK)

        self.connect("expose_event", self.expose)
        self.connect("button_press_event", self.mouse_down)
        self.connect("button_release_event", self.mouse_up)
        self.connect("motion_notify_event", self.mouse_hover)
        self.connect("leave_notify_event", self.mouse_leave)

        self.colors = [[115.0/255, 210.0/255, 22.0/255], [237.0/255, 212.0/255, 0.0/255], [204.0/255, 0.0/255, 0.0/255]]
        self.button_state = [[0] * 7 for dummy in xrange(24)]

        self.start_point = [0,0]
        self.hover_point = [-1,-1]
        self.hover_label = hover
        self.hover_days = DAYS
        self.mouse_press = False
        self.set_size_request(350,150)

    def set_button_state(self, state):
        self.button_state = []
        for s in state:
            self.button_state.append(list(s))
        log.debug(self.button_state)

    #redraw the whole thing
    def expose(self, widget, event):
        context = self.window.cairo_create()
        context.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
        context.clip()

        width = self.window.get_size()[0]
        height = self.window.get_size()[1]

        for y in xrange(7):
            for x in xrange(24):
                context.set_source_rgba(self.colors[self.button_state[x][y]][0], self.colors[self.button_state[x][y]][1], self.colors[self.button_state[x][y]][2], 0.7)
                context.rectangle(width*(6*x/145.0+1/145.0), height*(6*y/43.0+1/43.0), 5*width/145.0, 5*height/43.0)
                context.fill_preserve()
                context.set_source_rgba(0.5, 0.5, 0.5, 0.5)
                context.stroke()

    #coordinates --> which box
    def get_point(self, event):
        size = self.window.get_size()
        x = int((event.x-size[0]*0.5/145.0)/(6*size[0]/145.0))
        y = int((event.y-size[1]*0.5/43.0)/(6*size[1]/43.0))

        if x > 23: x = 23
        elif x < 0: x = 0
        if y > 6: y = 6
        elif y < 0: y = 0

        return [x,y]

    #mouse down
    def mouse_down(self, widget, event):
        self.mouse_press = True
        self.start_point = self.get_point(event)

    #if the same box -> change it
    def mouse_up(self, widget, event):
        self.mouse_press = False
        end_point = self.get_point(event)

        #change color on mouseclick depending on the button
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

    #if box changed and mouse is pressed draw all boxes from start point to end point
    #set hover text etc..
    def mouse_hover(self, widget, event):
        if self.get_point(event) != self.hover_point:
            self.hover_point = self.get_point(event)

            self.hover_label.set_text(self.hover_days[self.hover_point[1]] + " " + str(self.hover_point[0]) + ":00 - " + str(self.hover_point[0]) + ":59")

            if self.mouse_press == True:
                points = [[self.hover_point[0], self.start_point[0]], [self.hover_point[1], self.start_point[1]]]

                for x in xrange(min(points[0]), max(points[0])+1):
                    for y in xrange(min(points[1]), max(points[1])+1):
                        self.button_state[x][y] = self.button_state[self.start_point[0]][self.start_point[1]]

                self.queue_draw()

    #clear hover text on mouse leave
    def mouse_leave(self, widget, event):
        self.hover_label.set_text("")
        self.hover_point = [-1,-1]

class GtkUI(GtkPluginBase):
    def enable(self):
        self.create_prefs_page()

        component.get("PluginManager").register_hook("on_apply_prefs", self.on_apply_prefs)
        component.get("PluginManager").register_hook("on_show_prefs", self.on_show_prefs)
        self.statusbar = component.get("StatusBar")
        self.status_item = self.statusbar.add_item(
            image=get_resource("green.png"),
            text="",
            callback=self.on_status_item_clicked,
            tooltip="Scheduler")

        def on_state_deferred(state):
            self.state = state
            self.on_scheduler_event(state)
        client.scheduler.get_state().addCallback(on_state_deferred)
        client.register_event_handler("SchedulerEvent", self.on_scheduler_event)

    def disable(self):
        component.get("Preferences").remove_page(_("Scheduler"))
        # Reset statusbar dict.
        self.statusbar.config_value_changed_dict["max_download_speed"] = self.statusbar._on_max_download_speed
        self.statusbar.config_value_changed_dict["max_upload_speed"] = self.statusbar._on_max_upload_speed
        # Remove statusbar item.
        self.statusbar.remove_item(self.status_item)
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
        self.state = state
        self.status_item.set_image_from_file(get_resource(self.state.lower() + ".png"))
        if self.state == "Yellow":
            # Prevent func calls in Statusbar if the config changes.
            self.statusbar.config_value_changed_dict.pop("max_download_speed", None)
            self.statusbar.config_value_changed_dict.pop("max_upload_speed", None)
            try:
                self.statusbar._on_max_download_speed(self.spin_download.get_value())
                self.statusbar._on_max_upload_speed(self.spin_upload.get_value())
            except AttributeError:
                # Skip error due to Plugin being enabled before statusbar items created on startup.
                pass
        else:
            self.statusbar.config_value_changed_dict["max_download_speed"] = self.statusbar._on_max_download_speed
            self.statusbar.config_value_changed_dict["max_upload_speed"] = self.statusbar._on_max_upload_speed

            def update_config_values(config):
                try:
                    self.statusbar._on_max_download_speed(config["max_download_speed"])
                    self.statusbar._on_max_upload_speed(config["max_upload_speed"])
                except AttributeError:
                    # Skip error due to Plugin being enabled before statusbar items created on startup.
                    pass
            client.core.get_config_values(["max_download_speed", "max_upload_speed"]).addCallback(update_config_values)

    def on_status_item_clicked(self, widget, event):
        component.get("Preferences").show("Scheduler")

    #Configuration dialog
    def create_prefs_page(self):
        #Select Widget
        hover = gtk.Label()
        self.scheduler_select = SchedulerSelectWidget(hover)

        vbox = gtk.VBox(False, 5)
        hbox = gtk.HBox(False, 5)
        vbox_days = gtk.VBox()
        for day in DAYS:
            vbox_days.pack_start(gtk.Label(day))
        hbox.pack_start(vbox_days, False, False)
        hbox.pack_start(self.scheduler_select, True, True)
        frame = gtk.Frame()
        label = gtk.Label()
        label.set_markup("<b>Schedule</b>")
        frame.set_label_widget(label)
        frame.set_shadow_type(gtk.SHADOW_NONE)
        frame.add(hbox)

        vbox.pack_start(frame, True, True)
        vbox.pack_start(hover)

        table = gtk.Table(3, 4)

        label = gtk.Label(_("Download Limit:"))
        label.set_alignment(0.0, 0.6)
        table.attach(label, 0, 1, 0, 1, gtk.FILL)
        self.spin_download = gtk.SpinButton()
        self.spin_download.set_numeric(True)
        self.spin_download.set_range(-1.0, 99999.0)
        self.spin_download.set_increments(1, 10)
        table.attach(self.spin_download, 1, 2, 0, 1, gtk.FILL)

        label = gtk.Label(_("Upload Limit:"))
        label.set_alignment(0.0, 0.6)
        table.attach(label, 0, 1, 1, 2, gtk.FILL)
        self.spin_upload = gtk.SpinButton()
        self.spin_upload.set_numeric(True)
        self.spin_upload.set_range(-1.0, 99999.0)
        self.spin_upload.set_increments(1, 10)
        table.attach(self.spin_upload, 1, 2, 1, 2, gtk.FILL)

        label = gtk.Label(_("Active Torrents:"))
        label.set_alignment(0.0, 0.6)
        table.attach(label, 2, 3, 0, 1, gtk.FILL)
        self.spin_active = gtk.SpinButton()
        self.spin_active.set_numeric(True)
        self.spin_active.set_range(-1, 9999)
        self.spin_active.set_increments(1, 10)
        table.attach(self.spin_active, 3, 4, 0, 1, gtk.FILL)

        label = gtk.Label(_("Active Downloading:"))
        label.set_alignment(0.0, 0.6)
        table.attach(label, 2, 3, 1, 2, gtk.FILL)
        self.spin_active_down = gtk.SpinButton()
        self.spin_active_down.set_numeric(True)
        self.spin_active_down.set_range(-1, 9999)
        self.spin_active_down.set_increments(1, 10)
        table.attach(self.spin_active_down, 3, 4, 1, 2, gtk.FILL)

        label = gtk.Label(_("Active Seeding:"))
        label.set_alignment(0.0, 0.6)
        table.attach(label, 2, 3, 2, 3, gtk.FILL)
        self.spin_active_up = gtk.SpinButton()
        self.spin_active_up.set_numeric(True)
        self.spin_active_up.set_range(-1, 9999)
        self.spin_active_up.set_increments(1, 10)
        table.attach(self.spin_active_up, 3, 4, 2, 3, gtk.FILL)

        eventbox = gtk.EventBox()
        eventbox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#EDD400"))
        eventbox.add(table)
        frame = gtk.Frame()
        label = gtk.Label()
        label.set_markup(_("<b>Slow Settings</b>"))
        frame.set_label_widget(label)
        frame.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#CDB400"))
        frame.set_border_width(2)
        frame.add(eventbox)
        vbox.pack_start(frame, False, False)

        vbox.show_all()
        component.get("Preferences").add_page(_("Scheduler"), vbox)
