#
# add_util.py
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
#
# Modified function from commands/add.py:
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
from deluge.ui.client import client
import deluge.component as component
from deluge.ui.common import TorrentInfo
import deluge.common

import os,base64,glob



def add_torrent(t_file, options, success_cb, fail_cb, ress):
    t_options = {}
    if options["path"]:
        t_options["download_location"] = os.path.expanduser(options["path"])
    t_options["add_paused"] = options["add_paused"]

    is_url = (not (options["path_type"]==1)) and (deluge.common.is_url(t_file) or options["path_type"]==2)
    is_mag = not(is_url) and (not (options["path_type"]==1)) and deluge.common.is_magnet(t_file)

    if is_url or is_mag:
        files = [t_file]
    else:
        files = glob.glob(t_file)
    num_files = len(files)
    ress["total"] = num_files

    if num_files <= 0:
        fail_cb("Doesn't exist",t_file,ress)

    for f in files:
        if is_url:
            client.core.add_torrent_url(f, t_options).addCallback(success_cb,f,ress).addErrback(fail_cb,f,ress)
        elif is_mag:
            client.core.add_torrent_magnet(f, t_options).addCallback(success_cb,f,ress).addErrback(fail_cb,f,ress)
        else:
            if not os.path.exists(f):
                fail_cb("Doesn't exist",f,ress)
                continue
            if not os.path.isfile(f):
                fail_cb("Is a directory",f,ress)
                continue

            try:
                TorrentInfo(f)
            except Exception as e:
                fail_cb(e.message,f,ress)
                continue

            filename = os.path.split(f)[-1]
            filedump = base64.encodestring(open(f).read())

            client.core.add_torrent_file(filename, filedump, t_options).addCallback(success_cb,f,ress).addErrback(fail_cb,f,ress)

