# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Pedro Algarvio <pedro@algarvio.me>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging
from math import pi

import cairo

from deluge.configmanager import ConfigManager
from gi.repository import Gdk, Gtk, Pango, PangoCairo

log = logging.getLogger(__name__)


COLOR_STATES = {
    0: "missing",
    1: "waiting",
    2: "downloading",
    3: "completed"
}


class PiecesBar(Gtk.DrawingArea):
    # Draw in response to an expose-event
    __gsignals__ = {"draw": "override"}

    def __init__(self):
        Gtk.DrawingArea.__init__(self)
        # Get progress bar styles, in order to keep font consistency
        pb = Gtk.ProgressBar()
        pb_style = pb.get_style()
        self.__text_font = pb_style.font_desc
        self.__text_font.set_weight(Pango.Weight.BOLD)
        # Done with the ProgressBar styles, don't keep refs of it
        del pb, pb_style

        self.set_size_request(-1, 25)
        self.gtkui_config = ConfigManager("gtkui.conf")
        self.__width = self.__old_width = 0
        self.__height = self.__old_height = 0
        self.__pieces = self.__old_pieces = ()
        self.__num_pieces = self.__old_num_pieces = None
        self.__text = self.__old_text = ""
        self.__fraction = self.__old_fraction = 0.0
        self.__state = self.__old_state = None
        self.__progress_overlay = self.__text_overlay = self.__pieces_overlay = None
        self.__cr = None

        self.connect('size-allocate', self.do_size_allocate_event)
        self.set_colormap(Gdk.colormap_get_system())
        self.show()

    def do_size_allocate_event(self, widget, size):
        self.__old_width = self.__width
        self.__width = size.width
        self.__old_height = self.__height
        self.__height = size.height

    # Handle the expose-event by drawing
    def do_expose_event(self, event):
        # Create cairo context
        self.__cr = self.window.cairo_create()
        self.__cr.set_line_width(max(self.__cr.device_to_user_distance(0.5, 0.5)))

        # Restrict Cairo to the exposed area; avoid extra work
        self.__roundcorners_clipping()

        if not self.__pieces and self.__num_pieces is not None:
            # Special case. Completed torrents do not send any pieces in their
            # status.
            self.__draw_pieces_completed()
        elif self.__pieces:
            self.__draw_pieces()

        self.__draw_progress_overlay()
        self.__write_text()
        self.__roundcorners_border()

        # Drawn once, update width, eight
        if self.__resized():
            self.__old_width = self.__width
            self.__old_height = self.__height

    def __roundcorners_clipping(self):
        self.__create_roundcorners_subpath(
            self.__cr, 0, 0, self.__width, self.__height
        )
        self.__cr.clip()

    def __roundcorners_border(self):
        self.__create_roundcorners_subpath(
            self.__cr, 0.5, 0.5, self.__width - 1, self.__height - 1
        )
        self.__cr.set_source_rgba(0.0, 0.0, 0.0, 0.9)
        self.__cr.stroke()

    def __create_roundcorners_subpath(self, ctx, x, y, width, height):
        aspect = 1.0
        corner_radius = height / 10.0
        radius = corner_radius / aspect
        degrees = pi / 180.0
        ctx.new_sub_path()
        ctx.arc(x + width - radius, y + radius, radius, -90 * degrees, 0 * degrees)
        ctx.arc(x + width - radius, y + height - radius, radius, 0 * degrees, 90 * degrees)
        ctx.arc(x + radius, y + height - radius, radius, 90 * degrees, 180 * degrees)
        ctx.arc(x + radius, y + radius, radius, 180 * degrees, 270 * degrees)
        ctx.close_path()
        return ctx

    def __draw_pieces(self):
        if (self.__resized() or self.__pieces != self.__old_pieces or
                self.__pieces_overlay is None):
            # Need to recreate the cache drawing
            self.__pieces_overlay = cairo.ImageSurface(
                cairo.FORMAT_ARGB32, self.__width, self.__height
            )
            ctx = cairo.Context(self.__pieces_overlay)
            start_pos = 0
            num_pieces = self.__num_pieces and self.__num_pieces or len(self.__pieces)
            piece_width = self.__width * 1.0 / num_pieces

            for state in self.__pieces:
                color = self.gtkui_config["pieces_color_%s" % COLOR_STATES[state]]
                ctx.set_source_rgb(
                    color[0] / 65535.0,
                    color[1] / 65535.0,
                    color[2] / 65535.0,
                )
                ctx.rectangle(start_pos, 0, piece_width, self.__height)
                ctx.fill()
                start_pos += piece_width

        self.__cr.set_source_surface(self.__pieces_overlay)
        self.__cr.paint()

    def __draw_pieces_completed(self):
        if (self.__resized() or self.__pieces != self.__old_pieces or
                self.__pieces_overlay is None):
            # Need to recreate the cache drawing
            self.__pieces_overlay = cairo.ImageSurface(
                cairo.FORMAT_ARGB32, self.__width, self.__height
            )
            ctx = cairo.Context(self.__pieces_overlay)
            piece_width = self.__width * 1.0 / self.__num_pieces
            start = 0
            for _ in range(self.__num_pieces):
                # Like this to keep same aspect ratio
                color = self.gtkui_config["pieces_color_%s" % COLOR_STATES[3]]
                ctx.set_source_rgb(
                    color[0] / 65535.0,
                    color[1] / 65535.0,
                    color[2] / 65535.0,
                )
                ctx.rectangle(start, 0, piece_width, self.__height)
                ctx.fill()
                start += piece_width

        self.__cr.set_source_surface(self.__pieces_overlay)
        self.__cr.paint()

    def __draw_progress_overlay(self):
        if not self.__state:
            # Nothing useful to draw, return now!
            return
        if (self.__resized() or self.__fraction != self.__old_fraction) or self.__progress_overlay is None:
            # Need to recreate the cache drawing
            self.__progress_overlay = cairo.ImageSurface(
                cairo.FORMAT_ARGB32, self.__width, self.__height
            )
            ctx = cairo.Context(self.__progress_overlay)
            ctx.set_source_rgba(0.1, 0.1, 0.1, 0.3)  # Transparent
            ctx.rectangle(0.0, 0.0, self.__width * self.__fraction, self.__height)
            ctx.fill()
        self.__cr.set_source_surface(self.__progress_overlay)
        self.__cr.paint()

    def __write_text(self):
        if not self.__state:
            # Nothing useful to draw, return now!
            return
        if (self.__resized() or self.__text != self.__old_text or
                self.__fraction != self.__old_fraction or
                self.__state != self.__old_state or
                self.__text_overlay is None):
            # Need to recreate the cache drawing
            self.__text_overlay = cairo.ImageSurface(
                cairo.FORMAT_ARGB32, self.__width, self.__height
            )
            ctx = cairo.Context(self.__text_overlay)
            pg = PangoCairo.CairoContext(ctx)
            pl = pg.create_layout()
            pl.set_font_description(self.__text_font)
            pl.set_width(-1)    # No text wrapping

            text = ""
            if self.__text:
                text += self.__text
            else:
                if self.__state:
                    text += _(self.__state) + " "
                if self.__fraction == 1.0:
                    format = "%d%%"
                else:
                    format = "%.2f%%"
                text += format % (self.__fraction * 100)
            log.trace("PiecesBar text %r", text)
            pl.set_text(text)
            plsize = pl.get_size()
            text_width = plsize[0] / Pango.SCALE
            text_height = plsize[1] / Pango.SCALE
            area_width_without_text = self.__width - text_width
            area_height_without_text = self.__height - text_height
            ctx.move_to(area_width_without_text / 2, area_height_without_text / 2)
            ctx.set_source_rgb(1.0, 1.0, 1.0)
            pg.update_layout(pl)
            pg.show_layout(pl)
        self.__cr.set_source_surface(self.__text_overlay)
        self.__cr.paint()

    def __resized(self):
        return (self.__old_width != self.__width or
                self.__old_height != self.__height)

    def set_fraction(self, fraction):
        self.__old_fraction = self.__fraction
        self.__fraction = fraction

    def get_fraction(self):
        return self.__fraction

    def get_text(self):
        return self.__text

    def set_text(self, text):
        self.__old_text = self.__text
        self.__text = text

    def set_pieces(self, pieces, num_pieces):
        self.__old_pieces = self.__pieces
        self.__pieces = pieces
        self.__num_pieces = num_pieces

    def get_pieces(self):
        return self.__pieces

    def set_state(self, state):
        self.__old_state = self.__state
        self.__state = state

    def get_state(self):
        return self.__state

    def update_from_status(self, status):
        log.trace("Updating PiecesBar from status")
        self.set_fraction(status["progress"] / 100)
        torrent_state = status["state"]
        self.set_state(torrent_state)
        if torrent_state == "Checking":
            self.update()
            # Skip the pieces assignment
            return

        self.set_pieces(status['pieces'], status['num_pieces'])
        self.update()

    def clear(self):
        self.__pieces = self.__old_pieces = ()
        self.__num_pieces = self.__old_num_pieces = None
        self.__text = self.__old_text = ""
        self.__fraction = self.__old_fraction = 0.0
        self.__state = self.__old_state = None
        self.__progress_overlay = self.__text_overlay = self.__pieces_overlay = None
        self.__cr = None
        self.update()

    def update(self):
        self.queue_draw()
