#!/usr/bin/env python
#
# add.py
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
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
from deluge.ui.console.colors import templates
from deluge.ui.client import aclient as client
from optparse import make_option
import os

class Command(BaseCommand):
    """Add a torrent"""
    option_list = BaseCommand.option_list + (
            make_option('-p', '--path', dest='path',
                        help='save path for torrent'),
    )

    usage = "Usage: add [-p <save-location>] <torrent-file> [<torrent-file> ...]"

    def handle(self, *args, **options):
        if options['path'] is None:
            def _got_config(configs):
                global save_path
                save_path = configs['download_location']
            client.get_config(_got_config)
            client.force_call()
            options['path'] = save_path
        else:
            client.set_config({'download_location': options['path']})
        if not options['path']:
            print templates.ERROR("There's no save-path specified. You must specify a path to save the downloaded files.")
            return
        try:
            client.add_torrent_file(args)
        except Exception, msg:
            print templates.ERROR("Error: %s" % str(msg))
