#
# Copyright (C) 2011 Pedro Algarvio <pedro@algarvio.me>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from math import pi

import gi  # isort:skip (Version check required before import).

gi.require_version('PangoCairo', '1.0')
gi.require_foreign('cairo')
gi.require_version('cairo', '1.0')

# isort:imports-thirdparty
import cairo  # Backward compat cairo <= 1.15
from gi.repository import PangoCairo
from gi.repository.Gtk import DrawingArea, ProgressBar, StateFlags
from gi.repository.Pango import SCALE, Weight

# isort:imports-firstparty
from deluge.configmanager import ConfigManager

COLOR_STATES = ['missing', 'waiting', 'downloading', 'completed']


class PiecesBar(DrawingArea):
    # Draw in response to an draw
    __gsignals__ = {'draw': 'override'}

    def __init__(self):
        super().__init__()
        # Get progress bar styles, in order to keep font consistency
        pb = ProgressBar()
        pb_style = pb.get_style_context()
        # Get a copy of Pango.FontDescription since original needs freed.
        self.text_font = pb_style.get_property('font', StateFlags.NORMAL).copy()
        self.text_font.set_weight(Weight.BOLD)
        # Done with the ProgressBar styles, don't keep refs of it
        del pb, pb_style

        self.set_size_request(-1, 25)
        self.gtkui_config = ConfigManager('gtk3ui.conf')

        self.width = self.prev_width = 0
        self.height = self.prev_height = 0
        self.pieces = self.prev_pieces = ()
        self.num_pieces = None
        self.text = self.prev_text = ''
        self.fraction = self.prev_fraction = 0
        self.progress_overlay = self.text_overlay = self.pieces_overlay = None

        self.connect('size-allocate', self.do_size_allocate_event)
        self.show()

    def do_size_allocate_event(self, widget, size):
        self.prev_width = self.width
        self.width = size.width
        self.prev_height = self.height
        self.height = size.height

    # Handle the draw by drawing
    def do_draw(self, ctx):
        ctx.set_line_width(max(ctx.device_to_user_distance(0.5, 0.5)))

        # Restrict Cairo to the exposed area; avoid extra work
        self.roundcorners_clipping(ctx)

        self.draw_pieces(ctx)
        self.draw_progress_overlay(ctx)
        self.write_text(ctx)
        self.roundcorners_border(ctx)

        # Drawn once, update width, height
        if self.resized():
            self.prev_width = self.width
            self.prev_height = self.height

    def roundcorners_clipping(self, ctx):
        self.create_roundcorners_subpath(ctx, 0, 0, self.width, self.height)
        ctx.clip()

    def roundcorners_border(self, ctx):
        self.create_roundcorners_subpath(ctx, 0.5, 0.5, self.width - 1, self.height - 1)
        ctx.set_source_rgba(0, 0, 0, 0.9)
        ctx.stroke()

    @staticmethod
    def create_roundcorners_subpath(ctx, x, y, width, height):
        aspect = 1.0
        corner_radius = height / 10
        radius = corner_radius / aspect
        degrees = pi / 180
        ctx.new_sub_path()
        ctx.arc(x + width - radius, y + radius, radius, -90 * degrees, 0 * degrees)
        ctx.arc(
            x + width - radius, y + height - radius, radius, 0 * degrees, 90 * degrees
        )
        ctx.arc(x + radius, y + height - radius, radius, 90 * degrees, 180 * degrees)
        ctx.arc(x + radius, y + radius, radius, 180 * degrees, 270 * degrees)
        ctx.close_path()

    def draw_pieces(self, ctx):
        if not self.num_pieces:
            return

        if (
            self.resized()
            or self.pieces != self.prev_pieces
            or self.pieces_overlay is None
        ):
            # Need to recreate the cache drawing
            self.pieces_overlay = cairo.ImageSurface(
                cairo.FORMAT_ARGB32, self.width, self.height
            )
            pieces_ctx = cairo.Context(self.pieces_overlay)

            if self.pieces:
                pieces = self.pieces
            elif self.num_pieces:
                # Completed torrents do not send any pieces so create list using 'completed' state.
                pieces = [COLOR_STATES.index('completed')] * self.num_pieces
            start_pos = 0
            piece_width = self.width / len(pieces)
            pieces_colors = [
                [
                    color / 65535
                    for color in self.gtkui_config['pieces_color_%s' % state]
                ]
                for state in COLOR_STATES
            ]
            for state in pieces:
                pieces_ctx.set_source_rgb(*pieces_colors[state])
                pieces_ctx.rectangle(start_pos, 0, piece_width, self.height)
                pieces_ctx.fill()
                start_pos += piece_width

        ctx.set_source_surface(self.pieces_overlay)
        ctx.paint()

    def draw_progress_overlay(self, ctx):
        if not self.text:
            return

        if (
            self.resized()
            or self.fraction != self.prev_fraction
            or self.progress_overlay is None
        ):
            # Need to recreate the cache drawing
            self.progress_overlay = cairo.ImageSurface(
                cairo.FORMAT_ARGB32, self.width, self.height
            )
            progress_ctx = cairo.Context(self.progress_overlay)
            progress_ctx.set_source_rgba(0.1, 0.1, 0.1, 0.3)  # Transparent
            progress_ctx.rectangle(0, 0, self.width * self.fraction, self.height)
            progress_ctx.fill()
        ctx.set_source_surface(self.progress_overlay)
        ctx.paint()

    def write_text(self, ctx):
        if not self.text:
            return

        if self.resized() or self.text != self.prev_text or self.text_overlay is None:
            # Need to recreate the cache drawing
            self.text_overlay = cairo.ImageSurface(
                cairo.FORMAT_ARGB32, self.width, self.height
            )
            text_ctx = cairo.Context(self.text_overlay)
            pl = PangoCairo.create_layout(text_ctx)
            pl.set_font_description(self.text_font)
            pl.set_width(-1)  # No text wrapping
            pl.set_text(self.text, -1)
            plsize = pl.get_size()
            text_width = plsize[0] // SCALE
            text_height = plsize[1] // SCALE
            area_width_without_text = self.width - text_width
            area_height_without_text = self.height - text_height
            text_ctx.move_to(
                area_width_without_text // 2, area_height_without_text // 2
            )
            text_ctx.set_source_rgb(1, 1, 1)
            PangoCairo.update_layout(text_ctx, pl)
            PangoCairo.show_layout(text_ctx, pl)
        ctx.set_source_surface(self.text_overlay)
        ctx.paint()

    def resized(self):
        return self.prev_width != self.width or self.prev_height != self.height

    def set_fraction(self, fraction):
        self.prev_fraction = self.fraction
        self.fraction = fraction

    def get_fraction(self):
        return self.fraction

    def get_text(self):
        return self.text

    def set_text(self, text):
        self.prev_text = self.text
        self.text = text

    def set_pieces(self, pieces, num_pieces):
        self.prev_pieces = self.pieces
        self.pieces = pieces
        self.num_pieces = num_pieces

    def get_pieces(self):
        return self.pieces

    def clear(self):
        self.pieces = self.prev_pieces = ()
        self.num_pieces = None
        self.text = self.prev_text = ''
        self.fraction = self.prev_fraction = 0
        self.progress_overlay = self.text_overlay = self.pieces_overlay = None
        self.update()

    def update(self):
        self.queue_draw()
