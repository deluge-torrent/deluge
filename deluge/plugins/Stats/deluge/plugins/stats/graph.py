#
# graph.py
#
# Copyright (C) 2008 Damien Churchill <damoxc@gmail.com>
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) Marcos Pinto 2007 <markybob@gmail.com>
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
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception

"""
port of old plugin by markybob.
"""
import time
import cairo
import logging
from deluge.ui.client import client

black = (0, 0, 0)
gray = (0.75, 0.75, 0.75)
white = (1.0, 1.0, 1.0)
darkred = (0.65, 0, 0)
red = (1.0, 0, 0)
green = (0, 1.0, 0)
blue = (0, 0, 1.0)
orange = (1.0, 0.74, 0)

log = logging.getLogger(__name__)

def default_formatter(value):
    return str(value)

def change_opacity(color, opactiy):
    """A method to assist in changing the opacity of a color in order to draw the
    fills.
    """
    color = list(color)
    if len(color) == 4:
        color[3] = opactiy
    else:
        color.append(opactiy)
    return tuple(color)

class Graph:
    def __init__(self):
        self.width = 100
        self.height = 100
        self.length = 150
        self.stat_info = {}
        self.line_size = 2
        self.mean_selected = True
        self.legend_selected = True
        self.max_selected = True
        self.black = (0, 0 , 0,)
        self.interval = 2 # 2 secs
        self.text_bg =  (255, 255 , 255, 128) # prototyping
        self.set_left_axis()

    def set_left_axis(self, **kargs):
        self.left_axis = kargs

    def add_stat(self, stat, label='', axis='left', line=True, fill=True, color=None):
        self.stat_info[stat] = {
            'axis': axis,
            'label': label,
            'line': line,
            'fill': fill,
            'color': color
            }

    def set_stats(self, stats):
        self.last_update = stats["_last_update"]
        log.debug("Last update: %s" % self.last_update)
        del stats["_last_update"]
        self.stats = stats

    def set_config(self, config):
        self.length = config["length"]
        self.interval = config["update_interval"]

    def draw_to_context(self, context, width, height):
        self.ctx = context
        self.width, self.height = width, height
        try:
            self.draw_rect(white, 0, 0, self.width, self.height)
            self.draw_x_axis()
            self.draw_left_axis()

            if self.legend_selected:
                self.draw_legend()
        except cairo.Error, e:
            log.exception(e)
        return self.ctx

    def draw(self, width, height):
        self.width = width
        self.height = height

        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.width, self.height)
        self.ctx = cairo.Context(self.surface)
        self.draw_rect(white, 0, 0, self.width, self.height)
        self.draw_x_axis()
        self.draw_left_axis()

        if self.legend_selected:
            self.draw_legend()
        return self.surface

    def draw_x_axis(self):
        duration = float(self.length * self.interval)
        start = self.last_update - duration
        ratio = (self.width - 40) / duration
        seconds_to_minute = 60 - time.localtime(start)[5]

        for i in xrange(0, 5):
            text = time.strftime('%H:%M', time.localtime(start + seconds_to_minute + (60*i)))
            x = int(ratio * (seconds_to_minute + (60*i)))
            self.draw_text(text, x + 46, self.height - 20)
            x = x + 59.5
            self.draw_dotted_line(gray, x, 20, x, self.height - 20)

        y = self.height - 22.5
        self.draw_dotted_line(gray, 60, y, int(self.width), y)

    def draw_left_axis(self):
        stats = {}
        max_values = []
        for stat in self.stat_info:
            if self.stat_info[stat]['axis'] == 'left':
                stats[stat] = self.stat_info[stat]
                stats[stat]['values'] = self.stats[stat]
                stats[stat]['fill_color'] = change_opacity(stats[stat]['color'], 0.5)
                stats[stat]['color'] = change_opacity(stats[stat]['color'], 0.8)
                stats[stat]['max_value'] = max(self.stats[stat])
                max_values.append(stats[stat]['max_value'])
        if len(max_values) > 1:
            max_value = max(*max_values)
        else:
            max_value = max_values[0]

        if max_value < self.left_axis['min']:
            max_value = self.left_axis['min']

        height = self.height - self.line_size - 22
        #max_value = float(round(max_value, len(str(max_value)) * -1))
        max_value = float(max_value)
        ratio = height / max_value

        for i in xrange(1, 6):
            y = int(ratio * ((max_value / 5) * i)) - 0.5
            if i < 5:
                self.draw_dotted_line(gray, 60, y, self.width, y)
            text = self.left_axis['formatter']((max_value / 5) * (5 - i))
            self.draw_text(text, 0, y - 6)
        self.draw_dotted_line(gray, 60.5, 20, 60.5, self.height - 20)

        for stat, info in stats.iteritems():
            self.draw_value_poly(info['values'], info['color'], max_value)
            self.draw_value_poly(info['values'], info['fill_color'], max_value, info['fill'])

    def draw_legend(self):
        pass

    def trace_path(self, values, max_value):
        height = self.height - 24
        width = self.width
        line_width = self.line_size

        self.ctx.set_line_width(line_width)
        self.ctx.move_to(width, height)

        self.ctx.line_to(width,
                         int(height - ((height - 28) * values[0] / max_value)))

        x = width
        step = (width - 60) / float(self.length)
        for i, value in enumerate(values):
            if i == self.length - 1:
                x = 62
            self.ctx.line_to(x,
                int(height - 1 - ((height - 28) * value / max_value))
            )
            x -= step

        self.ctx.line_to(
            int(width + 62 - (((len(values) - 1) * width) / (self.length - 1))),
            height)
        self.ctx.close_path()

    def draw_value_poly(self, values, color, max_value, fill=False):
        self.trace_path(values, max_value)
        self.ctx.set_source_rgba(*color)

        if fill:
            self.ctx.fill()
        else:
            self.ctx.stroke()

    def draw_text(self, text, x, y):
        self.ctx.set_font_size(9)
        self.ctx.move_to(x, y + 9)
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
        self.ctx.move_to(x1, y1)
        self.ctx.line_to(x2, y2)
        #self.ctx.stroke_preserve()
        #self.ctx.set_source_rgba(*white)
        #self.ctx.set_dash((1, 1), 4)
        self.ctx.stroke()
        #self.ctx.set_dash((1, 1), 0)

if __name__ == "__main__":
    import test
