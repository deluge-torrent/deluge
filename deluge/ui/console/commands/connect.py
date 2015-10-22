# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import deluge.component as component
from deluge.ui.client import client
from deluge.ui.console.main import BaseCommand


class Command(BaseCommand):
    """Connect to a new deluge server."""

    usage = "Usage: connect <host[:port]> <username> <password>"

    def handle(self, host="127.0.0.1:58846", username="", password="", **options):
        self.console = component.get("ConsoleUI")
        try:
            host, port = host.split(":")
        except ValueError:
            port = 58846
        else:
            port = int(port)

        def do_connect():
            d = client.connect(host, port, username, password)

            def on_connect(result):
                if self.console.interactive:
                    self.console.write("{!success!}Connected to %s:%s!" % (host, port))
                return component.start()

            def on_connect_fail(result):
                try:
                    msg = result.value.exception_msg
                except AttributeError:
                    msg = result.value.args[0]
                self.console.write("{!error!}Failed to connect to %s:%s with reason: %s" % (host, port, msg))
                return result

            d.addCallback(on_connect)
            d.addErrback(on_connect_fail)
            return d

        if client.connected():
            def on_disconnect(result):
                self.console.statusbars.update_statusbars()
                return do_connect()
            return client.disconnect().addCallback(on_disconnect)
        else:
            return do_connect()
