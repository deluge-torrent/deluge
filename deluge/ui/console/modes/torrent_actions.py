# torrent_actions.py
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
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

from deluge.ui.client import client
from popup import SelectablePopup

import logging
log = logging.getLogger(__name__)

class ACTION:
    PAUSE=0
    RESUME=1
    REANNOUNCE=2
    EDIT_TRACKERS=3
    RECHECK=4
    REMOVE=5

    REMOVE_DATA=6
    REMOVE_NODATA=7

    DETAILS=8

def action_error(error,mode):
    rerr = error.value
    mode.report_message("An Error Occurred","%s got error %s: %s"%(rerr.method,rerr.exception_type,rerr.exception_msg))
    mode.refresh()

def torrent_action(idx, data, mode, ids):
    if ids:
        if data==ACTION.PAUSE:
            log.debug("Pausing torrents: %s",ids)
            client.core.pause_torrent(ids).addErrback(action_error,mode)
        elif data==ACTION.RESUME:
            log.debug("Resuming torrents: %s", ids)
            client.core.resume_torrent(ids).addErrback(action_error,mode)
        elif data==ACTION.REMOVE:
            def do_remove(idx,data,mode,ids):
                if data:
                    wd = data==ACTION.REMOVE_DATA
                    for tid in ids:
                        log.debug("Removing torrent: %s,%d",tid,wd)
                        client.core.remove_torrent(tid,wd).addErrback(action_error,mode)
                if len(ids) == 1:
                    mode.clear_marks()
                return True
            popup = SelectablePopup(mode,"Confirm Remove",do_remove,mode,ids)
            popup.add_line("Are you sure you want to remove the marked torrents?",selectable=False)
            popup.add_line("Remove with _data",data=ACTION.REMOVE_DATA)
            popup.add_line("Remove _torrent",data=ACTION.REMOVE_NODATA)
            popup.add_line("_Cancel",data=0)
            mode.set_popup(popup)
            return False
        elif data==ACTION.RECHECK:
            log.debug("Rechecking torrents: %s", ids)
            client.core.force_recheck(ids).addErrback(action_error,mode)
        elif data==ACTION.REANNOUNCE:
            log.debug("Reannouncing torrents: %s",ids)
            client.core.force_reannounce(ids).addErrback(action_error,mode)
        elif data==ACTION.DETAILS:
            log.debug("Torrent details")
            tid = mode.current_torrent_id()
            if tid:
                mode.show_torrent_details(tid)
            else:
                log.error("No current torrent in _torrent_action, this is a bug")
    if len(ids) == 1:
        mode.clear_marks()
    return True

# Creates the popup.  mode is the calling mode, tids is a list of torrents to take action upon
def torrent_actions_popup(mode,tids,details=False):
    popup = SelectablePopup(mode,"Torrent Actions",torrent_action,mode,tids)
    popup.add_line("_Pause",data=ACTION.PAUSE)
    popup.add_line("_Resume",data=ACTION.RESUME)
    popup.add_divider()
    popup.add_line("_Update Tracker",data=ACTION.REANNOUNCE)
    popup.add_divider()
    popup.add_line("Remo_ve Torrent",data=ACTION.REMOVE)
    popup.add_line("_Force Recheck",data=ACTION.RECHECK)
    if details:
        popup.add_divider()
        popup.add_line("Torrent _Details",data=ACTION.DETAILS)            
    mode.set_popup(popup)
