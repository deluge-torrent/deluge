# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import print_function, unicode_literals

import logging

from twisted.internet.error import CannotListenError

from deluge.common import run_profiled
from deluge.ui.ui import UI

log = logging.getLogger(__name__)


class Web(UI):

    cmd_description = """Web-based user interface (http://localhost:8112)"""

    def __init__(self, *args, **kwargs):
        super(Web, self).__init__(
            'web', *args, description='Starts the Deluge Web interface', **kwargs
        )
        self.__server = None

        group = self.parser.add_argument_group(_('Web Server Options'))
        group.add_argument(
            '-i',
            '--interface',
            metavar='<ip_address>',
            action='store',
            help=_('IP address for web server to listen on'),
        )
        group.add_argument(
            '-p',
            '--port',
            metavar='<port>',
            type=int,
            action='store',
            help=_('Port for web server to listen on'),
        )
        group.add_argument(
            '-b',
            '--base',
            metavar='<path>',
            action='store',
            help=_('Set the base path that the ui is running on'),
        )
        group.add_argument(
            '--ssl', action='store_true', help=_('Force the web server to use SSL')
        )
        group.add_argument(
            '--no-ssl',
            action='store_true',
            help=_('Force the web server to disable SSL'),
        )
        self.parser.add_process_arg_group()

    @property
    def server(self):
        return self.__server

    def start(self):
        super(Web, self).start()

        from deluge.ui.web import server

        self.__server = server.DelugeWeb(options=self.options)

        def run():
            try:
                self.server.install_signal_handlers()
                self.server.start()
            except CannotListenError as ex:
                log.error(
                    '%s \nCheck that deluge-web or webui plugin is not already running.',
                    ex,
                )
            except Exception as ex:
                log.exception(ex)
                raise

        run_profiled(
            run, output_file=self.options.profile, do_profile=self.options.profile
        )
