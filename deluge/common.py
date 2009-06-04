#
# common.py
#
# Copyright (C) 2007, 2008 Andrew Resch <andrewresch@gmail.com>
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


"""Common functions for various parts of Deluge to use."""

import os
import time
import subprocess
import platform

import pkg_resources
import xdg, xdg.BaseDirectory

LT_TORRENT_STATE = {
    "Queued": 0,
    "Checking": 1,
    "Downloading Metadata": 2,
    "Downloading": 3,
    "Finished": 4,
    "Seeding": 5,
    "Allocating": 6,
    "Checking Resume Data": 7,
    0: "Queued",
    1: "Checking",
    2: "Downloading Metadata",
    3: "Downloading",
    4: "Finished",
    5: "Seeding",
    6: "Allocating",
    7: "Checking Resume Data"
}

TORRENT_STATE = [
    "Allocating",
    "Checking",
    "Downloading",
    "Seeding",
    "Paused",
    "Error",
    "Queued"
]

FILE_PRIORITY = {
    0: "Do Not Download",
    1: "Normal Priority",
    2: "High Priority",
    5: "Highest Priority",
    "Do Not Download": 0,
    "Normal Priority": 1,
    "High Priority": 2,
    "Highest Priority": 5
}

def get_version():
    """
    Returns the program version from the egg metadata

    :returns: the version of Deluge
    :rtype: string

    """
    return pkg_resources.require("Deluge")[0].version

def get_revision():
    """
    The svn revision of the build if available

    :returns: the svn revision, or ""
    :rtype: string

    """
    revision = ""
    try:
        f = open(pkg_resources.resource_filename("deluge", os.path.join("data", "revision")))
        revision = f.read()
        f.close()
    except IOError, e:
        pass

    return revision

def get_default_config_dir(filename=None):
    """
    :param filename: if None, only the config path is returned, if provided, a path including the filename will be returned
    :returns: a file path to the config directory and optional filename
    :rtype: string

    """
    if windows_check():
        if filename:
            return os.path.join(os.environ.get("APPDATA"), "deluge", filename)
        else:
            return os.path.join(os.environ.get("APPDATA"), "deluge")
    else:
        if filename:
            return os.path.join(xdg.BaseDirectory.save_config_path("deluge"), filename)
        else:
            return xdg.BaseDirectory.save_config_path("deluge")

def get_default_download_dir():
    """
    :returns: the default download directory
    :rtype: string

    """
    if windows_check():
        return os.path.expanduser("~")
    else:
        return os.environ.get("HOME")

def windows_check():
    """
    Checks if the current platform is Windows

    :returns: True or False
    :rtype: bool

    """
    return platform.system() in ('Windows', 'Microsoft')

def vista_check():
    """
    Checks if the current platform is Windows Vista

    :returns: True or False
    :rtype: bool

    """
    return platform.release() == "Vista"

def osx_check():
    """
    Checks if the current platform is Mac OS X

    :returns: True or False
    :rtype: bool

    """
    return platform.system() == "Darwin"

def get_pixmap(fname):
    """
    Provides easy access to files in the deluge/data/pixmaps folder within the Deluge egg

    :param fname: the filename to look for
    :returns: a path to a pixmap file included with Deluge
    :rtype: string

    """
    return pkg_resources.resource_filename("deluge", os.path.join("data", \
                                           "pixmaps", fname))

def open_file(path):
    """
    Opens a file or folder using the system configured program

    :param path: the path to the file or folder to open

    """
    if windows_check():
        os.startfile("%s" % path)
    else:
        subprocess.Popen(["xdg-open", "%s" % path])

def open_url_in_browser(url):
    """
    Opens a url in the desktop's default browser

    :param url: the url to open
    """
    import threading
    import webbrowser
    class BrowserThread(threading.Thread):
        def __init__(self, url):
            threading.Thread.__init__(self)
            self.url = url
        def run(self):
            webbrowser.open(self.url)
    BrowserThread(url).start()

## Formatting text functions

def fsize(fsize_b):
    """
    Formats the bytes value into a string with KiB, MiB or GiB units

    :param fsize_b: int, the filesize in bytes
    :returns: formatted string in KiB, MiB or GiB units
    :rtype: string

    **Usage**

    >>> fsize(112245)
    '109.6 KiB'

    """
    fsize_kb = fsize_b / 1024.0
    if fsize_kb < 1024:
        return "%.1f KiB" % fsize_kb
    fsize_mb = fsize_kb / 1024.0
    if fsize_mb < 1024:
        return "%.1f MiB" % fsize_mb
    fsize_gb = fsize_mb / 1024.0
    return "%.1f GiB" % fsize_gb

def fpcnt(dec):
    """
    Formats a string to display a percentage with two decimal places

    :param dec: float, the ratio in the range [0.0, 1.0]
    :returns: a formatted string representing a percentage
    :rtype: string

    **Usage**

    >>> fpcnt(0.9311)
    '93.11%'

    """
    return '%.2f%%' % (dec * 100)

def fspeed(bps):
    """
    Formats a string to display a transfer speed utilizing :func:`fsize`

    :param bps: int, bytes per second
    :returns: a formatted string representing transfer speed
    :rtype: string

    **Usage**

    >>> fspeed(43134)
    '42.1 KiB/s'

    """
    return '%s/s' % (fsize(bps))

def fpeer(num_peers, total_peers):
    """
    Formats a string to show 'num_peers' ('total_peers')

    :param num_peers: int, the number of connected peers
    :param total_peers: int, the total number of peers
    :returns: a formatted string: num_peers (total_peers), if total_peers < 0, then it will not be shown
    :rtype: string

    **Usage**

    >>> fpeer(10, 20)
    '10 (20)'
    >>> fpeer(10, -1)
    '10'

    """
    if total_peers > -1:
        return "%d (%d)" % (num_peers, total_peers)
    else:
        return "%d" % num_peers

def ftime(seconds):
    """
    Formats a string to show time in a human readable form

    :param seconds: int, the number of seconds
    :returns: a formatted time string, will return '' if seconds == 0
    :rtype: string

    **Usage**

    >>> ftime(23011)
    '6h 23m'

    """
    if seconds == 0:
        return ""
    if seconds < 60:
        return '%ds' % (seconds)
    minutes = seconds / 60
    if minutes < 60:
        seconds = seconds % 60
        return '%dm %ds' % (minutes, seconds)
    hours = minutes / 60
    if hours < 24:
        minutes = minutes % 60
        return '%dh %dm' % (hours, minutes)
    days = hours / 24
    if days < 7:
        hours = hours % 24
        return '%dd %dh' % (days, hours)
    weeks = days / 7
    if weeks < 52:
        days = days % 7
        return '%dw %dd' % (weeks, days)
    years = weeks / 52
    weeks = weeks % 52
    return '%dy %dw' % (years, weeks)

def fdate(seconds):
    """
    Formats a date string in the locale's date representation based on the systems timezone

    :param seconds: float, time in seconds since the Epoch
    :returns: a string in the locale's date representation or "" if seconds < 0
    :rtype: string

    """
    if seconds < 0:
        return ""
    return time.strftime("%x", time.localtime(seconds))

def is_url(url):
    """
    A simple regex test to check if the URL is valid

    :param url: string, the url to test
    :returns: True or False
    :rtype: bool

    **Usage**

    >>> is_url("http://deluge-torrent.org")
    True

    """
    import re
    return bool(re.search('^(https?|ftp|udp)://', url))

def is_magnet(uri):
    """
    A check to determine if a uri is a valid bittorrent magnet uri

    :param uri: string, the uri to check
    :returns: True or False
    :rtype: bool

    **Usage**

    >>> is_magnet("magnet:?xt=urn:btih:SU5225URMTUEQLDXQWRB2EQWN6KLTYKN")
    True

    """
    if uri[:20] == "magnet:?xt=urn:btih:":
        return True
    return False

def fetch_url(url):
    """
    Downloads a torrent file from a given URL and checks the file's validity

    :param url: string, the url of the .torrent file to fetch
    :returns: the filepath to the downloaded file
    :rtype: string

    """
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

def create_magnet_uri(infohash, name=None, trackers=[]):
    """
    Creates a magnet uri

    :param infohash: string, the info-hash of the torrent
    :param name: string, the name of the torrent (optional)
    :param trackers: list of strings, the trackers to announce to (optional)

    :returns: a magnet uri string
    :rtype: string

    """
    from base64 import b32encode
    uri = "magnet:?xt=urn:btih:" + b32encode(infohash.decode("hex"))
    if name:
        uri = uri + "&dn=" + name
    if trackers:
        for t in trackers:
            uri = uri + "&tr=" + t

    return uri

def get_path_size(path):
    """
    Gets the size in bytes of 'path'

    :param path: string, the path to check for size
    :returns: the size in bytes of the path or -1 if the path does not exist
    :rtype: int

    """
    if not os.path.exists(path):
        return -1

    if os.path.isfile(path):
        return os.path.getsize(path)

    dir_size = 0
    for (p, dirs, files) in os.walk(path):
        for file in files:
            filename = os.path.join(p, file)
            dir_size += os.path.getsize(filename)
    return dir_size

def free_space(path):
    """
    Gets the free space available at 'path'

    :param path: string, the path to check
    :returns: the free space at path in bytes
    :rtype: int

    """
    if windows_check():
        import win32file
        sectors, bytes, free, total = map(long, win32file.GetDiskFreeSpace(path))
        return (free * sectors * bytes)
    else:
        disk_data = os.statvfs(path)
        block_size = disk_data.f_bsize
        return disk_data.f_bavail * block_size

def is_ip(ip):
    """
    A simple test to see if 'ip' is valid

    :param ip: string, the ip to check
    :returns: True or False
    :rtype: bool

    ** Usage **

    >>> is_ip("127.0.0.1")
    True

    """
    import socket
    #first we test ipv4
    try:
        if socket.inet_pton(socket.AF_INET, "%s" % (ip)):
            return True
    except socket.error:
        if not socket.has_ipv6:
            return False
    #now test ipv6
    try:
        if socket.inet_pton(socket.AF_INET6, "%s" % (ip)):
            return True
    except socket.error:
        return False
