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

from urllib import urlopen
from deluge.log import LOG as log
from deluge.common import get_default_config_dir, get_pixmap
import os

#some servers don't have their favicon at the expected location
RENAMES = {"legaltorrents.com":"beta.legaltorrents.com"}
VALID_TYPES = ["octet-stream","x-icon"]

class TrackerIcons(object):
    def __init__(self):
        #set image cache dir
        self.image_dir = get_default_config_dir("trackers")
        if not os.path.exists(self.image_dir):
            os.mkdir(self.image_dir)

        #self.images : {tracker_host:filename}
        self.images = {"DHT":get_pixmap("dht16.png" )}

        #load image-names in cache-dir
        for icon in os.listdir(self.image_dir):
            if icon.endswith(".ico"):
                self.add_icon(icon[:-4], os.path.join(self.image_dir, icon))


    def _fetch_icon(self, tracker_host):
        """
        gets new icon from the internet.
        used by get().
        calls add_icon()
        returns True or False
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
            self.add_icon(tracker_host, None)
            return False

        filename = os.path.join(get_default_config_dir("trackers"),"%s.ico" % tracker_host)

        f = open(filename,"wb")
        f.write(icon_data)
        f.close()
        self.add_icon(tracker_host, filename)
        return True

    def add_icon(self, tracker_host, filename):
        self.images[tracker_host] = filename

    def  get(self, tracker_host):
        """
        use this method to get the filename of an icon.
        """
        if not tracker_host in self.images:
            self._fetch_icon(tracker_host)
        else:
            log.debug("cached tracker icon:%s" % tracker_host)
        return self.images[tracker_host]





