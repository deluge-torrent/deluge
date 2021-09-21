# -*- coding: utf-8 -*-
#
# Copyright (C) 2007,2008 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

"""Common functions for various parts of Deluge to use."""
from __future__ import division, print_function, unicode_literals

import base64
import binascii
import functools
import glob
import locale
import logging
import numbers
import os
import platform
import re
import subprocess
import sys
import tarfile
import time
from contextlib import closing
from datetime import datetime
from io import BytesIO, open

import pkg_resources

from deluge.decorators import deprecated
from deluge.error import InvalidPathError

try:
    import chardet
except ImportError:
    chardet = None

try:
    from urllib.parse import unquote_plus, urljoin
    from urllib.request import pathname2url
except ImportError:
    # PY2 fallback
    from urllib import pathname2url, unquote_plus  # pylint: disable=ungrouped-imports
    from urlparse import urljoin  # pylint: disable=ungrouped-imports

# Windows workaround for HTTPS requests requiring certificate authority bundle.
# see: https://twistedmatrix.com/trac/ticket/9209
if platform.system() in ('Windows', 'Microsoft'):
    from certifi import where

    os.environ['SSL_CERT_FILE'] = where()


if platform.system() not in ('Windows', 'Microsoft', 'Darwin'):
    # gi makes dbus available on Window but don't import it as unused.
    try:
        import dbus
    except ImportError:
        dbus = None
    try:
        import distro
    except ImportError:
        distro = None

log = logging.getLogger(__name__)

TORRENT_STATE = [
    'Allocating',
    'Checking',
    'Downloading',
    'Seeding',
    'Paused',
    'Error',
    'Queued',
    'Moving',
]

# The output formatting for json.dump
JSON_FORMAT = {'indent': 4, 'sort_keys': True, 'ensure_ascii': False}

DBUS_FM_ID = 'org.freedesktop.FileManager1'
DBUS_FM_PATH = '/org/freedesktop/FileManager1'

PY2 = sys.version_info.major == 2


def get_version():
    """The program version from the egg metadata.

    Returns:
        str: The version of Deluge.
    """
    return pkg_resources.get_distribution('Deluge').version


def get_default_config_dir(filename=None):
    """
    :param filename: if None, only the config path is returned, if provided,
                     a path including the filename will be returned
    :type filename: string
    :returns: a file path to the config directory and optional filename
    :rtype: string

    """

    if windows_check():

        def save_config_path(resource):
            app_data_path = os.environ.get('APPDATA')
            if not app_data_path:
                try:
                    import winreg
                except ImportError:
                    import _winreg as winreg  # For Python 2.
                hkey = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    'Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Folders',
                )
                app_data_reg = winreg.QueryValueEx(hkey, 'AppData')
                app_data_path = app_data_reg[0]
                winreg.CloseKey(hkey)
            return os.path.join(app_data_path, resource)

    else:
        from xdg.BaseDirectory import save_config_path
    if not filename:
        filename = ''
    try:
        return decode_bytes(os.path.join(save_config_path('deluge'), filename))
    except OSError as ex:
        log.error('Unable to use default config directory, exiting... (%s)', ex)
        sys.exit(1)


def get_default_download_dir():
    """
    :returns: the default download directory
    :rtype: string

    """
    download_dir = ''
    if not windows_check():
        from xdg.BaseDirectory import xdg_config_home

        try:
            user_dirs_path = os.path.join(xdg_config_home, 'user-dirs.dirs')
            with open(user_dirs_path, 'r', encoding='utf8') as _file:
                for line in _file:
                    if not line.startswith('#') and line.startswith('XDG_DOWNLOAD_DIR'):
                        download_dir = os.path.expandvars(
                            line.partition('=')[2].rstrip().strip('"')
                        )
                        break
        except IOError:
            pass

    if not download_dir:
        download_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
    return download_dir


def archive_files(arc_name, filepaths, message=None, rotate=10):
    """Compress a list of filepaths into timestamped tarball in config dir.

    The archiving config directory is 'archive'.

    Args:
        arc_name (str): The archive output filename (appended with timestamp).
        filepaths (list): A list of the files to be archived into tarball.

    Returns:
        str: The full archive filepath.

    """

    from deluge.configmanager import get_config_dir

    # Set archive compression to lzma with bz2 fallback.
    arc_comp = 'xz' if not PY2 else 'bz2'

    archive_dir = os.path.join(get_config_dir(), 'archive')
    timestamp = datetime.now().replace(microsecond=0).isoformat().replace(':', '-')
    arc_filepath = os.path.join(
        archive_dir, arc_name + '-' + timestamp + '.tar.' + arc_comp
    )

    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
    else:
        all_arcs = glob.glob(os.path.join(archive_dir, arc_name) + '*')
        if len(all_arcs) >= rotate:
            log.warning(
                'Too many existing archives for %s. Deleting oldest archive.', arc_name
            )
            os.remove(sorted(all_arcs)[0])

    try:
        with tarfile.open(arc_filepath, 'w:' + arc_comp) as tar:
            for filepath in filepaths:
                if not os.path.isfile(filepath):
                    continue
                tar.add(filepath, arcname=os.path.basename(filepath))
            if message:
                with closing(BytesIO(message.encode('utf8'))) as fobj:
                    tarinfo = tarfile.TarInfo('archive_message.txt')
                    tarinfo.size = len(fobj.getvalue())
                    tarinfo.mtime = time.time()
                    tar.addfile(tarinfo, fileobj=fobj)
    except OSError:
        log.error('Problem occurred archiving filepaths: %s', filepaths)
        return False
    else:
        return arc_filepath


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
    return platform.release() == 'Vista'


def osx_check():
    """
    Checks if the current platform is Mac OS X

    :returns: True or False
    :rtype: bool

    """
    return platform.system() == 'Darwin'


def linux_check():
    """
    Checks if the current platform is Linux

    :returns: True or False
    :rtype: bool

    """
    return platform.system() == 'Linux'


def get_os_version():
    """Parse and return the os version information.

    Converts the platform ver tuple to a string.

    Returns:
        str: The os version info.

    """
    if windows_check():
        os_version = platform.win32_ver()
    elif osx_check():
        os_version = list(platform.mac_ver())
        os_version[1] = ''  # versioninfo always empty.
    elif distro:
        os_version = distro.linux_distribution()
    else:
        os_version = (platform.release(),)

    return ' '.join(filter(None, os_version))


def get_pixmap(fname):
    """
    Provides easy access to files in the deluge/ui/data/pixmaps folder within the Deluge egg

    :param fname: the filename to look for
    :type fname: string
    :returns: a path to a pixmap file included with Deluge
    :rtype: string

    """
    return resource_filename('deluge', os.path.join('ui', 'data', 'pixmaps', fname))


def resource_filename(module, path):
    """Get filesystem path for a resource.

    This function contains a work-around for pkg_resources.resource_filename
    not returning the correct path with multiple packages installed.

    So if there's a second deluge package, installed globally and another in
    develop mode somewhere else, while pkg_resources.get_distribution('Deluge')
    returns the proper deluge instance, pkg_resources.resource_filename
    does not, it returns the first found on the python path, which is wrong.
    """
    return pkg_resources.get_distribution('Deluge').get_resource_filename(
        pkg_resources._manager, os.path.join(*(module.split('.') + [path]))
    )


def open_file(path, timestamp=None):
    """Opens a file or folder using the system configured program.

    Args:
        path (str): The path to the file or folder to open.
        timestamp (int, optional): An event request timestamp.

    """
    if windows_check():
        os.startfile(path)
    elif osx_check():
        subprocess.Popen(['open', path])
    else:
        if timestamp is None:
            timestamp = int(time.time())
        env = os.environ.copy()
        env['DESKTOP_STARTUP_ID'] = '%s-%u-%s-xdg_open_TIME%d' % (
            os.path.basename(sys.argv[0]),
            os.getpid(),
            os.uname()[1],
            timestamp,
        )
        subprocess.Popen(['xdg-open', '%s' % path], env=env)


def show_file(path, timestamp=None):
    """Shows (highlights) a file or folder using the system configured file manager.

    Args:
        path (str): The path to the file or folder to show.
        timestamp (int, optional): An event request timestamp.

    """
    if windows_check():
        subprocess.Popen(['explorer', '/select,', path])
    elif osx_check():
        subprocess.Popen(['open', '-R', path])
    else:
        if timestamp is None:
            timestamp = int(time.time())
        startup_id = '%s_%u_%s-dbus_TIME%d TIMESTAMP=%d' % (
            os.path.basename(sys.argv[0]),
            os.getpid(),
            os.uname()[1],
            timestamp,
            timestamp,
        )

        if dbus:
            bus = dbus.SessionBus()
            try:
                filemanager1 = bus.get_object(DBUS_FM_ID, DBUS_FM_PATH)
            except dbus.exceptions.DBusException as ex:
                log.debug('Unable to get dbus file manager: %s', ex)
                # Fallback to xdg-open
            else:
                paths = [urljoin('file:', pathname2url(path))]
                filemanager1.ShowItems(paths, startup_id, dbus_interface=DBUS_FM_ID)
                return

        env = os.environ.copy()
        env['DESKTOP_STARTUP_ID'] = startup_id.replace('dbus', 'xdg-open')
        # No option in xdg to highlight a file so just open parent folder.
        subprocess.Popen(['xdg-open', os.path.dirname(path.rstrip('/'))], env=env)


def open_url_in_browser(url):
    """
    Opens a URL in the desktop's default browser

    :param url: the URL to open
    :type url: string

    """
    import webbrowser

    webbrowser.open(url)


# Formatting text functions
byte_txt = 'B'
kib_txt = 'KiB'
mib_txt = 'MiB'
gib_txt = 'GiB'
tib_txt = 'TiB'
kib_txt_short = 'K'
mib_txt_short = 'M'
gib_txt_short = 'G'
tib_txt_short = 'T'


def translate_size_units():
    """For performance reasons these units are translated outside the function"""

    global byte_txt, kib_txt, mib_txt, gib_txt, tib_txt
    global kib_txt_short, mib_txt_short, gib_txt_short, tib_txt_short

    byte_txt = _('B')
    kib_txt = _('KiB')
    mib_txt = _('MiB')
    gib_txt = _('GiB')
    tib_txt = _('TiB')
    kib_txt_short = _('K')
    mib_txt_short = _('M')
    gib_txt_short = _('G')
    tib_txt_short = _('T')


def fsize(fsize_b, precision=1, shortform=False):
    """Formats the bytes value into a string with KiB, MiB or GiB units.

    Args:
        fsize_b (int): The filesize in bytes.
        precision (int): The filesize float precision.

    Returns:
        str: A formatted string in KiB, MiB or GiB units.

    Examples:
        >>> fsize(112245)
        '109.6 KiB'
        >>> fsize(112245, precision=0)
        '110 KiB'

    Note:
        This function has been refactored for performance with the
        fsize units being translated outside the function.

    """

    if fsize_b >= 1024 ** 4:
        return '%.*f %s' % (
            precision,
            fsize_b / 1024 ** 4,
            tib_txt_short if shortform else tib_txt,
        )
    elif fsize_b >= 1024 ** 3:
        return '%.*f %s' % (
            precision,
            fsize_b / 1024 ** 3,
            gib_txt_short if shortform else gib_txt,
        )
    elif fsize_b >= 1024 ** 2:
        return '%.*f %s' % (
            precision,
            fsize_b / 1024 ** 2,
            mib_txt_short if shortform else mib_txt,
        )
    elif fsize_b >= 1024:
        return '%.*f %s' % (
            precision,
            fsize_b / 1024,
            kib_txt_short if shortform else kib_txt,
        )
    else:
        return '%d %s' % (fsize_b, byte_txt)


def fpcnt(dec, precision=2):
    """Formats a string to display a percentage with <precision> places.

    Args:
        dec (float): The ratio in the range [0.0, 1.0].
        precision (int): The percentage float precision.

    Returns:
        str: A formatted string representing a percentage.

    Examples:
        >>> fpcnt(0.9311)
        '93.11%'
        >>> fpcnt(0.9311, precision=0)
        '93%'

    """

    pcnt = dec * 100
    if pcnt == 0 or pcnt == 100:
        precision = 0
    return '%.*f%%' % (precision, pcnt)


def fspeed(bps, precision=1, shortform=False):
    """Formats a string to display a transfer speed.

    Args:
        bps (int): The speed in bytes per second.

    Returns:
        str: A formatted string representing transfer speed.

    Examples:
        >>> fspeed(43134)
        '42.1 KiB/s'

    """

    if bps < 1024 ** 2:
        return '%.*f %s' % (
            precision,
            bps / 1024,
            _('K/s') if shortform else _('KiB/s'),
        )
    elif bps < 1024 ** 3:
        return '%.*f %s' % (
            precision,
            bps / 1024 ** 2,
            _('M/s') if shortform else _('MiB/s'),
        )
    elif bps < 1024 ** 4:
        return '%.*f %s' % (
            precision,
            bps / 1024 ** 3,
            _('G/s') if shortform else _('GiB/s'),
        )
    else:
        return '%.*f %s' % (
            precision,
            bps / 1024 ** 4,
            _('T/s') if shortform else _('TiB/s'),
        )


def fpeer(num_peers, total_peers):
    """Formats a string to show 'num_peers' ('total_peers').

    Args:
        num_peers (int): The number of connected peers.
        total_peers (int): The total number of peers.

    Returns:
        str: A formatted string 'num_peers (total_peers)' or total_peers < 0, just 'num_peers'.

    Examples:
        >>> fpeer(10, 20)
        '10 (20)'
        >>> fpeer(10, -1)
        '10'

    """
    if total_peers > -1:
        return '{:d} ({:d})'.format(num_peers, total_peers)
    else:
        return '{:d}'.format(num_peers)


def ftime(secs):
    """Formats a string to show time in a human readable form.

    Args:
        secs (int or float): The number of seconds.

    Returns:
        str: A formatted time string or empty string if value is 0.

    Examples:
        >>> ftime(23011)
        '6h 23m'

    Note:
        This function has been refactored for performance.

    """

    # Handle floats by truncating to an int
    secs = int(secs)
    if secs <= 0:
        time_str = ''
    elif secs < 60:
        time_str = '{}s'.format(secs)
    elif secs < 3600:
        time_str = '{}m {}s'.format(secs // 60, secs % 60)
    elif secs < 86400:
        time_str = '{}h {}m'.format(secs // 3600, secs // 60 % 60)
    elif secs < 604800:
        time_str = '{}d {}h'.format(secs // 86400, secs // 3600 % 24)
    elif secs < 31449600:
        time_str = '{}w {}d'.format(secs // 604800, secs // 86400 % 7)
    else:
        time_str = '{}y {}w'.format(secs // 31449600, secs // 604800 % 52)

    return time_str


def fdate(seconds, date_only=False, precision_secs=False):
    """Formats a date time string in the locale's date representation based on the systems timezone.

    Args:
        seconds (float): Time in seconds since the Epoch.
        precision_secs (bool): Include seconds in time format.

    Returns:
        str: A string in the locale's datetime representation or "" if seconds < 0

    """

    if seconds < 0:
        return ''
    time_format = '%x %X' if precision_secs else '%x %H:%M'
    if date_only:
        time_format = time_format.split()[0]
    return time.strftime(time_format, time.localtime(seconds))


def tokenize(text):
    """
    Tokenize a text into numbers and strings.

    Args:
        text (str): The text to tokenize (a string).

    Returns:
        list: A list of strings and/or numbers.

    This function is used to implement robust tokenization of user input
    It automatically coerces integer and floating point numbers, ignores
    whitespace and knows how to separate numbers from strings even without
    whitespace.
    """
    tokenized_input = []
    for token in re.split(r'(\d+(?:\.\d+)?)', text):
        token = token.strip()
        if re.match(r'\d+\.\d+', token):
            tokenized_input.append(float(token))
        elif token.isdigit():
            tokenized_input.append(int(token))
        elif token:
            tokenized_input.append(token)
    return tokenized_input


size_units = [
    {'prefix': 'b', 'divider': 1, 'singular': 'byte', 'plural': 'bytes'},
    {'prefix': 'KiB', 'divider': 1024 ** 1},
    {'prefix': 'MiB', 'divider': 1024 ** 2},
    {'prefix': 'GiB', 'divider': 1024 ** 3},
    {'prefix': 'TiB', 'divider': 1024 ** 4},
    {'prefix': 'PiB', 'divider': 1024 ** 5},
    {'prefix': 'KB', 'divider': 1000 ** 1},
    {'prefix': 'MB', 'divider': 1000 ** 2},
    {'prefix': 'GB', 'divider': 1000 ** 3},
    {'prefix': 'TB', 'divider': 1000 ** 4},
    {'prefix': 'PB', 'divider': 1000 ** 5},
    {'prefix': 'm', 'divider': 1000 ** 2},
]


class InvalidSize(Exception):
    pass


def parse_human_size(size):
    """
    Parse a human readable data size and return the number of bytes.

    Args:
        size (str): The human readable file size to parse (a string).

    Returns:
        int: The corresponding size in bytes.

    Raises:
        InvalidSize: when the input can't be parsed.

    """
    tokens = tokenize(size)
    if tokens and isinstance(tokens[0], numbers.Number):
        # If the input contains only a number, it's assumed to be the number of bytes.
        if len(tokens) == 1:
            return int(tokens[0])
        # Otherwise we expect to find two tokens: A number and a unit.
        if len(tokens) == 2:
            try:
                normalized_unit = tokens[1].lower()
            except AttributeError:
                pass
            else:
                # Try to match the first letter of the unit.
                for unit in size_units:
                    if normalized_unit.startswith(unit['prefix'].lower()):
                        return int(tokens[0] * unit['divider'])
    # We failed to parse the size specification.
    msg = 'Failed to parse size! (input %r was tokenized as %r)'
    raise InvalidSize(msg % (size, tokens))


def is_url(url):
    """
    A simple test to check if the URL is valid

    :param url: the URL to test
    :type url: string
    :returns: True or False
    :rtype: bool

    :Example:

    >>> is_url('http://deluge-torrent.org')
    True

    """
    return url.partition('://')[0] in ('http', 'https', 'ftp', 'udp')


def is_infohash(infohash):
    """
    A check to determine if a string is a valid infohash.

    Args:
        infohash (str): The string to check.

    Returns:
        bool: True if valid infohash, False otherwise.

    """
    return len(infohash) == 40 and infohash.isalnum()


MAGNET_SCHEME = 'magnet:?'
XT_BTIH_PARAM = 'xt=urn:btih:'
DN_PARAM = 'dn='
TR_PARAM = 'tr='


def is_magnet(uri):
    """
    A check to determine if a URI is a valid bittorrent magnet URI

    :param uri: the URI to check
    :type uri: string
    :returns: True or False
    :rtype: bool

    :Example:

    >>> is_magnet('magnet:?xt=urn:btih:SU5225URMTUEQLDXQWRB2EQWN6KLTYKN')
    True

    """
    if not uri:
        return False

    return uri.startswith(MAGNET_SCHEME) and XT_BTIH_PARAM in uri


def get_magnet_info(uri):
    """Parse torrent information from magnet link.

    Args:
        uri (str): The magnet link.

    Returns:
        dict: Information about the magnet link.

        Format of the magnet dict::

            {
                "name": the torrent name,
                "info_hash": the torrents info_hash,
                "files_tree": empty value for magnet links
            }

    """

    tr0_param = 'tr.'
    tr0_param_regex = re.compile(r'^tr.(\d+)=(\S+)')
    if not uri.startswith(MAGNET_SCHEME):
        return {}

    name = None
    info_hash = None
    trackers = {}
    tier = 0
    for param in uri[len(MAGNET_SCHEME) :].split('&'):
        if param.startswith(XT_BTIH_PARAM):
            xt_hash = param[len(XT_BTIH_PARAM) :]
            if len(xt_hash) == 32:
                try:
                    infohash_str = base64.b32decode(xt_hash.upper())
                except TypeError as ex:
                    log.debug('Invalid base32 magnet hash: %s, %s', xt_hash, ex)
                    break
                info_hash = binascii.hexlify(infohash_str).decode()
            elif is_infohash(xt_hash):
                info_hash = xt_hash.lower()
            else:
                break
        elif param.startswith(DN_PARAM):
            name = unquote_plus(param[len(DN_PARAM) :])
        elif param.startswith(TR_PARAM):
            tracker = unquote_plus(param[len(TR_PARAM) :])
            trackers[tracker] = tier
            tier += 1
        elif param.startswith(tr0_param):
            try:
                tier, tracker = re.match(tr0_param_regex, param).groups()
                trackers[tracker] = tier
            except AttributeError:
                pass

    if info_hash:
        if not name:
            name = info_hash
        return {
            'name': name,
            'info_hash': info_hash,
            'files_tree': '',
            'trackers': trackers,
        }
    else:
        return {}


def create_magnet_uri(infohash, name=None, trackers=None):
    """Creates a magnet URI

    Args:
        infohash (str): The info-hash of the torrent.
        name (str, optional): The name of the torrent.
        trackers (list or dict, optional): A list of trackers or dict or {tracker: tier} pairs.

    Returns:
        str: A magnet URI string.

    """
    try:
        infohash = binascii.unhexlify(infohash)
    except TypeError:
        infohash.encode('utf-8')

    uri = [MAGNET_SCHEME, XT_BTIH_PARAM, base64.b32encode(infohash).decode('utf-8')]
    if name:
        uri.extend(['&', DN_PARAM, name])
    if trackers:
        try:
            for tracker in sorted(trackers, key=trackers.__getitem__):
                uri.extend(['&', 'tr.%d=' % trackers[tracker], tracker])
        except TypeError:
            for tracker in trackers:
                uri.extend(['&', TR_PARAM, tracker])

    return ''.join(uri)


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
    for (p, dummy_dirs, files) in os.walk(path):
        for _file in files:
            filename = os.path.join(p, _file)
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
        raise InvalidPathError('%s is not a valid path' % path)

    if windows_check():
        from win32file import GetDiskFreeSpaceEx

        return GetDiskFreeSpaceEx(path)[0]
    else:
        disk_data = os.statvfs(path.encode('utf8'))
        block_size = disk_data.f_frsize
        return disk_data.f_bavail * block_size


def is_ip(ip):
    """A test to see if 'ip' is a valid IPv4 or IPv6 address.

    Args:
        ip (str): The IP to test.

    Returns:
        bool: Whether IP is valid is not.

    Examples:
        >>> is_ip("192.0.2.0")
        True
        >>> is_ip("2001:db8::")
        True

    """

    return is_ipv4(ip) or is_ipv6(ip)


def is_ipv4(ip):
    """A test to see if 'ip' is a valid IPv4 address.

    Args:
        ip (str): The IP to test.

    Returns:
        bool: Whether IP is valid is not.

    Examples:
        >>> is_ipv4("192.0.2.0")
        True

    """

    import socket

    try:
        if windows_check():
            return socket.inet_aton(ip)
        else:
            return socket.inet_pton(socket.AF_INET, ip)
    except socket.error:
        return False


def is_ipv6(ip):
    """A test to see if 'ip' is a valid IPv6 address.

    Args:
        ip (str): The IP to test.

    Returns:
        bool: Whether IP is valid is not.

    Examples:
        >>> is_ipv6("2001:db8::")
        True

    """

    try:
        import ipaddress
    except ImportError:
        import socket

        try:
            return socket.inet_pton(socket.AF_INET6, ip)
        except (socket.error, AttributeError):
            if windows_check():
                log.warning('Unable to verify IPv6 Address on Windows.')
                return True
    else:
        try:
            return ipaddress.IPv6Address(decode_bytes(ip))
        except ipaddress.AddressValueError:
            pass

    return False


def decode_bytes(byte_str, encoding='utf8'):
    """Decodes a byte string and return unicode.

    If it cannot decode using `encoding` then it will try latin1,
    and if that fails, try to detect the string encoding. If that fails,
    decode with ignore.

    Args:
        byte_str (bytes): The byte string to decode.
        encoding (str): The encoding to try first when decoding.

    Returns:
        str: A unicode string.

    """
    if not byte_str:
        return ''
    elif not isinstance(byte_str, bytes):
        return byte_str

    encodings = [lambda: ('utf8', 'strict'), lambda: ('iso-8859-1', 'strict')]
    if chardet:
        encodings.append(lambda: (chardet.detect(byte_str)['encoding'], 'strict'))
    encodings.append(lambda: (encoding, 'ignore'))

    if encoding.lower() not in ['utf8', 'utf-8']:
        encodings.insert(0, lambda: (encoding, 'strict'))

    for enc in encodings:
        try:
            return byte_str.decode(*enc())
        except UnicodeDecodeError:
            pass
    return ''


@deprecated
def decode_string(byte_str, encoding='utf8'):
    """Deprecated: Use decode_bytes"""
    return decode_bytes(byte_str, encoding)


@deprecated
def utf8_encoded(str_, encoding='utf8'):
    """Deprecated: Use encode or decode_bytes if needed"""
    return decode_bytes(str_, encoding).encode('utf8')


def utf8_encode_structure(data):
    """Recursively convert all unicode keys and values in a data structure to utf8.

    e.g. converting keys and values for a dict with nested dicts and lists etc.

    Args:
        data (any): This can be any structure, dict, list or tuple.

    Returns:
        input type: The data with unicode keys and values converted to utf8.

    """
    if isinstance(data, (list, tuple)):
        return type(data)([utf8_encode_structure(d) for d in data])
    elif isinstance(data, dict):
        return {
            utf8_encode_structure(k): utf8_encode_structure(v) for k, v in data.items()
        }
    elif not isinstance(data, bytes):
        try:
            return data.encode('utf8')
        except AttributeError:
            pass
    return data


@functools.total_ordering
class VersionSplit(object):
    """
    Used for comparing version numbers.

    :param ver: the version
    :type ver: string

    """

    def __init__(self, ver):
        version_re = re.compile(
            r"""
        ^
        (?P<version>\d+\.\d+)          # minimum 'N.N'
        (?P<extraversion>(?:\.\d+)*)   # any number of extra '.N' segments
        (?:
            (?P<prerel>[abc]|rc)       # 'a'=alpha, 'b'=beta, 'c'=release candidate
                                       # 'rc'= alias for release candidate
            (?P<prerelversion>\d+(?:\.\d+)*)
        )?
        (?P<postdev>(\.post(?P<post>\d+))?(\.dev(?P<dev>\d+))?)?
        $""",
            re.VERBOSE,
        )

        # Check for PEP 386 compliant version
        match = re.search(version_re, ver)
        if match:
            group = [(x if x is not None else '') for x in match.group(1, 2, 3, 4, 8)]
            vs = [''.join(group[0:2]), ''.join(group[2:4]), group[4].lstrip('.')]
        else:
            ver = ver.lower()
            vs = ver.replace('_', '-').split('-')

        self.version = [int(x) for x in vs[0].split('.') if x.isdigit()]
        self.version_string = ''.join(str(x) for x in vs[0].split('.') if x.isdigit())
        self.suffix = None
        self.dev = None
        if len(vs) > 1:
            if vs[1].startswith(('rc', 'a', 'b', 'c')):
                self.suffix = vs[1]
            if vs[-1].startswith('dev'):
                try:
                    # Store only the dev numeral.
                    self.dev = int(vs[-1].rsplit('dev')[1])
                except ValueError:
                    # Implicit dev numeral is 0.
                    self.dev = 0

    def get_comparable_versions(self, other):
        """
        Returns a 2-tuple of lists for use in the comparison
        methods.
        """
        # PEP 386 versions with .devN precede release version so default
        # non-dev versions to infinity while dev versions are ints.
        self.dev = float('inf') if self.dev is None else self.dev
        other.dev = float('inf') if other.dev is None else other.dev
        # If there is no suffix we use z because we want final
        # to appear after alpha, beta, and rc alphabetically.
        v1 = [self.version, self.suffix or 'z', self.dev]
        v2 = [other.version, other.suffix or 'z', other.dev]

        return (v1, v2)

    def __eq__(self, other):
        v1, v2 = self.get_comparable_versions(other)
        return v1 == v2

    def __lt__(self, other):
        v1, v2 = self.get_comparable_versions(other)
        return v1 < v2


# Common AUTH stuff
AUTH_LEVEL_NONE = 0
AUTH_LEVEL_READONLY = 1
AUTH_LEVEL_NORMAL = 5
AUTH_LEVEL_ADMIN = 10
AUTH_LEVEL_DEFAULT = AUTH_LEVEL_NORMAL


def create_auth_file():
    import stat

    import deluge.configmanager

    auth_file = deluge.configmanager.get_config_dir('auth')
    # Check for auth file and create if necessary
    if not os.path.exists(auth_file):
        with open(auth_file, 'w', encoding='utf8') as _file:
            _file.flush()
            os.fsync(_file.fileno())
        # Change the permissions on the file so only this user can read/write it
        os.chmod(auth_file, stat.S_IREAD | stat.S_IWRITE)


def create_localclient_account(append=False):
    import random
    from hashlib import sha1 as sha

    import deluge.configmanager

    auth_file = deluge.configmanager.get_config_dir('auth')
    if not os.path.exists(auth_file):
        create_auth_file()

    with open(auth_file, 'a' if append else 'w', encoding='utf8') as _file:
        _file.write(
            ':'.join(
                [
                    'localclient',
                    sha(str(random.random()).encode('utf8')).hexdigest(),
                    str(AUTH_LEVEL_ADMIN),
                ]
            )
            + '\n'
        )
        _file.flush()
        os.fsync(_file.fileno())


def get_localhost_auth():
    """Grabs the localclient auth line from the 'auth' file and creates a localhost URI.

    Returns:
        tuple: With the username and password to login as.
    """
    from deluge.configmanager import get_config_dir

    auth_file = get_config_dir('auth')
    if not os.path.exists(auth_file):
        from deluge.common import create_localclient_account

        create_localclient_account()

    with open(auth_file, encoding='utf8') as auth:
        for line in auth:
            line = line.strip()
            if line.startswith('#') or not line:
                # This is a comment or blank line
                continue

            lsplit = line.split(':')

            if len(lsplit) == 2:
                username, password = lsplit
            elif len(lsplit) == 3:
                username, password, level = lsplit
            else:
                log.error('Your auth file is malformed: Incorrect number of fields!')
                continue

            if username == 'localclient':
                return (username, password)


def set_env_variable(name, value):
    """
    :param name: environment variable name
    :param value: environment variable value

    This function ensures that changes to an environment variable are applied
    to each copy of the environment variables used by a process. Starting from
    Python 2.4, os.environ changes only apply to the copy Python keeps (os.environ)
    and are no longer automatically applied to the other copies for the process.

    On Microsoft Windows, each process has multiple copies of the environment
    variables, one managed by the OS and one managed by the C library. We also
    need to take care of the fact that the C library used by Python is not
    necessarily the same as the C library used by pygtk and friends. This because
    the latest releases of pygtk and friends are built with mingw32 and are thus
    linked against msvcrt.dll. The official gtk+ binaries have always been built
    in this way.

    Basen on _putenv in TransUtils.py from sourceforge project gramps
    http://sourceforge.net/p/gramps/code/HEAD/tree/branches/maintenance/gramps32/src/TransUtils.py
    """
    # Update Python's copy of the environment variables
    try:
        os.environ[name] = value
    except UnicodeEncodeError:
        # Python 2
        os.environ[name] = value.encode('utf8')

    if windows_check():
        from ctypes import cdll, windll

        # Update the copy maintained by Windows (so SysInternals Process Explorer sees it)
        result = windll.kernel32.SetEnvironmentVariableW(name, value)
        if result == 0:
            log.info(
                "Failed to set Env Var '%s' (kernel32.SetEnvironmentVariableW)", name
            )
        else:
            log.debug(
                "Set Env Var '%s' to '%s' (kernel32.SetEnvironmentVariableW)",
                name,
                value,
            )

        # Update the copy maintained by msvcrt (used by gtk+ runtime)
        result = cdll.msvcrt._wputenv('%s=%s' % (name, value))
        if result != 0:
            log.info("Failed to set Env Var '%s' (msvcrt._putenv)", name)
        else:
            log.debug("Set Env Var '%s' to '%s' (msvcrt._putenv)", name, value)


def unicode_argv():
    """ Gets sys.argv as list of unicode objects on any platform."""
    if windows_check():
        # Versions 2.x of Python don't support Unicode in sys.argv on
        # Windows, with the underlying Windows API instead replacing multi-byte
        # characters with '?'.
        from ctypes import POINTER, byref, c_int, cdll, windll
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
            return [argv[i] for i in range(start, argc.value)]
    else:
        # On other platforms, we have to find the likely encoding of the args and decode
        # First check if sys.stdout or stdin have encoding set
        encoding = getattr(sys.stdout, 'encoding') or getattr(sys.stdin, 'encoding')
        # If that fails, check what the locale is set to
        encoding = encoding or locale.getpreferredencoding()
        # As a last resort, just default to utf-8
        encoding = encoding or 'utf-8'

        arg_list = []
        for arg in sys.argv:
            try:
                arg_list.append(arg.decode(encoding))
            except AttributeError:
                arg_list.append(arg)

        return arg_list


def run_profiled(func, *args, **kwargs):
    """
    Profile a function with cProfile

    Args:
        func (func): The function to profile
        *args (tuple): The arguments to pass to the function
        do_profile (bool, optional): If profiling should be performed. Defaults to True.
        output_file (str, optional): Filename to save profile results. If None, print to stdout.
                                     Defaults to None.
    """
    if kwargs.get('do_profile', True) is not False:
        import cProfile

        profiler = cProfile.Profile()

        def on_shutdown():
            output_file = kwargs.get('output_file', None)
            if output_file:
                profiler.dump_stats(output_file)
                log.info('Profile stats saved to %s', output_file)
                print('Profile stats saved to %s' % output_file)
            else:
                import pstats
                from io import StringIO

                strio = StringIO()
                ps = pstats.Stats(profiler, stream=strio).sort_stats('cumulative')
                ps.print_stats()
                print(strio.getvalue())

        try:
            return profiler.runcall(func, *args)
        finally:
            on_shutdown()
    else:
        return func(*args)


def is_process_running(pid):
    """
    Verify if the supplied pid is a running process.

    Args:
        pid (int): The pid to check.

    Returns:
        bool: True if pid is a running process, False otherwise.

    """

    if windows_check():
        from win32process import EnumProcesses

        return pid in EnumProcesses()
    else:
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        else:
            return True
