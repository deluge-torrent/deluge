#
# httpdownloader.py
#
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

from twisted.web import client
from twisted.internet import reactor

class HTTPDownloader(client.HTTPDownloader):
    """
    Factory class for downloading files and keeping track of progress.
    """
    def __init__(self, url, filename, part_callback=None):
        """
        :param url: str, the url to download from
        :param filename: str, the filename to save the file as
        :param part_callback: func, a function to be called when a part of data
            is received, it's signature should be: func(data, current_length, total_length)
        """
        self.__part_callback = part_callback
        self.current_length = 0
        client.HTTPDownloader.__init__(self, url, filename)

    def gotHeaders(self, headers):
        if self.status == "200":
            if "content-length" in headers:
                self.total_length = int(headers["content-length"][0])
            else:
                self.total_length = 0

        return client.HTTPDownloader.gotHeaders(self, headers)

    def pagePart(self, data):
        if self.status == "200":
            self.current_length += len(data)
            if self.__part_callback:
                self.__part_callback(data, self.current_length, self.total_length)

        return client.HTTPDownloader.pagePart(self, data)

def download_file(url, filename, callback=None):
    """
    Downloads a file from a specific URL and returns a Deferred.  You can also
    specify a callback function to be called as parts are received.

    :param url: str, the url to download from
    :param filename: str, the filename to save the file as
    :param callback: func, a function to be called when a part of data is received,
         it's signature should be: func(data, current_length, total_length)
    """
    url = str(url)
    scheme, host, port, path = client._parse(url)
    factory = HTTPDownloader(url, filename, callback)
    if scheme == "https":
        from twisted.internet import ssl
        reactor.connectSSL(host, port, factory, ssl.ClientContextFactory())
    else:
        reactor.connectTCP(host, port, factory)

    return factory.deferred
