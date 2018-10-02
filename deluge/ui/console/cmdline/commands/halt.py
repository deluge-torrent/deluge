# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import deluge.component as component
from deluge.ui.client import client

from . import BaseCommand


class Command(BaseCommand):
    """Shutdown the deluge server."""

    def handle(self, options):
        self.console = component.get('ConsoleUI')

        def on_shutdown(result):
            self.console.write('{!success!}Daemon was shutdown')

        def on_shutdown_fail(reason):
            self.console.write('{!error!}Unable to shutdown daemon: %s' % reason)

        return (
            client.daemon.shutdown()
            .addCallback(on_shutdown)
            .addErrback(on_shutdown_fail)
        )
