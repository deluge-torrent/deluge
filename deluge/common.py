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
#   The Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor
#   Boston, MA  02110-1301, USA.
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

from __future__ import with_statement

import os
import time
import subprocess
import platform
import sys
import chardet
import pkg_resources
import gettext
import locale

try:
    import json
except ImportError:
    import simplejson as json

from deluge.error import *
from deluge.log import LOG as log

# Do a little hack here just in case the user has json-py installed since it
# has a different api
if not hasattr(json, "dumps"):
    json.dumps = json.write
    json.loads = json.read

    def dump(obj, fp, **kw):
        fp.write(json.dumps(obj))

    def load(fp, **kw):
        return json.loads(fp.read())

    json.dump = dump
    json.load = load

# Initialize gettext
try:
    if hasattr(locale, "bindtextdomain"):
        locale.bindtextdomain("deluge", pkg_resources.resource_filename("deluge", "i18n"))
    if hasattr(locale, "textdomain"):
        locale.textdomain("deluge")
    gettext.install("deluge", pkg_resources.resource_filename("deluge", "i18n"), unicode=True)
except Exception, e:
    log.error("Unable to initialize gettext/locale!")
    log.exception(e)
    import __builtin__
    __builtin__.__dict__["_"] = lambda x: x

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
    3: "High Priority",
    4: "High Priority",
    5: "High Priority",
    6: "High Priority",
    7: "Highest Priority",
    "Do Not Download": 0,
    "Normal Priority": 1,
    "High Priority": 5,
    "Highest Priority": 7
}

def get_version():
    """
    Returns the program version from the egg metadata

    :returns: the version of Deluge
    :rtype: string

    """
    return pkg_resources.require("Deluge")[0].version

def get_default_config_dir(filename=None):
    """
    :param filename: if None, only the config path is returned, if provided, a path including the filename will be returned
    :type filename: string
    :returns: a file path to the config directory and optional filename
    :rtype: string

    """
    if windows_check():
        appDataPath = os.environ.get("APPDATA")
        if not appDataPath:
            import _winreg
            hkey = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Folders")
            appDataReg = _winreg.QueryValueEx(hkey, "AppData")
            appDataPath = appDataReg[0]
            _winreg.CloseKey(hkey)
        if filename:
            return os.path.join(appDataPath, "deluge", filename)
        else:
            return os.path.join(appDataPath, "deluge")
    else:
        from xdg.BaseDirectory import save_config_path
        try:
            if filename:
                return os.path.join(save_config_path("deluge"), filename)
            else:
                return save_config_path("deluge")
        except OSError, e:
            log.error("Unable to use default config directory, exiting... (%s)", e)
            sys.exit(1)

def get_default_download_dir():
    """
    :returns: the default download directory
    :rtype: string

    """
    download_dir = ""
    if not windows_check():
        from xdg.BaseDirectory import xdg_config_home
        try:
            with open(os.path.join(xdg_config_home, 'user-dirs.dirs'), 'r') as _file:
                for line in _file:
                    if not line.startswith('#') and line.startswith('XDG_DOWNLOAD_DIR'):
                        download_dir = os.path.expandvars(line.partition("=")[2].rstrip().strip('"'))
                        break
        except IOError:
            pass

    if not download_dir:
        download_dir = os.path.join(os.path.expanduser("~"), 'Downloads')
    return download_dir

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
    :type fname: string
    :returns: a path to a pixmap file included with Deluge
    :rtype: string

    """
    return pkg_resources.resource_filename("deluge", os.path.join("data", \
                                           "pixmaps", fname))

def open_file(path, timestamp=None):
    """
    Opens a file or folder using the system configured program

    :param path: the path to the file or folder to open
    :type path: string
    :param timestamp: the timestamp of the event that requested to open
    :type timestamp: int

    """
    if windows_check():
        os.startfile(path.decode("utf8"))
    elif osx_check():
        subprocess.Popen(["open", "%s" % path])
    else:
        if timestamp is None:
            timestamp = int(time.time())
        env = os.environ.copy()
        env["DESKTOP_STARTUP_ID"] = "%s-%u-%s-xdg_open_TIME%d" % \
            (os.path.basename(sys.argv[0]), os.getpid(), os.uname()[1], timestamp)
        subprocess.Popen(["xdg-open", "%s" % path], env=env)

def open_url_in_browser(url):
    """
    Opens a url in the desktop's default browser

    :param url: the url to open
    :type url: string

    """
    import webbrowser
    webbrowser.open(url)

## Formatting text functions

def fsize(fsize_b):
    """
    Formats the bytes value into a string with KiB, MiB or GiB units

    :param fsize_b: the filesize in bytes
    :type fsize_b: int
    :returns: formatted string in KiB, MiB or GiB units
    :rtype: string

    **Usage**

    >>> fsize(112245)
    '109.6 KiB'

    """
    fsize_kb = fsize_b / 1024.0
    if fsize_kb < 1024:
        return "%.1f %s" % (fsize_kb, _("KiB"))
    fsize_mb = fsize_kb / 1024.0
    if fsize_mb < 1024:
        return "%.1f %s" % (fsize_mb, _("MiB"))
    fsize_gb = fsize_mb / 1024.0
    return "%.1f %s" % (fsize_gb, _("GiB"))

def fsize_short(fsize_b):
    """
    Formats the bytes value into a string with K, M or G units

    :param fsize_b: the filesize in bytes
    :type fsize_b: int
    :returns: formatted string in K, M or G units
    :rtype: string

    **Usage**

    >>> fsize(112245)
    '109.6 K'

    """
    fsize_kb = fsize_b / 1024.0
    if fsize_kb < 1024:
        return "%.1f %s" % (fsize_kb, _("K"))
    fsize_mb = fsize_kb / 1024.0
    if fsize_mb < 1024:
        return "%.1f %s" % (fsize_mb, _("M"))
    fsize_gb = fsize_mb / 1024.0
    return "%.1f %s" % (fsize_gb, _("G"))

def fpcnt(dec):
    """
    Formats a string to display a percentage with two decimal places

    :param dec: the ratio in the range [0.0, 1.0]
    :type dec: float
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

    :param bps: bytes per second
    :type bps: int
    :returns: a formatted string representing transfer speed
    :rtype: string

    **Usage**

    >>> fspeed(43134)
    '42.1 KiB/s'

    """
    fspeed_kb = bps / 1024.0
    if fspeed_kb < 1024:
        return "%.1f %s" % (fspeed_kb, _("KiB/s"))
    fspeed_mb = fspeed_kb / 1024.0
    if fspeed_mb < 1024:
        return "%.1f %s" % (fspeed_mb, _("MiB/s"))
    fspeed_gb = fspeed_mb / 1024.0
    return "%.1f %s" % (fspeed_gb, _("GiB/s"))

def fpeer(num_peers, total_peers):
    """
    Formats a string to show 'num_peers' ('total_peers')

    :param num_peers: the number of connected peers
    :type num_peers: int
    :param total_peers: the total number of peers
    :type total_peers: int
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

    :param seconds: the number of seconds
    :type seconds: int
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
    Formats a date time string in the locale's date representation based on the systems timezone

    :param seconds: time in seconds since the Epoch
    :type seconds: float
    :returns: a string in the locale's datetime representation or "" if seconds < 0
    :rtype: string

    """
    if seconds < 0:
        return ""
    return time.strftime("%x %X", time.localtime(seconds))

def is_url(url):
    """
    A simple test to check if the URL is valid

    :param url: the url to test
    :type url: string
    :returns: True or False
    :rtype: bool

    **Usage**

    >>> is_url("http://deluge-torrent.org")
    True

    """
    return url.partition('://')[0] in ("http", "https", "ftp", "udp")

def is_magnet(uri):
    """
    A check to determine if a uri is a valid bittorrent magnet uri

    :param uri: the uri to check
    :type uri: string
    :returns: True or False
    :rtype: bool

    **Usage**

    >>> is_magnet("magnet:?xt=urn:btih:SU5225URMTUEQLDXQWRB2EQWN6KLTYKN")
    True

    """
    magnet_scheme = 'magnet:?'
    xt_param = 'xt=urn:btih:'
    if uri.startswith(magnet_scheme) and xt_param in uri:
        return True
    return False

def create_magnet_uri(infohash, name=None, trackers=[]):
    """
    Creates a magnet uri

    :param infohash: the info-hash of the torrent
    :type infohash: string
    :param name: the name of the torrent (optional)
    :type name: string
    :param trackers: the trackers to announce to (optional)
    :type trackers: list of strings

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

    :param path: the path to check for size
    :type path: string
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

    :param path: the path to check
    :type path: string
    :returns: the free space at path in bytes
    :rtype: int

    :raises InvalidPathError: if the path is not valid

    """
    if not path or not os.path.exists(path):
        raise InvalidPathError("%s is not a valid path" % path)

    if windows_check():
        from win32file import GetDiskFreeSpaceEx
        return GetDiskFreeSpaceEx(path)[0]
    else:
        disk_data = os.statvfs(path.encode("utf8"))
        block_size = disk_data.f_frsize
        return disk_data.f_bavail * block_size

def is_ip(ip):
    """
    A simple test to see if 'ip' is valid

    :param ip: the ip to check
    :type ip: string
    :returns: True or False
    :rtype: bool

    ** Usage **

    >>> is_ip("127.0.0.1")
    True

    """
    import socket
    #first we test ipv4
    try:
        if windows_check():
            if socket.inet_aton("%s" % (ip)):
                return True
        else:
            if socket.inet_pton(socket.AF_INET, "%s" % (ip)):
                return True
    except socket.error:
        if not socket.has_ipv6:
            return False
    #now test ipv6
    try:
        if windows_check():
            log.warning("ipv6 check unavailable on windows")
            return True
        else:
            if socket.inet_pton(socket.AF_INET6, "%s" % (ip)):
                return True
    except socket.error:
        return False

def path_join(*parts):
    """
    An implementation of os.path.join that always uses / for the separator
    to ensure that the correct paths are produced when working with internal
    paths on Windows.
    """
    path = ''
    for part in parts:
        if not part:
            continue
        elif part[0] == '/':
            path = part
        elif not path:
            path = part
        else:
            path += '/' + part
    return path

XML_ESCAPES = (
    ('&', '&amp;'),
    ('<', '&lt;'),
    ('>', '&gt;'),
    ('"', '&quot;'),
    ("'", '&apos;')
)

def xml_decode(string):
    """
    Unescape a string that was previously encoded for use within xml.

    :param string: The string to escape
    :type string: string
    :returns: The unescaped version of the string.
    :rtype: string
    """
    for char, escape in XML_ESCAPES:
        string = string.replace(escape, char)
    return string

def xml_encode(string):
    """
    Escape a string for use within an xml element or attribute.

    :param string: The string to escape
    :type string: string
    :returns: An escaped version of the string.
    :rtype: string
    """
    for char, escape in XML_ESCAPES:
        string = string.replace(char, escape)
    return string

def decode_string(s, encoding="utf8"):
    """
    Decodes a string and return unicode. If it cannot decode using
    `:param:encoding` then it will try latin1, and if that fails,
    try to detect the string encoding. If that fails, decode with
    ignore.

    :param s: string to decode
    :type s: string
    :keyword encoding: the encoding to use in the decoding
    :type encoding: string
    :returns: s converted to unicode
    :rtype: unicode

    """
    if not s:
        return u''
    elif isinstance(s, unicode):
        return s

    encodings = [lambda: ("utf8", 'strict'),
                 lambda: ("iso-8859-1", 'strict'),
                 lambda: (chardet.detect(s)["encoding"], 'strict'),
                 lambda: (encoding, 'ignore')]

    if not encoding is "utf8":
        encodings.insert(0, lambda: (encoding, 'strict'))

    for l in encodings:
        try:
            return s.decode(*l())
        except UnicodeDecodeError:
            pass
    return u''

def utf8_encoded(s, encoding="utf8"):
    """
    Returns a utf8 encoded string of s

    :param s: (unicode) string to (re-)encode
    :type s: basestring
    :keyword encoding: the encoding to use in the decoding
    :type encoding: string
    :returns: a utf8 encoded string of s
    :rtype: str

    """
    if isinstance(s, str):
        s = decode_string(s, encoding).encode("utf8")
    elif isinstance(s, unicode):
        s = s.encode("utf8")
    return s

class VersionSplit(object):
    """
    Used for comparing version numbers.

    :param ver: the version
    :type ver: string

    """
    def __init__(self, ver):
        ver = ver.lower()
        vs = ver.replace("_", "-").split("-")
        self.version = [int(x) for x in vs[0].split(".") if x.isdigit()]
        self.suffix = None
        self.dev = False
        if len(vs) > 1:
            if vs[1].startswith(("rc", "alpha", "beta")):
                self.suffix = vs[1]
            if vs[-1] == 'dev':
                self.dev = True

    def __cmp__(self, ver):
        """
        The comparison method.

        :param ver: the version to compare with
        :type ver: VersionSplit

        """

        # If there is no suffix we use z because we want final
        # to appear after alpha, beta, and rc alphabetically.
        v1 = [self.version, self.suffix or 'z', self.dev]
        v2 = [ver.version, ver.suffix or 'z', ver.dev]
        return cmp(v1, v2)

def win32_unicode_argv():
    """ Gets sys.argv as list of unicode objects on any platform."""
    if windows_check():
        # Versions 2.x of Python don't support Unicode in sys.argv on Windows, with the
        # underlying Windows API instead replacing multi-byte characters with '?'.
        from ctypes import POINTER, byref, cdll, c_int, windll
        from ctypes.wintypes import LPCWSTR, LPWSTR

        get_cmd_linew = cdll.kernel32.GetCommandLineW
        get_cmd_linew.argtypes = []
        get_cmd_linew.restype = LPCWSTR

        cmdline_to_argvw = windll.shell32.CommandLineToArgvW
        cmdline_to_argvw.argtypes = [LPCWSTR, POINTER(c_int)]
        cmdline_to_argvw.restype = POINTER(LPWSTR)

        cmd = get_cmd_linew()
        argc = c_int(0)
        argv = cmdline_to_argvw(cmd, byref(argc))
        if argc.value > 0:
            # Remove Python executable and commands if present
            start = argc.value - len(sys.argv)
            return [argv[i] for i in xrange(start, argc.value)]
