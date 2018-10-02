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

from twisted.internet import defer

import deluge.component as component
import deluge.log

from . import BaseCommand


class Command(BaseCommand):
    """Enable and disable debugging"""

    def add_arguments(self, parser):
        parser.add_argument(
            'state', metavar='<on|off>', choices=['on', 'off'], help=_('The new state')
        )

    def handle(self, options):
        if options.state == 'on':
            deluge.log.set_logger_level('debug')
        elif options.state == 'off':
            deluge.log.set_logger_level('error')
        else:
            component.get('ConsoleUI').write('{!error!}%s' % self.usage)

        return defer.succeed(True)

    def complete(self, text):
        return [x for x in ['on', 'off'] if x.startswith(text)]
