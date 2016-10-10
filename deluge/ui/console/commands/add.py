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

from __future__ import with_statement

from twisted.internet import defer

from deluge.ui.console.main import BaseCommand
import deluge.ui.console.colors as colors
from deluge.ui.client import client
import deluge.component as component
import deluge.common

from optparse import make_option
import os
import base64

class Command(BaseCommand):
    """Add a torrent"""
    option_list = BaseCommand.option_list + (
            make_option('-p', '--path', dest='path',
                        help='save path for torrent'),
    )

    usage = "Usage: add [-p <save-location>] <torrent-file/infohash/url> [<torrent-file/infohash/url> ...]"

    def handle(self, *args, **options):
        self.console = component.get("ConsoleUI")

        t_options = {}
        if options["path"]:
            t_options["download_location"] = os.path.abspath(os.path.expanduser(options["path"]))

        def on_success(result):
            self.console.write("{!success!}Torrent added!")
        def on_fail(result):
            self.console.write("{!error!}Torrent was not added! %s" % result)

        # Keep a list of deferreds to make a DeferredList
        deferreds = []
        for arg in args:
            if not arg.strip():
                continue
            if deluge.common.is_url(arg):
                    deferreds.append(client.core.add_torrent_url(arg, t_options).addCallback(on_success).addErrback(on_fail))
            elif deluge.common.is_magnet(arg):
                    deferreds.append(client.core.add_torrent_magnet(arg, t_options).addCallback(on_success).addErrback(on_fail))
            else:
                # Just a file
                path = os.path.abspath(arg.replace('file://', '', 1))
                if not os.path.exists(path):
                    self.console.write("{!error!}%s doesn't exist!" % arg)
                    continue
                if not os.path.isfile(path):
                    self.console.write("{!error!}This is a directory!")
                    continue
                self.console.write("{!info!}Attempting to add torrent: %s" % arg)
                filename = os.path.split(arg)[-1]
                with open(arg, "rb") as _file:
                    filedump = base64.encodestring(_file.read())
                deferreds.append(client.core.add_torrent_file(filename, filedump, t_options).addCallback(on_success).addErrback(on_fail))

        return defer.DeferredList(deferreds)

    def complete(self, line):
        line = os.path.abspath(os.path.expanduser(line))
        ret = []
        if os.path.exists(line):
            # This is a correct path, check to see if it's a directory
            if os.path.isdir(line):
                # Directory, so we need to show contents of directory
                #ret.extend(os.listdir(line))
                for f in os.listdir(line):
                    # Skip hidden
                    if f.startswith("."):
                        continue
                    f = os.path.join(line, f)
                    if os.path.isdir(f):
                        f += "/"
                    ret.append(f)
            else:
                # This is a file, but we could be looking for another file that
                # shares a common prefix.
                for f in os.listdir(os.path.dirname(line)):
                    if f.startswith(os.path.split(line)[1]):
                        ret.append(os.path.join( os.path.dirname(line), f))
        else:
            # This path does not exist, so lets do a listdir on it's parent
            # and find any matches.
            ret = []
            if os.path.isdir(os.path.dirname(line)):
                for f in os.listdir(os.path.dirname(line)):
                    if f.startswith(os.path.split(line)[1]):
                        p = os.path.join(os.path.dirname(line), f)

                        if os.path.isdir(p):
                            p += "/"
                        ret.append(p)

        return ret
