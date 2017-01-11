#
# tracker_icons.py
#
# Copyright (C) 2010 John Garland <johnnybg+deluge@gmail.com>
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

from __future__ import with_statement

import os
from HTMLParser import HTMLParser, HTMLParseError
from urlparse import urljoin, urlparse
from tempfile import mkstemp

from twisted.internet import defer, threads
from twisted.web.error import PageRedirect
try:
    from twisted.web.resource import NoResource, ForbiddenResource
except ImportError:
    # twisted 8
    from twisted.web.error import NoResource, ForbiddenResource

from deluge.component import Component
from deluge.configmanager import get_config_dir
from deluge.httpdownloader import download_file
from deluge.decorators import proxy
from deluge.log import LOG as log

try:
    import PIL.Image as Image
    import deluge.ui.Win32IconImagePlugin
except ImportError:
    PIL_INSTALLED = False
else:
    PIL_INSTALLED = True

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
        return os.path.samefile(self.filename, other.filename) or \
               self.get_mimetype() == other.get_mimetype() and \
               self.get_data() == other.get_data()

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
            f = open(self.filename, "rb")
            self.data = f.read()
            f.close()
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
        Component.__init__(self, "TrackerIcons")
        if not icon_dir:
            icon_dir = get_config_dir("icons")
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
                    log.warning("invalid icon %s", icon)
        if no_icon:
            self.icons[None] = TrackerIcon(no_icon)
        else:
            self.icons[None] = None
        self.icons[''] = self.icons[None]

        self.pending = {}
        self.redirects = {}

    def get(self, host):
        """
        Returns a TrackerIcon for the given tracker's host

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
            d.addCallbacks(self.on_download_page_complete, self.on_download_page_fail,
                           errbackArgs=(host,))
            d.addCallback(self.parse_html_page)
            d.addCallbacks(self.on_parse_complete, self.on_parse_fail,
                           callbackArgs=(host,))
            d.addCallback(self.download_icon, host)
            d.addCallbacks(self.on_download_icon_complete, self.on_download_icon_fail,
                           callbackArgs=(host,), errbackArgs=(host,))
            if PIL_INSTALLED:
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
        log.debug("Downloading %s %s", host, url)
        fd, filename = mkstemp(prefix='deluge_ticon.')
        os.close(fd)
        return download_file(url, filename, force_filename=True)

    def on_download_page_complete(self, page):
        """
        Runs any download clean up functions

        :param page: the page that finished downloading
        :type page: string
        :returns: the page that finished downloading
        :rtype: string
        """
        log.debug("Finished downloading %s", page)
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
        log.debug("Error downloading page: %s", error_msg)
        d = f
        if f.check(PageRedirect):
            # Handle redirect errors
            location = urljoin(self.host_to_url(host), error_msg.split(" to ")[1])
            self.redirects[host] = url_to_host(location)
            d = self.download_page(host, url=location)
            d.addCallbacks(self.on_download_page_complete, self.on_download_page_fail,
                           errbackArgs=(host,))

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
        f = open(page, "r")
        parser = FaviconParser()
        for line in f:
            parser.feed(line)
            if parser.left_head:
                break
        parser.close()
        f.close()
        try:
            os.remove(page)
        except Exception, e:
            log.warning("Couldn't remove temp file: %s", e)

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
        log.debug("Parse Complete, got icons for %s: %s", host, icons)
        url = self.host_to_url(host)
        icons = [(urljoin(url, icon), mimetype) for icon, mimetype in icons]
        log.debug("Icon urls from %s: %s", host, icons)
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
        log.debug("Error parsing page: %s", f.getErrorMessage())
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
            raise NoIconsError, "empty icons list"
        (url, mimetype) = icons.pop(0)
        d = download_file(url, os.path.join(self.dir, host_to_icon_name(host, mimetype)),
                          force_filename=True)
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

        if PIL_INSTALLED:
            try:
                Image.open(icon_name)
            except IOError, e:
                raise InvalidIconError(e)
        else:
            if os.stat(icon_name).st_size == 0L:
                raise InvalidIconError("empty icon")

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
        log.debug("Successfully downloaded from %s: %s", host, icon_name)
        icon = TrackerIcon(icon_name)
        return icon

    def on_download_icon_fail(self, f, host, icons=[]):
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
        error_msg = f.getErrorMessage()
        log.debug("Error downloading icon from %s: %s", host, error_msg)
        d = f
        if f.check(PageRedirect):
            # Handle redirect errors
            location = urljoin(self.host_to_url(host), error_msg.split(" to ")[1])
            d = self.download_icon([(location, extension_to_mimetype(location.rpartition('.')[2]))] + icons, host)
            if not icons:
                d.addCallbacks(self.on_download_icon_complete, self.on_download_icon_fail,
                               callbackArgs=(host,), errbackArgs=(host,))
        elif f.check(NoResource, ForbiddenResource) and icons:
            d = self.download_icon(icons, host)
        elif f.check(NoIconsError, HTMLParseError):
            # No icons, try favicon.ico as an act of desperation
            d = self.download_icon([(urljoin(self.host_to_url(host), "favicon.ico"), extension_to_mimetype("ico"))], host)
            d.addCallbacks(self.on_download_icon_complete, self.on_download_icon_fail,
                           callbackArgs=(host,), errbackArgs=(host,))
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
        if icon:
            filename = icon.get_filename()
            img = Image.open(filename)
            if img.size > (16, 16):
                new_filename = filename.rpartition('.')[0]+".png"
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
        return "http://%s/" % host

################################ HELPER CLASSES ###############################

class FaviconParser(HTMLParser):
    """
    A HTMLParser which extracts favicons from a HTML page
    """
    def __init__(self):
        self.icons = []
        self.left_head = False
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if tag == "link" and ("rel", "icon") in attrs or ("rel", "shortcut icon") in attrs:
            href = None
            type = None
            for attr, value in attrs:
                if attr == "href":
                    href = value
                elif attr == "type":
                    type = value
            if href:
                try:
                    mimetype = extension_to_mimetype(href.rpartition('.')[2])
                except KeyError:
                    pass
                else:
                    type = mimetype
                if type:
                    self.icons.append((href, type))

    def handle_endtag(self, tag):
        if tag == "head":
            self.left_head = True

    def get_icons(self):
        """
        Returns a list of favicons extracted from the HTML page

        :returns: a list of favicons
        :rtype: list
        """
        return self.icons


############################### HELPER FUNCTIONS ##############################

def url_to_host(url):
    """
    Given a URL, returns the host it belongs to

    :param url: the URL in question
    :type url: string
    :returns: the host of the given URL
    :rtype:string
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
    return host+'.'+mimetype_to_extension(mimetype)

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
    "image/gif" : "gif",
    "image/jpeg" : "jpg",
    "image/png" : "png",
    "image/vnd.microsoft.icon" : "ico",
    "image/x-icon" : "ico",
    "gif" : "image/gif",
    "jpg" : "image/jpeg",
    "jpeg" : "image/jpeg",
    "png" : "image/png",
    "ico" : "image/vnd.microsoft.icon",
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

################################## EXCEPTIONS #################################

class NoIconsError(Exception):
    pass

class InvalidIconError(Exception):
    pass
