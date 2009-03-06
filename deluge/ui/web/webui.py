#
# deluge/ui/web/webui.py
#
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
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
#   Boston, MA    02110-1301, USA.
#

from twisted.internet import reactor


class WebUI:
    def __init__(self, args):
        import os
        import server
        print "Starting server in PID %s." % os.getpid()
        deluge_web = server.DelugeWeb()
        reactor.listenTCP(deluge_web.port, deluge_web.site)
        
        print "serving on 0.0.0.0:%(port)s view at http://127.0.0.1:%(port)s" % {
            "port": deluge_web.port
        }
        reactor.run()