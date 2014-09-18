# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from twisted.internet import error, reactor

from deluge.ui.client import client
from deluge.ui.console.main import BaseCommand


class Command(BaseCommand):
    """Exit from the client."""
    aliases = ["exit"]
    interactive_only = True

    def handle(self, *args, **options):
        if client.connected():
            def on_disconnect(result):
                reactor.stop()
            return client.disconnect().addCallback(on_disconnect)
        else:
            try:
                reactor.stop()
            except error.ReactorNotRunning:
                pass
