#
# core.py
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

import deluge.component as component
from deluge.log import LOG as log

#special purpose filters:
def filter_keyword(torrent):
    pass

def filter_state_active(torrent):
    pass

class FilterManager(component.Component):
    """FilterManager

    """
    def __init__(self, core):
        component.Component.__init__(self, "FilterManager")
        log.debug("FilterManager init..")
        self.core = core
        self.torrents = core.torrents

    def filter_torrent_ids(self, filter_dict):
        """
        internal :
        returns a list of torrent_id's matching filter_dict.
        """
        if not filter_dict:
            return self.torrents.get_torrent_list()

        if "id"in filter_dict: #optimized filter for id:
            torrent_ids = filter_dict["id"]
            del filter_dict["id"]
        else:
            torrent_ids = self.torrents.get_torrent_list()

        #todo:
        #register/deregister special filters like "text search" and "active"
        #

        #leftover filter arguments:
        #default filter on status fields.
        if filter_dict:
            status_func = self.core.export_get_torrent_status #premature optimalisation..
            for torrent_id in list(torrent_ids):
                status = status_func(torrent_id, filter_dict.keys()) #status={id:{key:value}}
                for field, value_list in filter_dict.iteritems():
                    if (not status[field] in value_list) and torrent_id in torrent_ids:
                        torrent_ids.remove(torrent_id)

        return torrent_ids


