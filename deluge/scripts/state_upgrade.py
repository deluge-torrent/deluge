#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Martijn Voncken 2008 <mvoncken@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, write to:
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
#


import sys, pickle , shutil , os
from deluge.ui.client import sclient

options = {
    "new_torrents_dir" :"~/torrents06",
    "state05":"~/.config/deluge/persistent.state",
    "all_paused":True
}

#start : http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/286203
def makeFakeClass(module, name):
    class FakeThing(object):
        pass
    FakeThing.__name__ = name
    FakeThing.__module__ = '(fake)' + module
    return FakeThing

class PickleUpgrader(pickle.Unpickler):
    def find_class(self, module, cname):
        # Pickle tries to load a couple things like copy_reg and
        # __builtin__.object even though a pickle file doesn't
        # explicitly reference them (afaict): allow them to be loaded
        # normally.
        if module in ('copy_reg', '__builtin__'):
            thing = pickle.Unpickler.find_class(self, module, cname)
            return thing
        return makeFakeClass(module, cname)
# end: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/286203

def load_05(state_05_file, new_torrent_dir,all_paused):
    state5 = PickleUpgrader(open(state_05_file)).load()
    for torrent in state5.torrents:
        #print [x for x in dir(torrent) if not x.startswith("_")]
        print("file:%s, save_dir:%s, compact:%s, paused:%s " % (torrent.filename,torrent.save_dir,torrent.compact,torrent.user_paused))

        new_file = os.path.join(new_torrent_dir,os.path.basename(torrent.filename))
        print("copy" , torrent.filename , new_file)
        shutil.copyfile(torrent.filename , new_file)

        sclient.add_torrent_file([torrent.filename],[{
            "add_paused" : (all_paused or torrent.user_paused),
            "compact_allocation":torrent.compact,
            "download_location":torrent.save_dir
        }])

if __name__ == "__main__":
    sclient.set_core_uri()
    new_torrents_dir = os.path.expanduser(options["new_torrents_dir"])
    state_05_file = os.path.expanduser(options['state05']);
    load_05(state_05_file, new_torrents_dir, options["all_paused"])














