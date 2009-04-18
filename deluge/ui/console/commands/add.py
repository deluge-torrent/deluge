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
# 	Boston, MA    02110-1301, USA.
#
from deluge.ui.console.main import BaseCommand, match_torrents
from deluge.ui.console import mapping
import deluge.ui.console.colors as colors
from deluge.ui.client import client
from optparse import make_option
import os
import base64

class Command(BaseCommand):
    """Add a torrent"""
    option_list = BaseCommand.option_list + (
            make_option('-p', '--path', dest='path',
                        help='save path for torrent'),
    )

    usage = "Usage: add [-p <save-location>] <torrent-file> [<torrent-file> ...]"

    def handle(self, *args, **options):
        t_options = {}
        if options["path"]:
            t_options["download_location"] = options["path"]

        for arg in args:
            self.write("{{info}}Attempting to add torrent: %s" % arg)
            filename = os.path.split(arg)[-1]
            filedump = base64.encodestring(open(arg).read())

            def on_success(result):
                self.write("{{success}}Torrent added!")
            def on_fail(result):
                self.write("{{error}}Torrent was not added! %s" % result)

            client.core.add_torrent_file(filename, filedump, t_options).addCallback(on_success).addErrback(on_fail)
