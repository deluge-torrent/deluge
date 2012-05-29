#
# add.py
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
from twisted.internet import defer

from deluge.ui.console.main import BaseCommand
import deluge.ui.console.colors as colors
from deluge.ui.client import client
import deluge.component as component
import deluge.common
from deluge.ui.common import TorrentInfo

from optparse import make_option
import os
import base64
from urllib import url2pathname
from urlparse import urlparse

class Command(BaseCommand):
    """Add a torrent"""
    option_list = BaseCommand.option_list + (
            make_option('-p', '--path', dest='path',
                        help='save path for torrent'),
    )

    usage = "Usage: add [-p <save-location>] <torrent-file> [<torrent-file> ...]\n"\
            "             <torrent-file> arguments can be file paths, URLs or magnet uris"

    def handle(self, *args, **options):
        self.console = component.get("ConsoleUI")

        t_options = {}
        if options["path"]:
            t_options["download_location"] = os.path.expanduser(options["path"])

        def on_success(result):
            if not result:
                self.console.write("{!error!}Torrent was not added: Already in session")
            else:
                self.console.write("{!success!}Torrent added!")
        def on_fail(result):
            self.console.write("{!error!}Torrent was not added: %s" % result)

        # Keep a list of deferreds to make a DeferredList
        deferreds = []
        for arg in args:
            if not arg.strip():
                continue
            if deluge.common.is_url(arg):
                self.console.write("{!info!}Attempting to add torrent from url: %s" % arg)
                deferreds.append(client.core.add_torrent_url(arg, t_options).addCallback(on_success).addErrback(on_fail))
            elif deluge.common.is_magnet(arg):
                self.console.write("{!info!}Attempting to add torrent from magnet uri: %s" % arg)
                deferreds.append(client.core.add_torrent_magnet(arg, t_options).addCallback(on_success).addErrback(on_fail))
            else:
                # Just a file
                if urlparse(arg).scheme == "file":
                    arg = url2pathname(urlparse(arg).path)
                path = os.path.abspath(os.path.expanduser(arg))
                if not os.path.exists(path):
                    self.console.write("{!error!}%s doesn't exist!" % path)
                    continue
                if not os.path.isfile(path):
                    self.console.write("{!error!}This is a directory!")
                    continue
                self.console.write("{!info!}Attempting to add torrent: %s" % path)
                filename = os.path.split(path)[-1]
                filedump = base64.encodestring(open(path, "rb").read())
                deferreds.append(client.core.add_torrent_file(filename, filedump, t_options).addCallback(on_success).addErrback(on_fail))

        return defer.DeferredList(deferreds)

    def complete(self, line):
        return component.get("ConsoleUI").tab_complete_path(line, ext=".torrent", sort="date")