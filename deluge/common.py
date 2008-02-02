#
# common.py
#
# Copyright (C) 2007 Andrew Resch ('andar') <andrewresch@gmail.com>
# 
# Deluge is free software.
# 
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 2 of the License, or (at your option)
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

"""Common functions for various parts of Deluge to use."""

import os

import pkg_resources
import xdg, xdg.BaseDirectory


LT_TORRENT_STATE = {
    "Queued": 0,
    "Checking": 1,
    "Connecting": 2,
    "Downloading Metadata": 3,
    "Downloading": 4,
    "Finished": 5,
    "Seeding": 6,
    "Allocating": 7,
    "Paused": 8
}

TORRENT_STATE = {
    "Allocating": 0,
    "Checking": 1,
    "Downloading": 2,
    "Seeding": 3,
    "Paused": 4,
    "Error": 5
}
def get_version():
    """Returns the program version from the egg metadata"""
    return pkg_resources.require("Deluge")[0].version.split("r")[0]

def get_revision():
    revision = ""
    try:
        f = open(pkg_resources.resource_filename("deluge", os.path.join("data", "revision")))
        revision = f.read()
        f.close()
    except IOError, e:
        pass
        
    return revision
    
def get_config_dir(filename=None):
    """ Returns the config path if no filename is specified
    Returns the config directory + filename as a path if filename is specified
    """
    if filename != None:
        return os.path.join(xdg.BaseDirectory.save_config_path("deluge"), 
                                                                    filename)
    else:
        return xdg.BaseDirectory.save_config_path("deluge")

def get_default_download_dir():
    """Returns the default download directory"""
    if windows_check():
        return os.path.expanduser("~")
    else:
        return os.environ.get("HOME")

def get_default_torrent_dir():
    """Returns the default torrent directory"""
    return os.path.join(get_config_dir(), "torrentfiles")
    
def get_default_plugin_dir():
    """Returns the default plugin directory"""
    return os.path.join(get_config_dir(), "plugins")

def windows_check():
    """Checks if the current platform is Windows.  Returns True if it is Windows
        and False if not."""
    import platform
    if platform.system() in ('Windows', 'Microsoft'):
        return True
    else:
        return False

def get_pixmap(fname):
    """Returns a pixmap file included with deluge"""
    return pkg_resources.resource_filename("deluge", os.path.join("data", \
                                           "pixmaps", fname))

def get_logo(size):
    """Returns a deluge logo pixbuf based on the size parameter."""
    import gtk
    if windows_check(): 
        return gtk.gdk.pixbuf_new_from_file_at_size(get_pixmap("deluge.png"), \
            size, size)
    else:
        return gtk.gdk.pixbuf_new_from_file_at_size(get_pixmap("deluge.svg"), \
            size, size)

def open_file(path):
    """Opens a file or folder."""
    os.popen("xdg-open %s" % path)

def open_url_in_browser(url):
    """Opens link in the desktop's default browser"""
    def start_browser():
        import webbrowser
        webbrowser.open(url)
        return False
        
    import gobject
    gobject.idle_add(start_browser)
        
## Formatting text functions

def fsize(fsize_b):
    """Returns formatted string describing filesize
       fsize_b should be in bytes
       Returned value will be in either KB, MB, or GB
    """    
    fsize_kb = fsize_b / 1024.0
    if fsize_kb < 1000:
        return "%.1f KiB" % fsize_kb
    fsize_mb = fsize_kb / 1024.0
    if fsize_mb < 1000:
        return "%.1f MiB" % fsize_mb
    fsize_gb = fsize_mb / 1024.0
    return "%.1f GiB" % fsize_gb

def fpcnt(dec):
    """Returns a formatted string representing a percentage"""
    return '%.2f%%' % (dec * 100)

def fspeed(bps):
    """Returns a formatted string representing transfer speed"""
    return '%s/s' % (fsize(bps))

def fpeer(num_peers, total_peers):
    """Returns a formatted string num_peers (total_peers)"""
    if total_peers > -1:
        return "%d (%d)" % (num_peers, total_peers)
    else:
        return "%d" % num_peers
    
def ftime(seconds):
    """Returns a formatted time string"""
    if seconds == 0:
        return "Infinity"
    if seconds < 60:
        return '%ds' % (seconds)
    minutes = seconds / 60
    seconds = seconds % 60
    if minutes < 60:
        return '%dm %ds' % (minutes, seconds)
    hours = minutes / 60
    minutes = minutes % 60
    if hours < 24:
        return '%dh %dm' % (hours, minutes)
    days = hours / 24
    hours = hours % 24
    if days < 7:
        return '%dd %dh' % (days, hours)
    weeks = days / 7
    days = days % 7
    if weeks < 10:
        return '%dw %dd' % (weeks, days)
    return 'unknown'

def is_url(url):
    """A simple regex test to check if the URL is valid."""
    import re
    return bool(re.search('^(https?|ftp)://', url))

def fetch_url(url):
    """Downloads a torrent file from a given 
    URL and checks the file's validity."""
    import urllib
    from deluge.log import LOG as log
    try:
        filename, headers = urllib.urlretrieve(url)
    except IOError:
        log.debug("Network error while trying to fetch torrent from %s", url)
    else:
        if filename.endswith(".torrent") or headers["content-type"] ==\
        "application/x-bittorrent":
            return filename
        else:
            log.debug("URL doesn't appear to be a valid torrent file: %s", url)
            return None
            
def pythonize(var):
    """Translates DBUS types back to basic Python types."""
    if isinstance(var, list):
        return [pythonize(value) for value in var]
    if isinstance(var, tuple):
        return tuple([pythonize(value) for value in var])
    if isinstance(var, dict):
        return dict(
        [(pythonize(key), pythonize(value)) for key, value in var.iteritems()]
        )

    for klass in [unicode, str, bool, int, float, long]:
        if isinstance(var, klass):
            return klass(var)
    return var
