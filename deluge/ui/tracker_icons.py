# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 John Garland <johnnybg+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging
import os
from tempfile import mkstemp

from twisted.internet import defer, threads
from twisted.web.error import PageRedirect
from twisted.web.resource import ForbiddenResource, NoResource

from deluge.component import Component
from deluge.configmanager import get_config_dir
from deluge.decorators import proxy
from deluge.httpdownloader import download_file

try:
    from html.parser import HTMLParser
    from urllib.parse import urljoin, urlparse
except ImportError:
    # PY2 fallback
    from HTMLParser import HTMLParser
    from urlparse import urljoin, urlparse  # pylint: disable=ungrouped-imports

try:
    from PIL import Image
except ImportError:
    Image = None

log = logging.getLogger(__name__)


class TrackerIcon(object):
    """
    Represents a tracker's icon
    """

    def __init__(self, filename):
        """
        Initialises a new TrackerIcon object

        :param filename: the filename of the icon
        :type filename: string
        """
        self.filename = os.path.abspath(filename)
        self.mimetype = extension_to_mimetype(self.filename.rpartition('.')[2])
        self.data = None
        self.icon_cache = None

    def __eq__(self, other):
        """
        Compares this TrackerIcon with another to determine if they're equal

        :param other: the TrackerIcon to compare to
        :type other: TrackerIcon
        :returns: whether or not they're equal
        :rtype: boolean
        """
        return (
            os.path.samefile(self.filename, other.filename)
            or self.get_mimetype() == other.get_mimetype()
            and self.get_data() == other.get_data()
        )

    def get_mimetype(self):
        """
        Returns the mimetype of this TrackerIcon's image

        :returns: the mimetype of the image
        :rtype: string
        """
        return self.mimetype

    def get_data(self):
        """
        Returns the TrackerIcon's image data as a string

        :returns: the image data
        :rtype: string
        """
        if not self.data:
            with open(self.filename, 'rb') as _file:
                self.data = _file.read()
        return self.data

    def get_filename(self, full=True):
        """
        Returns the TrackerIcon image's filename

        :param full: an (optional) arg to indicate whether or not to
                     return the full path
        :type full: boolean
        :returns: the path of the TrackerIcon's image
        :rtype: string
        """
        return self.filename if full else os.path.basename(self.filename)

    def set_cached_icon(self, data):
        """
        Set the cached icon data.

        """
        self.icon_cache = data

    def get_cached_icon(self):
        """
        Returns the cached icon data.

        """
        return self.icon_cache


class TrackerIcons(Component):
    """
    A TrackerIcon factory class
    """

    def __init__(self, icon_dir=None, no_icon=None):
        """
        Initialises a new TrackerIcons object

        :param icon_dir: the (optional) directory of where to store the icons
        :type icon_dir: string
        :param no_icon: the (optional) path name of the icon to show when no icon
                       can be fetched
        :type no_icon: string
        """
        Component.__init__(self, 'TrackerIcons')
        if not icon_dir:
            icon_dir = get_config_dir('icons')
        self.dir = icon_dir
        if not os.path.isdir(self.dir):
            os.makedirs(self.dir)

        self.icons = {}
        for icon in os.listdir(self.dir):
            if icon != no_icon:
                host = icon_name_to_host(icon)
                try:
                    self.icons[host] = TrackerIcon(os.path.join(self.dir, icon))
                except KeyError:
                    log.warning('invalid icon %s', icon)
        if no_icon:
            self.icons[None] = TrackerIcon(no_icon)
        else:
            self.icons[None] = None
        self.icons[''] = self.icons[None]

        self.pending = {}
        self.redirects = {}

    def has(self, host):
        """
        Returns True or False if the tracker icon for the given host exists or not.

        :param host: the host for the TrackerIcon
        :type host: string
        :returns: True or False
        :rtype: bool
        """
        return host.lower() in self.icons

    def get(self, host):
        """
        Returns a TrackerIcon for the given tracker's host
        from the icon cache.

        :param host: the host for the TrackerIcon
        :type host: string
        :returns: the TrackerIcon for the host
        :rtype: TrackerIcon
        """
        host = host.lower()
        if host in self.icons:
            return self.icons[host]
        else:
            return None

    def fetch(self, host):
        """
        Fetches (downloads) the icon for the given host.
        When the icon is downloaded a callback is fired
        on the the queue of callers to this function.

        :param host: the host to obtain the TrackerIcon for
        :type host: string
        :returns: a Deferred which fires with the TrackerIcon for the given host
        :rtype: Deferred
        """
        host = host.lower()
        if host in self.icons:
            # We already have it, so let's return it
            d = defer.succeed(self.icons[host])
        elif host in self.pending:
            # We're in the middle of getting it
            # Add ourselves to the waiting list
            d = defer.Deferred()
            self.pending[host].append(d)
        else:
            # We need to fetch it
            self.pending[host] = []
            # Start callback chain
            d = self.download_page(host)
            d.addCallbacks(
                self.on_download_page_complete,
                self.on_download_page_fail,
                errbackArgs=(host,),
            )
            d.addCallback(self.parse_html_page)
            d.addCallbacks(
                self.on_parse_complete, self.on_parse_fail, callbackArgs=(host,)
            )
            d.addCallback(self.download_icon, host)
            d.addCallbacks(
                self.on_download_icon_complete,
                self.on_download_icon_fail,
                callbackArgs=(host,),
                errbackArgs=(host,),
            )
            d.addCallback(self.resize_icon)
            d.addCallback(self.store_icon, host)
        return d

    def download_page(self, host, url=None):
        """
        Downloads a tracker host's page
        If no url is provided, it bases the url on the host

        :param host: the tracker host
        :type host: string
        :param url: the (optional) url of the host
        :type url: string
        :returns: the filename of the tracker host's page
        :rtype: Deferred
        """
        if not url:
            url = self.host_to_url(host)
        log.debug('Downloading %s %s', host, url)
        tmp_fd, tmp_file = mkstemp(prefix='deluge_ticon.')
        os.close(tmp_fd)
        return download_file(url, tmp_file, force_filename=True, handle_redirects=False)

    def on_download_page_complete(self, page):
        """
        Runs any download clean up functions

        :param page: the page that finished downloading
        :type page: string
        :returns: the page that finished downloading
        :rtype: string
        """
        log.debug('Finished downloading %s', page)
        return page

    def on_download_page_fail(self, f, host):
        """
        Recovers from download error

        :param f: the failure that occurred
        :type f: Failure
        :param host: the name of the host whose page failed to download
        :type host: string
        :returns: a Deferred if recovery was possible
                  else the original failure
        :rtype: Deferred or Failure
        """
        error_msg = f.getErrorMessage()
        log.debug('Error downloading page: %s', error_msg)
        d = f
        if f.check(PageRedirect):
            # Handle redirect errors
            location = urljoin(self.host_to_url(host), error_msg.split(' to ')[1])
            self.redirects[host] = url_to_host(location)
            d = self.download_page(host, url=location)
            d.addCallbacks(
                self.on_download_page_complete,
                self.on_download_page_fail,
                errbackArgs=(host,),
            )

        return d

    @proxy(threads.deferToThread)
    def parse_html_page(self, page):
        """
        Parses the html page for favicons

        :param page: the page to parse
        :type page: string
        :returns: a Deferred which callbacks a list of available favicons (url, type)
        :rtype: Deferred
        """
        with open(page, 'r') as _file:
            parser = FaviconParser()
            for line in _file:
                parser.feed(line)
                if parser.left_head:
                    break
            parser.close()
        try:
            os.remove(page)
        except OSError as ex:
            log.warning('Could not remove temp file: %s', ex)

        return parser.get_icons()

    def on_parse_complete(self, icons, host):
        """
        Runs any parse clean up functions

        :param icons: the icons that were extracted from the page
        :type icons: list
        :param host: the host the icons are for
        :type host: string
        :returns: the icons that were extracted from the page
        :rtype: list
        """
        log.debug('Parse Complete, got icons for %s: %s', host, icons)
        url = self.host_to_url(host)
        icons = [(urljoin(url, icon), mimetype) for icon, mimetype in icons]
        log.debug('Icon urls from %s: %s', host, icons)
        return icons

    def on_parse_fail(self, f):
        """
        Recovers from a parse error

        :param f: the failure that occurred
        :type f: Failure
        :returns: a Deferred if recovery was possible
                  else the original failure
        :rtype: Deferred or Failure
        """
        log.debug('Error parsing page: %s', f.getErrorMessage())
        return f

    def download_icon(self, icons, host):
        """
        Downloads the first available icon from icons

        :param icons: a list of icons
        :type icons: list
        :param host: the tracker's host name
        :type host: string
        :returns: a Deferred which fires with the downloaded icon's filename
        :rtype: Deferred
        """
        if len(icons) == 0:
            raise NoIconsError('empty icons list')
        (url, mimetype) = icons.pop(0)
        d = download_file(
            url,
            os.path.join(self.dir, host_to_icon_name(host, mimetype)),
            force_filename=True,
        )
        d.addCallback(self.check_icon_is_valid)
        if icons:
            d.addErrback(self.on_download_icon_fail, host, icons)
        return d

    @proxy(threads.deferToThread)
    def check_icon_is_valid(self, icon_name):
        """
        Performs a sanity check on icon_name

        :param icon_name: the name of the icon to check
        :type icon_name: string
        :returns: the name of the validated icon
        :rtype: string
        :raises: InvalidIconError
        """

        if Image:
            try:
                with Image.open(icon_name):
                    pass
            except IOError as ex:
                raise InvalidIconError(ex)
        else:
            if not os.path.getsize(icon_name):
                raise InvalidIconError('empty icon')

        return icon_name

    def on_download_icon_complete(self, icon_name, host):
        """
        Runs any download cleanup functions

        :param icon_name: the filename of the icon that finished downloading
        :type icon_name: string
        :param host: the host the icon completed to download for
        :type host: string
        :returns: the icon that finished downloading
        :rtype: TrackerIcon
        """
        log.debug('Successfully downloaded from %s: %s', host, icon_name)
        return TrackerIcon(icon_name)

    def on_download_icon_fail(self, f, host, icons=None):
        """
        Recovers from a download error

        :param f: the failure that occurred
        :type f: Failure
        :param host: the host the icon failed to download for
        :type host: string
        :param icons: the (optional) list of remaining icons
        :type icons: list
        :returns: a Deferred if recovery was possible
                  else the original failure
        :rtype: Deferred or Failure
        """
        if not icons:
            icons = []
        error_msg = f.getErrorMessage()
        log.debug('Error downloading icon from %s: %s', host, error_msg)
        d = f
        if f.check(PageRedirect):
            # Handle redirect errors
            location = urljoin(self.host_to_url(host), error_msg.split(' to ')[1])
            d = self.download_icon(
                [(location, extension_to_mimetype(location.rpartition('.')[2]))]
                + icons,
                host,
            )
            if not icons:
                d.addCallbacks(
                    self.on_download_icon_complete,
                    self.on_download_icon_fail,
                    callbackArgs=(host,),
                    errbackArgs=(host,),
                )
        elif f.check(NoResource, ForbiddenResource) and icons:
            d = self.download_icon(icons, host)
        elif f.check(NoIconsError):
            # No icons, try favicon.ico as an act of desperation
            d = self.download_icon(
                [
                    (
                        urljoin(self.host_to_url(host), 'favicon.ico'),
                        extension_to_mimetype('ico'),
                    )
                ],
                host,
            )
            d.addCallbacks(
                self.on_download_icon_complete,
                self.on_download_icon_fail,
                callbackArgs=(host,),
                errbackArgs=(host,),
            )
        else:
            # No icons :(
            # Return the None Icon
            d = self.icons[None]

        return d

    @proxy(threads.deferToThread)
    def resize_icon(self, icon):
        """
        Resizes the given icon to be 16x16 pixels

        :param icon: the icon to resize
        :type icon: TrackerIcon
        :returns: the resized icon
        :rtype: TrackerIcon
        """
        # Requires Pillow(PIL) to resize.
        if icon and Image:
            filename = icon.get_filename()
            with Image.open(filename) as img:
                if img.size > (16, 16):
                    new_filename = filename.rpartition('.')[0] + '.png'
                    img = img.resize((16, 16), Image.ANTIALIAS)
                    img.save(new_filename)
                    if new_filename != filename:
                        os.remove(filename)
                        icon = TrackerIcon(new_filename)
        return icon

    def store_icon(self, icon, host):
        """
        Stores the icon for the given host
        Callbacks any pending deferreds waiting on this icon

        :param icon: the icon to store
        :type icon: TrackerIcon or None
        :param host: the host to store it for
        :type host: string
        :returns: the stored icon
        :rtype: TrackerIcon or None
        """
        self.icons[host] = icon
        for d in self.pending[host]:
            d.callback(icon)
        del self.pending[host]
        return icon

    def host_to_url(self, host):
        """
        Given a host, returns the URL to fetch

        :param host: the tracker host
        :type host: string
        :returns: the url of the tracker
        :rtype: string
        """
        if host in self.redirects:
            host = self.redirects[host]
        return 'http://%s/' % host


# ------- HELPER CLASSES ------


class FaviconParser(HTMLParser):
    """
    A HTMLParser which extracts favicons from a HTML page
    """

    def __init__(self):
        self.icons = []
        self.left_head = False
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if (
            tag == 'link'
            and ('rel', 'icon') in attrs
            or ('rel', 'shortcut icon') in attrs
        ):
            href = None
            icon_type = None
            for attr, value in attrs:
                if attr == 'href':
                    href = value
                elif attr == 'type':
                    icon_type = value
            if href:
                try:
                    mimetype = extension_to_mimetype(href.rpartition('.')[2])
                except KeyError:
                    pass
                else:
                    icon_type = mimetype
                if icon_type:
                    self.icons.append((href, icon_type))

    def handle_endtag(self, tag):
        if tag == 'head':
            self.left_head = True

    def get_icons(self):
        """
        Returns a list of favicons extracted from the HTML page

        :returns: a list of favicons
        :rtype: list
        """
        return self.icons


# ------ HELPER FUNCTIONS ------


def url_to_host(url):
    """
    Given a URL, returns the host it belongs to

    :param url: the URL in question
    :type url: string
    :returns: the host of the given URL
    :rtype: string
    """
    return urlparse(url).hostname


def host_to_icon_name(host, mimetype):
    """
    Given a host, returns the appropriate icon name

    :param host: the host in question
    :type host: string
    :param mimetype: the mimetype of the icon
    :type mimetype: string
    :returns: the icon's filename
    :rtype: string

    """
    return host + '.' + mimetype_to_extension(mimetype)


def icon_name_to_host(icon):
    """
    Given a host's icon name, returns the host name

    :param icon: the icon name
    :type icon: string
    :returns: the host name
    :rtype: string
    """
    return icon.rpartition('.')[0]


MIME_MAP = {
    'image/gif': 'gif',
    'image/jpeg': 'jpg',
    'image/png': 'png',
    'image/vnd.microsoft.icon': 'ico',
    'image/x-icon': 'ico',
    'gif': 'image/gif',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'ico': 'image/vnd.microsoft.icon',
}


def mimetype_to_extension(mimetype):
    """
    Given a mimetype, returns the appropriate filename extension

    :param mimetype: the mimetype
    :type mimetype: string
    :returns: the filename extension for the given mimetype
    :rtype: string
    :raises KeyError: if given an invalid mimetype
    """
    return MIME_MAP[mimetype.lower()]


def extension_to_mimetype(extension):
    """
    Given a filename extension, returns the appropriate mimetype

    :param extension: the filename extension
    :type extension: string
    :returns: the mimetype for the given filename extension
    :rtype: string
    :raises KeyError: if given an invalid filename extension
    """
    return MIME_MAP[extension.lower()]


#  ------ EXCEPTIONS ------


class NoIconsError(Exception):
    pass


class InvalidIconError(Exception):
    pass
