#
# tracker_icons.py
#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
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
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.


import threading
import gobject
from urllib import urlopen
from deluge.log import LOG as log
from deluge.common import get_default_config_dir, get_pixmap
import os

#some servers don't have their favicon at the expected location
RENAMES = {
    "legaltorrents.com":"beta.legaltorrents.com",
    "aelitis.com":"www.vuze.com"
    }

VALID_TYPES = ["octet-stream","x-icon"]

class TrackerIcons(object):
    def __init__(self):
        #set image cache dir
        self.image_dir = get_default_config_dir("icons")
        if not os.path.exists(self.image_dir):
            os.mkdir(self.image_dir)

        #self.images : {tracker_host:filename}
        self.images = {"DHT":get_pixmap("dht16.png" )}

        #load image-names in cache-dir
        for icon in os.listdir(self.image_dir):
            if icon.endswith(".ico"):
                self.images[icon[:-4]] = os.path.join(self.image_dir, icon)

    def _fetch_icon_thread(self, tracker_host, callback):
        """
        gets new icon from the internet.
        used by get().
        calls callback on sucess
        assumes dicts,urllib and logging are threadsafe.
        """
        try:
            host_name = RENAMES.get(tracker_host, tracker_host)
            icon = urlopen("http://%s/favicon.ico" % host_name)
            icon_data = icon.read()

            #validate icon:
            if icon.info().getsubtype() not in VALID_TYPES:
                raise Exception("Unexpected type: %s" % icon.info().getsubtype())
            if not icon_data:
                raise Exception("No data")
        except Exception, e:
            log.debug("%s %s %s" % (tracker_host, e, e.message))
            return False

        filename = os.path.join(get_default_config_dir("icons"),"%s.ico" % tracker_host)

        f = open(filename,"wb")
        f.write(icon_data)
        f.close()
        self.images[tracker_host] = filename
        if callback:
            gobject.idle_add(callback, filename)

    def get_async(self, tracker_host, callback):
        if tracker_host in self.images:
            callback(self.images[tracker_host])
        else:
            self.images[tracker_host] = None
            threading.Thread(target=self. _fetch_icon_thread,
                args=(tracker_host, callback)).start()

    def  get(self, tracker_host):
        """
        returns None if the icon is not fetched(yet) or not fond.
        """
        if tracker_host in self.images:
            return self.images[tracker_host]
        else:
            self.get_async(tracker_host, None)
            return None


