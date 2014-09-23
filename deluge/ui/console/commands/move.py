# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import os.path

import deluge.component as component
from deluge.ui.client import client
from deluge.ui.console.main import BaseCommand


class Command(BaseCommand):
    """Move torrents' storage location"""
    usage = "Usage: move <torrent-id> [<torrent-id> ...] <path>"

    def handle(self, *args, **options):
        self.console = component.get("ConsoleUI")

        if len(args) < 2:
            self.console.write(self.usage)
            return

        path = args[-1]

        if os.path.exists(path) and not os.path.isdir(path):
            self.console.write("{!error!}Cannot Move Download Folder: %s exists and is not a directory" % path)
            return

        ids = []
        for i in args[:-1]:
            ids.extend(self.console.match_torrent(i))

        names = []
        for i in ids:
            names.append(self.console.get_torrent_name(i))
        namestr = ", ".join(names)

        def on_move(res):
            self.console.write("Moved \"%s\" to %s" % (namestr, path))

        d = client.core.move_storage(ids, path)
        d.addCallback(on_move)
        return d

    def complete(self, line):
        line = os.path.abspath(os.path.expanduser(line))
        ret = []
        if os.path.exists(line):
            # This is a correct path, check to see if it's a directory
            if os.path.isdir(line):
                # Directory, so we need to show contents of directory
                # ret.extend(os.listdir(line))
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
                        ret.append(os.path.join(os.path.dirname(line), f))
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
