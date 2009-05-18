#
# debug.py
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA    02110-1301, USA.
#

from twisted.internet import defer

from deluge.ui.console.main import BaseCommand
from deluge.ui.client import client
import deluge.ui.console.colors as colors
import deluge.log
import deluge.component as component

class Command(BaseCommand):
    """Enable and disable debugging"""
    usage = 'debug [on|off]'
    def handle(self, state='', **options):
        if state == 'on':
            deluge.log.setLoggerLevel("debug")
        elif state == 'off':
            deluge.log.setLoggerLevel("error")
        else:
            component.get("ConsoleUI").write("{!error!}%s" % usage)

        return defer.succeed(True)

    def complete(self, text):
        return [x for x in ['on', 'off'] if x.startswith(text)]
