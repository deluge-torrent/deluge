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

import pygtk
pygtk.require('2.0')
import gtk
import gtk.gdk
import cairo
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
        self.set_size_request(-1, 25)
        self.gtkui_config = ConfigManager("gtkui.conf")
        self.width = 0
        self.height = 0
        self.pieces = ()
        self.num_pieces = None
        self.connect('size-allocate', self.do_size_allocate_event)
        self.set_colormap(self.get_screen().get_rgba_colormap())
        self.show()

    def do_size_allocate_event(self, widget, size):
        self.width = size.width
        self.height = size.height

    # Handle the expose-event by drawing
    def do_expose_event(self, event=None):
        # Create the cairo context
        cr = self.window.cairo_create()

        # Restrict Cairo to the exposed area; avoid extra work
        cr.rectangle(event.area.x, event.area.y,
                     event.area.width, event.area.height)
        cr.clip()

#            # Sets the operator to clear which deletes everything below where
#            # an object is drawn
#            cr.set_operator(cairo.OPERATOR_CLEAR)
#            # Makes the mask fill the entire area
#            cr.rectangle(0.0, 0.0, event.area.width, event.area.height)
#            # Deletes everything in the window (since the compositing operator
#            # is clear and mask fills the entire window
#            cr.fill()
#            # Set the compositing operator back to the default
#            cr.set_operator(cairo.OPERATOR_OVER)


        cr.set_line_width(max(cr.device_to_user_distance(0.5, 0.5)))
#        bgColor = self.window.get_style().copy().bg[gtk.STATE_NORMAL]
#        cr.set_source_rgba(0.53, 0.53, 0.53, 1.0) # Transparent
#        cr.set_source_rgba(0.8, 0.8, 0.8, 1.0) # Transparent
#        cr.set_source_rgb(0.3, 0.3, 0.3) # Transparent
        cr.set_source_rgb(0.1, 0.1, 0.1) # Transparent
#        cr.set_source_rgb(bgColor.red/65535.0, bgColor.green/65535.0, bgColor.blue/65535.0)
#        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.rectangle(0.0, 0.0, event.area.width, event.area.height)
        cr.stroke()
#        # Set the compositing operator back to the default
#        cr.set_operator(cairo.OPERATOR_OVER)


        if not self.pieces and self.num_pieces is not None:
            # Complete Torrent
            piece_height = self.height - 2
            piece_width = self.width*1.0/self.num_pieces
            start = 1
            for _ in range(self.num_pieces):
                # Like this to keep same aspect ratio
                color = self.gtkui_config["pieces_color_%s" % COLOR_STATES[3]]
                cr.set_source_rgb(
                    color[0]/65535.0,
                    color[1]/65535.0,
                    color[2]/65535.0,
                )
#                cr.set_source_rgba(*list(self.colors[3])+[0.5])
                cr.rectangle(start, 1, piece_width, piece_height)
                cr.fill()
                start += piece_width
            return

        if not self.pieces:
            return

        # Create the cairo context
        start_pos = 1
        num_pieces = self.num_pieces and self.num_pieces or len(self.pieces)
        piece_width = self.width*1.0/num_pieces
        piece_height = self.height - 2

        for state in self.pieces:
#            cr.set_source_rgb(*self.colors[state])
#            cr.set_source_rgb(*self.colors[state])

            color = self.gtkui_config["pieces_color_%s" % COLOR_STATES[state]]
            cr.set_source_rgb(
                color[0]/65535.0,
                color[1]/65535.0,
                color[2]/65535.0,
            )
#            cr.set_source_rgba(*list(self.colors[state])+[0.5])
            cr.rectangle(start_pos, 1, piece_width, piece_height)
            cr.fill()
            start_pos += piece_width

    def set_pieces(self, pieces, num_pieces):
        if pieces != self.pieces:
            self.pieces = pieces
            self.num_pieces = num_pieces
            self.update()

    def clear(self):
        self.pieces = []
        self.num_pieces = None
        self.update()

    def update(self):
        self.queue_draw()

    def get_text(self):
        return ""

    def set_text(self, text):
        pass

#    def on_pieces_colors_updated(self, key, colors):
#        log.debug("Pieces bar got config change for key: %s  values: %s",
#                  key, colors)
#        if key != "pieces_colors":
#            return
#        # Make sure there's no state color missong
#        self.colors[0] = [c/65535.0 for c in colors[0]]
#        self.colors[1] = [c/65535.0 for c in colors[1]]
#        self.colors[2] = [c/65535.0 for c in colors[2]]
#        self.colors[3] = [c/65535.0 for c in colors[3]]
#        self.update()
