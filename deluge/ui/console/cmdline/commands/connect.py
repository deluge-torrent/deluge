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

import logging

import deluge.component as component
from deluge.ui.client import client

from . import BaseCommand

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """Connect to a new deluge server"""

    usage = _('Usage: connect <host[:port]> [<username>] [<password>]')

    def add_arguments(self, parser):
        parser.add_argument(
            'host', help=_('Daemon host and port'), metavar='<host[:port]>'
        )
        parser.add_argument(
            'username', help=_('Username'), metavar='<username>', nargs='?', default=''
        )
        parser.add_argument(
            'password', help=_('Password'), metavar='<password>', nargs='?', default=''
        )

    def add_parser(self, subparsers):
        parser = subparsers.add_parser(
            self.name, help=self.__doc__, description=self.__doc__, prog='connect'
        )
        self.add_arguments(parser)

    def handle(self, options):
        self.console = component.get('ConsoleUI')

        host = options.host
        try:
            host, port = host.split(':')
            port = int(port)
        except ValueError:
            port = 58846

        def do_connect():
            d = client.connect(host, port, options.username, options.password)

            def on_connect(result):
                if self.console.interactive:
                    self.console.write('{!success!}Connected to %s:%s!' % (host, port))
                return component.start()

            def on_connect_fail(result):
                try:
                    msg = result.value.exception_msg
                except AttributeError:
                    msg = result.value.message
                self.console.write(
                    '{!error!}Failed to connect to %s:%s with reason: %s'
                    % (host, port, msg)
                )
                return result

            d.addCallbacks(on_connect, on_connect_fail)
            return d

        if client.connected():

            def on_disconnect(result):
                if self.console.statusbars:
                    self.console.statusbars.update_statusbars()
                return do_connect()

            return client.disconnect().addCallback(on_disconnect)
        else:
            return do_connect()
