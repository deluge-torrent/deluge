# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Ian Martin <ianmartin@cantab.net>
# Copyright (C) 2008 Damien Churchill <damoxc@gmail.com>
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007 Marcos Mobley <markybob@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

"""
port of old plugin by markybob.
"""

from __future__ import division, unicode_literals

import logging
import math
import time

import gi

gi.require_foreign('cairo')  # NOQA: E402

import cairo  # isort:skip (gi checks required before import).

log = logging.getLogger(__name__)

black = (0, 0, 0)
gray = (0.75, 0.75, 0.75)
white = (1.0, 1.0, 1.0)
darkred = (0.65, 0, 0)
red = (1.0, 0, 0)
green = (0, 1.0, 0)
blue = (0, 0, 1.0)
orange = (1.0, 0.74, 0)


def default_formatter(value):
    return str(value)


def size_formatter_scale(value):
    scale = 1.0
    for i in range(0, 3):
        scale = scale * 1024.0
        if value // scale < 1024:
            return scale


def change_opacity(color, opactiy):
    """A method to assist in changing the opactiy of a color inorder to draw the
    fills.
    """
    color = list(color)
    if len(color) == 4:
        color[3] = opactiy
    else:
        color.append(opactiy)
    return tuple(color)


class Graph(object):
    def __init__(self):
        self.width = 100
        self.height = 100
        self.length = 150
        self.stat_info = {}
        self.line_size = 2
        self.dash_length = [10]
        self.mean_selected = True
        self.legend_selected = True
        self.max_selected = True
        self.black = (0, 0, 0)
        self.interval = 2  # 2 secs
        self.text_bg = (255, 255, 255, 128)  # prototyping
        self.set_left_axis()

    def set_left_axis(self, **kargs):
        self.left_axis = kargs

    def add_stat(self, stat, label='', axis='left', line=True, fill=True, color=None):
        self.stat_info[stat] = {
            'axis': axis,
            'label': label,
            'line': line,
            'fill': fill,
            'color': color,
        }

    def set_stats(self, stats):
        self.last_update = stats['_last_update']
        del stats['_last_update']
        self.length = stats['_length']
        del stats['_length']
        self.interval = stats['_update_interval']
        del stats['_update_interval']
        self.stats = stats
        return

    # def set_config(self, config):
    #      self.length = config["length"]
    #      self.interval = config["update_interval"]

    def set_interval(self, interval):
        self.interval = interval

    def draw_to_context(self, context, width, height):
        self.ctx = context
        self.width, self.height = width, height
        self.draw_rect(white, 0, 0, self.width, self.height)
        self.draw_graph()
        return self.ctx

    def draw(self, width, height):
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        ctx = cairo.Context(surface)
        self.draw_to_context(ctx, width, height)
        return surface

    def draw_x_axis(self, bounds):
        (left, top, right, bottom) = bounds
        duration = self.length * self.interval
        start = self.last_update - duration
        ratio = (right - left) / duration

        if duration < 1800 * 10:
            # try rounding to nearest 1min, 5mins, 10mins, 30mins
            for step in [60, 300, 600, 1800]:
                if duration // step < 10:
                    x_step = step
                    break
        else:
            # If there wasnt anything useful find a nice fitting hourly divisor
            x_step = ((duration // 5) // 3600) * 3600

        # this doesnt allow for dst and timezones...
        seconds_to_step = math.ceil(start / x_step) * x_step - start

        for i in range(0, duration // x_step + 1):
            text = time.strftime(
                '%H:%M', time.localtime(start + seconds_to_step + i * x_step)
            )
            # + 0.5 to allign x to nearest pixel
            x = int(ratio * (seconds_to_step + i * x_step) + left) + 0.5
            self.draw_x_text(text, x, bottom)
            self.draw_dotted_line(gray, x, top - 0.5, x, bottom + 0.5)

        self.draw_line(gray, left, bottom + 0.5, right, bottom + 0.5)

    def draw_graph(self):
        font_extents = self.ctx.font_extents()
        x_axis_space = font_extents[2] + 2 + self.line_size / 2
        plot_height = self.height - x_axis_space
        # lets say we need 2n-1*font height pixels to plot the y ticks
        tick_limit = plot_height / font_extents[3]

        max_value = 0
        for stat in self.stat_info:
            if self.stat_info[stat]['axis'] == 'left':
                try:
                    l_max = max(self.stats[stat])
                except ValueError:
                    l_max = 0
                if l_max > max_value:
                    max_value = l_max
        if max_value < self.left_axis['min']:
            max_value = self.left_axis['min']

        y_ticks = self.intervalise(max_value, tick_limit)
        max_value = y_ticks[-1]
        # find the width of the y_ticks
        y_tick_text = [self.left_axis['formatter'](tick) for tick in y_ticks]

        def space_required(text):
            te = self.ctx.text_extents(text)
            return math.ceil(te[4] - te[0])

        y_tick_width = max((space_required(text) for text in y_tick_text))

        top = font_extents[2] / 2
        # bounds(left, top, right, bottom)
        bounds = (y_tick_width + 4, top + 2, self.width, self.height - x_axis_space)

        self.draw_x_axis(bounds)
        self.draw_left_axis(bounds, y_ticks, y_tick_text)

    def intervalise(self, x, limit=None):
        """Given a value x create an array of tick points to got with the graph
        The number of ticks returned can be constrained by limit, minimum of 3
        """
        # Limit is the number of ticks which is 1 + the number of steps as we
        # count the 0 tick in limit
        if limit is not None:
            if limit < 3:
                limit = 2
            else:
                limit = limit - 1
        scale = 1
        if 'formatter_scale' in self.left_axis:
            scale = self.left_axis['formatter_scale'](x)
            x = x / scale

        # Find the largest power of 10 less than x
        comm_log = math.log10(x)
        intbit = math.floor(comm_log)

        interval = math.pow(10, intbit)
        steps = int(math.ceil(x / interval))

        if steps <= 1 and (limit is None or limit >= 10 * steps):
            interval = interval * 0.1
            steps = steps * 10
        elif steps <= 2 and (limit is None or limit >= 5 * steps):
            interval = interval * 0.2
            steps = steps * 5
        elif steps <= 5 and (limit is None or limit >= 2 * steps):
            interval = interval * 0.5
            steps = steps * 2

        if limit is not None and steps > limit:
            multi = steps / limit
            if multi > 2:
                interval = interval * 5
            else:
                interval = interval * 2

        intervals = [
            i * interval * scale for i in range(1 + int(math.ceil(x / interval)))
        ]
        return intervals

    def draw_left_axis(self, bounds, y_ticks, y_tick_text):
        (left, top, right, bottom) = bounds
        stats = {}
        for stat in self.stat_info:
            if self.stat_info[stat]['axis'] == 'left':
                stats[stat] = self.stat_info[stat]
                stats[stat]['values'] = self.stats[stat]
                stats[stat]['fill_color'] = change_opacity(stats[stat]['color'], 0.5)
                stats[stat]['color'] = change_opacity(stats[stat]['color'], 0.8)

        height = bottom - top
        max_value = y_ticks[-1]
        ratio = height / max_value

        for i, y_val in enumerate(y_ticks):
            y = int(bottom - y_val * ratio) - 0.5
            if i != 0:
                self.draw_dotted_line(gray, left, y, right, y)
            self.draw_y_text(y_tick_text[i], left, y)
        self.draw_line(gray, left, top, left, bottom)

        for stat, info in stats.items():
            if len(info['values']) > 0:
                self.draw_value_poly(info['values'], info['color'], max_value, bounds)
                self.draw_value_poly(
                    info['values'], info['fill_color'], max_value, bounds, info['fill']
                )

    def draw_legend(self):
        pass

    def trace_path(self, values, max_value, bounds):
        (left, top, right, bottom) = bounds
        ratio = (bottom - top) / max_value
        line_width = self.line_size

        self.ctx.set_line_width(line_width)
        self.ctx.move_to(right, bottom)

        self.ctx.line_to(right, int(bottom - values[0] * ratio))

        x = right
        step = (right - left) / (self.length - 1)
        for i, value in enumerate(values):
            if i == self.length - 1:
                x = left

            self.ctx.line_to(x, int(bottom - value * ratio))
            x -= step

        self.ctx.line_to(int(right - (len(values) - 1) * step), bottom)
        self.ctx.close_path()

    def draw_value_poly(self, values, color, max_value, bounds, fill=False):
        self.trace_path(values, max_value, bounds)
        self.ctx.set_source_rgba(*color)

        if fill:
            self.ctx.fill()
        else:
            self.ctx.stroke()

    def draw_x_text(self, text, x, y):
        """Draws text below and horizontally centered about x,y"""
        fe = self.ctx.font_extents()
        te = self.ctx.text_extents(text)
        height = fe[2]
        x_bearing = te[0]
        width = te[2]
        self.ctx.move_to(int(x - width / 2 + x_bearing), int(y + height))
        self.ctx.set_source_rgba(*self.black)
        self.ctx.show_text(text)

    def draw_y_text(self, text, x, y):
        """Draws text left of and vertically centered about x,y"""
        fe = self.ctx.font_extents()
        te = self.ctx.text_extents(text)
        descent = fe[1]
        ascent = fe[0]
        x_bearing = te[0]
        width = te[4]
        self.ctx.move_to(
            int(x - width - x_bearing - 2), int(y + (ascent - descent) / 2)
        )
        self.ctx.set_source_rgba(*self.black)
        self.ctx.show_text(text)

    def draw_rect(self, color, x, y, height, width):
        self.ctx.set_source_rgba(*color)
        self.ctx.rectangle(x, y, height, width)
        self.ctx.fill()

    def draw_line(self, color, x1, y1, x2, y2):
        self.ctx.set_source_rgba(*color)
        self.ctx.set_line_width(1)
        self.ctx.move_to(x1, y1)
        self.ctx.line_to(x2, y2)
        self.ctx.stroke()

    def draw_dotted_line(self, color, x1, y1, x2, y2):
        self.ctx.set_source_rgba(*color)
        self.ctx.set_line_width(1)
        dash, offset = self.ctx.get_dash()
        self.ctx.set_dash(self.dash_length, 0)
        self.ctx.move_to(x1, y1)
        self.ctx.line_to(x2, y2)
        self.ctx.stroke()
        self.ctx.set_dash(dash, offset)
