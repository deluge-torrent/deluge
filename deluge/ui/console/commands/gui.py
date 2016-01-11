# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging

import deluge.component as component
from deluge.ui.console.main import BaseCommand
from deluge.ui.console.modes.alltorrents import AllTorrents

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """Enable interactive mode"""
    interactive_only = True

    def handle(self, options):
        console = component.get("ConsoleUI")
        try:
            at = component.get("AllTorrents")
        except KeyError:
            at = AllTorrents(console.stdscr, console.encoding)

        console.set_mode(at)
        at._go_top = True
        at.resume()
