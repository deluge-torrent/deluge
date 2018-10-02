# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging

import deluge.component as component

from . import BaseCommand

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """Enable interactive mode"""

    interactive_only = True

    def handle(self, options):
        console = component.get('ConsoleUI')
        at = console.set_mode('TorrentList')
        at.go_top = True
        at.resume()
