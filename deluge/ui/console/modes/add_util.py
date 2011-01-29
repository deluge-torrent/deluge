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
from twisted.internet import defer

from deluge.ui.client import client
import deluge.component as component

from optparse import make_option
import os
import base64

def add_torrent(t_file, options, success_cb, fail_cb):
    t_options = {}
    if options["path"]:
        t_options["download_location"] = os.path.expanduser(options["path"])
    t_options["add_paused"] = options["add_paused"]

    # Keep a list of deferreds to make a DeferredList
    if not os.path.exists(t_file):
        fail_cb("{!error!}%s doesn't exist!" % t_file)
        return
    if not os.path.isfile(t_file):
        fail_cb("{!error!}%s is a directory!" % t_file)
        return
        

    filename = os.path.split(t_file)[-1]
    filedump = base64.encodestring(open(t_file).read())

    def on_success(result):
        success_cb("{!success!}Torrent added!")
    def on_fail(result):
        fail_cb("{!error!}Torrent was not added! %s" % result)

    client.core.add_torrent_file(filename, filedump, t_options).addCallback(on_success).addErrback(on_fail)
        
