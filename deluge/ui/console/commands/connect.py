#
# connect.py
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
from deluge.ui.console.main import BaseCommand
import deluge.ui.console.colors as colors
from deluge.ui.client import client
import deluge.component as component

class Command(BaseCommand):
    """Connect to a new deluge server."""
    def handle(self, host="", port="58846", username="", password="", **options):
        self.console = component.get("ConsoleUI")

        port = int(port)
        d = client.connect(host, port, username, password)
        def on_connect(result):
            self.console.write("{!success!}Connected to %s:%s!" % (host, port))

        def on_connect_fail(result):
            self.console.write("{!error!}Failed to connect to %s:%s!" % (host, port))

        d.addCallback(on_connect)
        d.addErrback(on_connect_fail)
