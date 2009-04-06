#!/usr/bin/env python
#
# resume.py
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
from deluge.ui.console.main import BaseCommand, match_torrents
from deluge.ui.console import mapping
from deluge.ui.client import aclient as client
from deluge.ui.console.colors import templates, default_style as style

class Command(BaseCommand):
    """Resume a torrent"""
    usage = "Usage: resume [ all | <torrent-id> [<torrent-id> ...] ]"
    def handle(self, *args, **options):
        if len(args) == 0:
            print self.usage
            return
        if len(args) == 1 and args[0] == 'all':
            args = tuple() # empty tuple means everything
        try:
            args = mapping.to_ids(args)
            torrents = match_torrents(args)
            client.resume_torrent(torrents)
        except Exception, msg:
            print templates.ERROR(str(msg))
        else:
            print templates.SUCCESS('torrent%s successfully resumed' % ('s' if len(args) > 1 else ''))

    def complete(self, text, *args):
        torrents = match_torrents()
        names = mapping.get_names(torrents)
        return [ x[1] for x in names if x[1].startswith(text) ]

