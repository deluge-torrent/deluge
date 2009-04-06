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



import threading
import gobject
from urllib import urlopen
from deluge.log import LOG as log
from deluge.common import get_pixmap
import os
import deluge.configmanager

#some servers don't have their favicon at the expected location
RENAMES = {
    "legaltorrents.com":"beta.legaltorrents.com",
    "aelitis.com":"www.vuze.com"
    }

VALID_ICO_TYPES = ["octet-stream", "x-icon", "vnd.microsoft.icon"]
VALID_PNG_TYPES = ["octet-stream", "png"]

def fetch_url(url, valid_subtypes=None):
    """
    returns: data or None
    """
    try:
        url_file = urlopen(url)
        data = url_file.read()

        #validate:
        if valid_subtypes and (url_file.info().getsubtype() not in valid_subtypes):
            raise Exception("Unexpected type for %s : %s" % (url, url_file.info().getsubtype()))
        if not data:
            raise Exception("No data")
    except Exception, e:
        log.debug("%s %s %s" % (url, e, e.message))
        return None

    return data

class TrackerIcons(object):
    def __init__(self):
        #set image cache dir
        self.image_dir = os.path.join(deluge.configmanager.get_config_dir(), "icons")
        if not os.path.exists(self.image_dir):
            os.mkdir(self.image_dir)

        #self.images : {tracker_host:filename}
        self.images = {"DHT":get_pixmap("dht16.png" )}

        #load image-names in cache-dir
        for icon in os.listdir(self.image_dir):
            if icon.endswith(".ico"):
                self.images[icon[:-4]] = os.path.join(self.image_dir, icon)
            if icon.endswith(".png"):
                self.images[icon[:-4]] = os.path.join(self.image_dir, icon)

    def _fetch_icon(self, tracker_host):
        """
        returns (ext, data)
        """
        host_name = RENAMES.get(tracker_host, tracker_host) #HACK!

        ico = fetch_url("http://%s/favicon.ico" % host_name, VALID_ICO_TYPES)
        if ico:
            return ("ico", ico)

        png = fetch_url("http://%s/favicon.png" % host_name, VALID_PNG_TYPES)
        if png:
            return ("png", png)

        # FIXME: This should be cleaned up and not copy the top code

        try:
            html = urlopen("http://%s/" % (host_name,))
        except Exception, e:
            log.debug(e)
            html = None

        if html:
            icon_path = ""
            line = html.readline()
            while line:
                if '<link rel="icon"' in line or '<link rel="shortcut icon"' in line:
                    log.debug("line: %s", line)
                    icon_path = line[line.find("href"):].split("\"")[1]
                    break
                line = html.readline()
            if icon_path:
                ico = fetch_url(("http://%s/" + icon_path) % host_name, VALID_ICO_TYPES)
                if ico:
                    return ("ico", ico)
                png = fetch_url(("http://%s/" + icon_path) % host_name, VALID_PNG_TYPES)
                if png:
                    return ("png", png)

        """
        TODO: need a test-site first...
        html = fetch_url("http://%s/" % (host_name,))
        if html:
            for line in html:
                print line
        """
        return (None, None)

    def _fetch_icon_thread(self, tracker_host, callback):
        """
        gets new icon from the internet.
        used by get().
        calls callback on sucess
        assumes dicts,urllib and logging are threadsafe.
        """

        ext, icon_data  = self._fetch_icon(tracker_host)

        if icon_data:
            filename = os.path.join(self.image_dir, "%s.%s" % (tracker_host, ext))
            f = open(filename,"wb")
            f.write(icon_data)
            f.close()
            self.images[tracker_host] = filename
        else:
            filename = None

        if callback:
            gobject.idle_add(callback, filename)

    def get_async(self, tracker_host, callback):
        if tracker_host in self.images:
            callback(self.images[tracker_host])
        elif "." in tracker_host:
            #only find icon if there's a dot in the name.
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

if __name__ == "__main__":
    import time
    def del_old():
        filename = os.path.join(deluge.configmanager.get_config_dir(),"legaltorrents.com.ico")
        if os.path.exists(filename):
            os.remove(filename)

    def test_get():
        del_old()
        trackericons  = TrackerIcons()
        print trackericons.images
        print trackericons.get("unknown2")
        print trackericons.get("ntorrents.net")
        print trackericons.get("google.com")
        print trackericons.get("legaltorrents.com")
        time.sleep(5.0)
        print trackericons.get("legaltorrents.com")

    test_get()
    #test_async()
