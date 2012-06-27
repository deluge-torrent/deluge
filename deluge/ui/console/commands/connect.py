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
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#
#
from deluge.ui.console.main import BaseCommand
import deluge.ui.console.colors as colors
from deluge.ui.client import client
import deluge.component as component

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
                    self.console.write("{!success!}Connected to %s:%s" % (host, port))
                return component.start()

            def on_connect_fail(result):
                try:
                    msg = result.value.exception_msg
                except:
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
