# -*- coding: utf-8 -*-
#
# listview.py
#
# Copyright (C) 2011 Pedro Algarvio <pedro@algarvio.me>
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
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
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

import gtk
import cairo
import pango
import pangocairo
import logging
from deluge.configmanager import ConfigManager

log = logging.getLogger(__name__)


COLOR_STATES = {
    0: "missing",
    1: "waiting",
    2: "downloading",
    3: "completed"
}

class PiecesBar(gtk.DrawingArea):
    # Draw in response to an expose-event
    __gsignals__ = {"expose-event": "override"}

    def __init__(self):
        gtk.DrawingArea.__init__(self)
        # Get progress bar styles, in order to keep font consistency
        pb = gtk.ProgressBar()
        pb_style = pb.get_style()
        self.text_font = pb_style.font_desc
        self.text_font.set_weight(pango.WEIGHT_BOLD)
        # Done with the ProgressBar styles, don't keep refs of it
        del pb, pb_style

        self.set_size_request(-1, 25)
        self.gtkui_config = ConfigManager("gtkui.conf")
        self.width = 0
        self.height = 0
        self.pieces = ()
        self.num_pieces = None
        self.text = ""
        self.fraction = 0.0
        self.torrent_state = None
        self.connect('size-allocate', self.do_size_allocate_event)
        self.set_colormap(self.get_screen().get_rgba_colormap())
        self.show()

    def do_size_allocate_event(self, widget, size):
        self.width = size.width
        self.height = size.height

    # Handle the expose-event by drawing
    def do_expose_event(self, event):
        self.draw_pieces(event)

    def draw_pieces(self, event):
        # Create the cairo context
        cr = self.window.cairo_create()

        # Restrict Cairo to the exposed area; avoid extra work
        cr.rectangle(event.area.x, event.area.y,
                     event.area.width, event.area.height)
        cr.clip()
        self.__roundcorners_clipping(cr, event)

        if not self.pieces and self.num_pieces is not None:
            # Complete Torrent
            piece_width = self.width*1.0/self.num_pieces
            start = 0
            for _ in range(self.num_pieces):
                # Like this to keep same aspect ratio
                color = self.gtkui_config["pieces_color_%s" % COLOR_STATES[3]]
                cr.set_source_rgb(
                    color[0]/65535.0,
                    color[1]/65535.0,
                    color[2]/65535.0,
                )
                cr.rectangle(start, 0, piece_width, self.height)
                cr.fill()
                start += piece_width
            self.__write_text(cr, event)
            return

        if not self.pieces:
            self.__write_text(cr, event)
            return

        start_pos = 0
        num_pieces = self.num_pieces and self.num_pieces or len(self.pieces)
        piece_width = self.width*1.0/num_pieces

        for state in self.pieces:
            color = self.gtkui_config["pieces_color_%s" % COLOR_STATES[state]]
            cr.set_source_rgb(
                color[0]/65535.0,
                color[1]/65535.0,
                color[2]/65535.0,
            )
            cr.rectangle(start_pos, 0, piece_width, self.height)
            cr.fill()
            start_pos += piece_width
        self.__write_text(cr, event)

    def __roundcorners_clipping(self, cr, event):
        from math import pi
        x = 0
        y = 0
        width = event.area.width
        height = event.area.height
        aspect = 1.0
        corner_radius = height/10.0
        radius = corner_radius/aspect
        degrees = pi/180.0

        cr.new_sub_path()
        cr.arc(x + width - radius, y + radius, radius, -90 * degrees, 0 * degrees)
        cr.arc(x + width - radius, y + height - radius, radius, 0 * degrees, 90 * degrees)
        cr.arc(x + radius, y + height - radius, radius, 90 * degrees, 180 * degrees)
        cr.arc(x + radius, y + radius, radius, 180 * degrees, 270 * degrees)
        cr.close_path()
        cr.clip()

    def __draw_progress_overlay(self, cr):
        cr.set_source_rgba(0.1, 0.1, 0.1, 0.3) # Transparent
        cr.rectangle(0.0, 0.0, self.width*self.fraction, self.height)
        cr.fill()

    def __write_text(self, cr, event):
        if not self.torrent_state:
            # Nothing useful to draw, return now!
            return
        self.__draw_progress_overlay(cr)

        pg = pangocairo.CairoContext(cr)
        pl = pg.create_layout()
        pl.set_font_description(self.text_font)
        pl.set_width(-1)    # No text wrapping

        text = ""
        if self.text:
            text += self.text
        else:
            if self.torrent_state:
                text += self.torrent_state + " "
            if self.fraction == 1.0:
                format = "%d%%"
            else:
                format = "%.2f%%"
            text += format % (self.fraction*100)
        log.debug("PiecesBar text %r", text)
        pl.set_text(text)
        plsize = pl.get_size()
        text_width = plsize[0]/pango.SCALE
        text_height = plsize[1]/pango.SCALE
        area_width_without_text = event.area.width - text_width
        area_height_without_text = event.area.height - text_height
        cr.move_to(area_width_without_text/2, area_height_without_text/2)
        cr.set_source_rgb(1.0, 1.0, 1.0)
        pg.update_layout(pl)
        pg.show_layout(pl)


    def set_fraction(self, fraction):
        self.fraction = fraction
        self.update()

    def set_pieces(self, pieces, num_pieces):
        if pieces != self.pieces:
            self.pieces = pieces
            self.num_pieces = num_pieces
            self.update()

    def update_from_status(self, status):
        update = False

        fraction = status["progress"]/100
        if fraction != self.fraction:
            self.fraction = fraction
            update = True

        torrent_state = status["state"]
        if torrent_state != self.torrent_state:
            self.torrent_state = torrent_state
            update = True

        if torrent_state == "Checking":
            self.update()
            # Skip the pieces assignment
            return

        if status['pieces'] != self.pieces:
            self.pieces = status['pieces']
            self.num_pieces = status['num_pieces']
            update = True

        if update:
            self.update()

    def clear(self):
        self.pieces = []
        self.num_pieces = None
        self.fraction = 0.0
        self.update()

    def update(self):
        self.queue_draw()

    def get_text(self):
        return self.text

    def set_text(self, text):
        self.text = text
        self.update()
