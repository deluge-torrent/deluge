# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, 2008 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import print_function

import warnings
from functools import partial

import gobject
import gtk

import deluge.common as common
import deluge.component as component

# Status icons.. Create them from file only once to avoid constantly
# re-creating them.
icon_downloading = gtk.gdk.pixbuf_new_from_file(common.get_pixmap("downloading16.png"))
icon_seeding = gtk.gdk.pixbuf_new_from_file(common.get_pixmap("seeding16.png"))
icon_inactive = gtk.gdk.pixbuf_new_from_file(common.get_pixmap("inactive16.png"))
icon_alert = gtk.gdk.pixbuf_new_from_file(common.get_pixmap("alert16.png"))
icon_queued = gtk.gdk.pixbuf_new_from_file(common.get_pixmap("queued16.png"))
icon_checking = gtk.gdk.pixbuf_new_from_file(common.get_pixmap("checking16.png"))

# Holds the info for which status icon to display based on TORRENT_STATE
ICON_STATE = {
    "Allocating": icon_checking,
    "Checking": icon_checking,
    "Downloading": icon_downloading,
    "Seeding": icon_seeding,
    "Paused": icon_inactive,
    "Error": icon_alert,
    "Queued": icon_queued,
    "Moving": icon_checking
}

# Cache the key used to calculate the current value set for the specific cell
# renderer. This is much cheaper than fetch the current value and test if
# it's equal.
func_last_value = {"cell_data_speed_down": None,
                   "cell_data_speed_up": None,
                   "cell_data_time": None,
                   "cell_data_ratio_seeds_peers": None,
                   "cell_data_ratio_ratio": None,
                   "cell_data_ratio_avail": None,
                   "cell_data_date_added": None,
                   "cell_data_date_completed": None,
                   "cell_data_date_or_never": None,
                   "cell_data_speed_limit_down": None,
                   "cell_data_speed_limit_up": None,
                   "cell_data_trackericon": None,
                   "cell_data_statusicon": None,
                   "cell_data_queue": None,
                   "cell_data_progress": [None, None],
                   }


def cell_data_statusicon(column, cell, model, row, data):
    """Display text with an icon"""
    try:
        state = model.get_value(row, data)

        if func_last_value["cell_data_statusicon"] == state:
            return
        func_last_value["cell_data_statusicon"] = state

        icon = ICON_STATE[state]

        # Supress Warning: g_object_set_qdata: assertion `G_IS_OBJECT (object)' failed
        original_filters = warnings.filters[:]
        warnings.simplefilter("ignore")
        try:
            cell.set_property("pixbuf", icon)
        finally:
            warnings.filters = original_filters

    except KeyError:
        pass


def create_blank_pixbuf():
    i = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, 16, 16)
    i.fill(0x00000000)
    return i


def set_icon(icon, cell):
    if icon:
        pixbuf = icon.get_cached_icon()
        if pixbuf is None:
            try:
                pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(icon.get_filename(), 16, 16)
            except gobject.GError:
                # Failed to load the pixbuf (Bad image file), so set a blank pixbuf
                pixbuf = create_blank_pixbuf()
            finally:
                icon.set_cached_icon(pixbuf)
    else:
        pixbuf = create_blank_pixbuf()

    # Suppress Warning: g_object_set_qdata: assertion `G_IS_OBJECT (object)' failed
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cell.set_property("pixbuf", pixbuf)


def cell_data_trackericon(column, cell, model, row, data):
    host = model[row][data]

    if func_last_value["cell_data_trackericon"] == host:
        return
    if host:
        if not component.get("TrackerIcons").has(host):
            # Set blank icon while waiting for the icon to be loaded
            set_icon(None, cell)
            component.get("TrackerIcons").fetch(host)
            func_last_value["cell_data_trackericon"] = None
        else:
            set_icon(component.get("TrackerIcons").get(host), cell)
            # Only set the last value when we have found the icon
            func_last_value["cell_data_trackericon"] = host
    else:
        set_icon(None, cell)
        func_last_value["cell_data_trackericon"] = None


def cell_data_progress(column, cell, model, row, data):
    """Display progress bar with text"""
    (value, state_str) = model.get(row, *data)
    if func_last_value["cell_data_progress"][0] != value:
        func_last_value["cell_data_progress"][0] = value
        cell.set_property("value", value)

    # Marked for translate states text are in filtertreeview
    textstr = _(state_str)
    if state_str != "Seeding" and value < 100:
        textstr = "%s %.2f%%" % (textstr, value)

    if func_last_value["cell_data_progress"][1] != textstr:
        func_last_value["cell_data_progress"][1] = textstr
        cell.set_property("text", textstr)


def cell_data_queue(column, cell, model, row, data):
    value = model.get_value(row, data)

    if func_last_value["cell_data_queue"] == value:
        return
    func_last_value["cell_data_queue"] = value

    if value < 0:
        cell.set_property("text", "")
    else:
        cell.set_property("text", str(value + 1))


def cell_data_speed(cell, model, row, data, cache_key):
    """Display value as a speed, eg. 2 KiB/s"""
    try:
        speed = model.get_value(row, data)
    except AttributeError:
        print("AttributeError")
        import traceback
        traceback.print_exc()
    if func_last_value[cache_key] == speed:
        return
    func_last_value[cache_key] = speed

    speed_str = ""
    if speed > 0:
        speed_str = common.fspeed(speed)
    cell.set_property('text', speed_str)


def cell_data_speed_down(column, cell, model, row, data):
    """Display value as a speed, eg. 2 KiB/s"""
    cell_data_speed(cell, model, row, data, "cell_data_speed_down")


def cell_data_speed_up(column, cell, model, row, data):
    """Display value as a speed, eg. 2 KiB/s"""
    cell_data_speed(cell, model, row, data, "cell_data_speed_up")


def cell_data_speed_limit(cell, model, row, data, cache_key):
    """Display value as a speed, eg. 2 KiB/s"""
    speed = model.get_value(row, data)

    if func_last_value[cache_key] == speed:
        return
    func_last_value[cache_key] = speed

    speed_str = ""
    if speed > 0:
        speed_str = common.fspeed(speed * 1024)
    cell.set_property('text', speed_str)


def cell_data_speed_limit_down(column, cell, model, row, data):
    cell_data_speed_limit(cell, model, row, data, "cell_data_speed_limit_down")


def cell_data_speed_limit_up(column, cell, model, row, data):
    cell_data_speed_limit(cell, model, row, data, "cell_data_speed_limit_up")


def cell_data_size(column, cell, model, row, data):
    """Display value in terms of size, eg. 2 MB"""
    size = model.get_value(row, data)
    cell.set_property('text', common.fsize(size))


def cell_data_peer(column, cell, model, row, data):
    """Display values as 'value1 (value2)'"""
    (first, second) = model.get(row, *data)
    # Only display a (total) if second is greater than -1
    if second > -1:
        cell.set_property('text', '%d (%d)' % (first, second))
    else:
        cell.set_property('text', '%d' % first)


def cell_data_time(column, cell, model, row, data):
    """Display value as time, eg 1m10s"""
    time = model.get_value(row, data)
    if func_last_value["cell_data_time"] == time:
        return
    func_last_value["cell_data_time"] = time

    if time <= 0:
        time_str = ""
    else:
        time_str = common.ftime(time)
    cell.set_property('text', time_str)


def cell_data_ratio(cell, model, row, data, cache_key):
    """Display value as a ratio with a precision of 3."""
    ratio = model.get_value(row, data)
    # Previous value in cell is the same as for this value, so ignore
    if func_last_value[cache_key] == ratio:
        return
    func_last_value[cache_key] = ratio
    cell.set_property('text', "∞" if ratio < 0 else "%.3f" % ratio)


def cell_data_ratio_seeds_peers(column, cell, model, row, data):
    cell_data_ratio(cell, model, row, data, "cell_data_ratio_seeds_peers")


def cell_data_ratio_ratio(column, cell, model, row, data):
    cell_data_ratio(cell, model, row, data, "cell_data_ratio_ratio")


def cell_data_ratio_avail(column, cell, model, row, data):
    cell_data_ratio(cell, model, row, data, "cell_data_ratio_avail")


def cell_data_date(column, cell, model, row, data, key):
    """Display value as date, eg 05/05/08"""
    date = model.get_value(row, data)

    if func_last_value[key] == date:
        return
    func_last_value[key] = date

    date_str = common.fdate(date) if date > 0.0 else ""
    cell.set_property('text', date_str)

cell_data_date_added = partial(cell_data_date, key="cell_data_date_added")
cell_data_date_completed = partial(cell_data_date, key="cell_data_date_completed")


def cell_data_date_or_never(column, cell, model, row, data):
    """Display value as date, eg 05/05/08 or Never"""
    value = model.get_value(row, data)

    if func_last_value["cell_data_date_or_never"] == value:
        return
    func_last_value["cell_data_date_or_never"] = value

    date_str = common.fdate(value) if value > 0.0 else _("Never")
    cell.set_property('text', date_str)
