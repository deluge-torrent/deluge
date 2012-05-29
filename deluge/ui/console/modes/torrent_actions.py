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
from popup import SelectablePopup, Popup
from input_popup import InputPopup
import deluge.component as component

from deluge.ui.console import colors, modes
from twisted.internet import defer

import logging
log = logging.getLogger(__name__)

torrent_options = [
    ("max_download_speed", float),
    ("max_upload_speed", float),
    ("max_connections", int),
    ("max_upload_slots", int),
    ("prioritize_first_last", bool),
    ("sequential_download", bool),
    ("is_auto_managed", bool),
    ("stop_at_ratio", bool),
    ("stop_ratio", float),
    ("remove_at_ratio", bool),
    ("move_on_completed", bool),
    ("move_on_completed_path", str)
]

torrent_options_to_names = {
    "max_download_speed": "Max DL speed",
    "max_upload_speed": "Max UL speed",
    "max_connections": "Max connections",
    "max_upload_slots": "Max upload slots",
    "prioritize_first_last": "Prioritize first/last pieces",
    "sequential_download": "Sequential download",
    "is_auto_managed": "Is auto managed?",
    "stop_at_ratio": "Stop at ratio",
    "stop_ratio": "Seeding ratio limit",
    "remove_at_ratio": "Remove after reaching ratio",
    "move_on_completed": "Move torrent after completion",
    "move_on_completed_path": "Path to move the torrent to"
}

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
    MOVE_STORAGE=9
    QUEUE=10
    QUEUE_TOP=11
    QUEUE_UP=12
    QUEUE_DOWN=13
    QUEUE_BOTTOM=14
    TORRENT_OPTIONS=15

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
        elif data==ACTION.QUEUE:
            def do_queue(idx,qact,mode,ids):
                def move_selection(r):
                    if mode.config["move_selection"]:
                        queue_length = 0
                        selected_num = 0
                        for tid in mode.curstate:
                            tq = mode.curstate.get(tid)["queue"]
                            if tq != -1:
                                queue_length += 1
                                if tq in mode.marked:
                                    selected_num += 1
                        if qact == ACTION.QUEUE_TOP:
                            if mode.marked:
                                mode.cursel = 1 + sorted(mode.marked).index(mode.cursel)
                            else:
                                mode.cursel = 1
                            mode.marked = range(1, selected_num + 1)
                        elif qact == ACTION.QUEUE_UP:
                            mode.cursel = max(1, mode.cursel - 1)
                            mode.marked = map(lambda v: v-1, mode.marked)
                            mode.marked = filter(lambda v: v>0, mode.marked)
                        elif qact == ACTION.QUEUE_DOWN:
                            mode.cursel = min(queue_length, mode.cursel + 1)
                            mode.marked = map(lambda v: v+1, mode.marked)
                            mode.marked = filter(lambda v: v<=queue_length, mode.marked)
                        elif qact == ACTION.QUEUE_BOTTOM:
                            if mode.marked:
                                mode.cursel = queue_length - selected_num + 1 + sorted(mode.marked).index(mode.cursel)
                            else:
                                mode.cursel = queue_length
                            mode.marked = range(queue_length - selected_num + 1, queue_length+1)

                if qact == ACTION.QUEUE_TOP:
                    log.debug("Queuing torrents top")
                    client.core.queue_top(ids).addCallback(move_selection)
                elif qact == ACTION.QUEUE_UP:
                    log.debug("Queuing torrents up")
                    client.core.queue_up(ids).addCallback(move_selection)
                elif qact == ACTION.QUEUE_DOWN:
                    log.debug("Queuing torrents down")
                    client.core.queue_down(ids).addCallback(move_selection)
                elif qact == ACTION.QUEUE_BOTTOM:
                    log.debug("Queuing torrents bottom")
                    client.core.queue_bottom(ids).addCallback(move_selection)

                if len(ids) == 1:
                    mode.clear_marks()
                return True
            popup = SelectablePopup(mode,"Queue Action", do_queue, (mode, ids))
            popup.add_line("_Top",data=ACTION.QUEUE_TOP)
            popup.add_line("_Up",data=ACTION.QUEUE_UP)
            popup.add_line("_Down",data=ACTION.QUEUE_DOWN)
            popup.add_line("_Bottom",data=ACTION.QUEUE_BOTTOM)
            mode.set_popup(popup)
            return False
        elif data==ACTION.REMOVE:
            def do_remove(data):
                if not data: return
                mode.clear_marks()

                wd = data["remove_files"]
                for tid in ids:
                    log.debug("Removing torrent: %s, %d", tid, wd)
                    client.core.remove_torrent(tid,wd).addErrback(action_error,mode)

            rem_msg = ""


            def got_status(status):
                return (status["name"], status["state"])

            callbacks = []
            for tid in ids:
                d = client.core.get_torrent_status(tid, ["name", "state"])
                callbacks.append( d.addCallback(got_status) )


            def finish_up(status):
                status = map(lambda x: x[1], status)

                if len(ids) == 1:
                    rem_msg = "{!info!}Removing the following torrent:{!input!}"
                else:
                    rem_msg = "{!info!}Removing the following torrents:{!input!}"

                for i, (name, state) in enumerate(status):
                    color = colors.state_color[state]
                    rem_msg += "\n %s* {!input!}%s" % (color, name)
                    if i == 5:
                        if i < len(status):
                            rem_msg += "\n  {!red!}And %i more" % (len(status) - 5)
                        break

                popup = InputPopup(mode, "(Esc to cancel, Enter to remove)", close_cb=do_remove)
                popup.add_text(rem_msg)
                popup.add_spaces(1)
                popup.add_select_input("{!info!}Torrent files:", 'remove_files', ["Keep", "Remove"], [False, True], False)
                mode.set_popup(popup)
            defer.DeferredList(callbacks).addCallback(finish_up)
            return False
        elif data==ACTION.MOVE_STORAGE:
            def do_move(res):
                import os.path
                if os.path.exists(res["path"]) and not os.path.isdir(res["path"]):
                    mode.report_message("Cannot Move Storage","{!error!}%s exists and is not a directory"%res["path"])
                else:
                    log.debug("Moving %s to: %s",ids,res["path"])
                    client.core.move_storage(ids,res["path"]).addErrback(action_error,mode)
                if len(ids) == 1:
                    mode.clear_marks()
                return True
            popup = InputPopup(mode,"Move Storage (Esc to cancel)",close_cb=do_move)
            popup.add_text_input("Enter path to move to:","path")
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
        elif data==ACTION.TORRENT_OPTIONS:
            mode.popup = Popup(mode, "Torrent options")
            mode.popup.add_line("Querying core, please wait...")

            torrents = ids

            options = {}

            def _do_set_torrent_options(ids, result):
                options = {}
                for opt in result:
                    if result[opt] not in ["multiple", None]:
                        options[opt] = result[opt]
                client.core.set_torrent_options( ids, options )
                for tid in ids:
                    if "move_on_completed_path" in options:
                        client.core.set_torrent_move_completed_path(tid, options["move_on_completed_path"])
                    if "is_auto_managed" in options:
                        client.core.set_torrent_auto_managed(tid, options["is_auto_managed"])
                    if "remove_at_ratio" in options:
                        client.core.set_torrent_remove_at_ratio(tid, options["remove_at_ratio"])
                    if "prioritize_first_last" in options:
                        client.core.set_torrent_prioritize_first_last(tid, options["prioritize_first_last"])

            def on_torrent_status(status):
                for key in status:
                    if   key not in options:
                        options[key] = status[key]
                    elif options[key] != status[key]:
                        options[key] = "multiple"

            def create_popup(status):
                cb = lambda result, ids=ids: _do_set_torrent_options(ids, result)
                option_popup = InputPopup(mode,"Set torrent options (Esc to cancel)",close_cb=cb, height_req=22)

                for (field, field_type) in torrent_options:
                    caption = "{!info!}" + torrent_options_to_names[field]
                    value = options[field]
                    if   field_type == str:
                        option_popup.add_text_input(caption, field, str(value))
                    elif field_type == bool:
                        if options[field] == "multiple":
                            choices = (
                                ["Yes", "No", "Mixed"],
                                [True, False, None],
                                2
                            )
                        else:
                            choices = (
                                ["Yes", "No"],
                                [True, False],
                                [True, False].index(options[field])
                            )
                        option_popup.add_select_input(caption, field, choices[0], choices[1], choices[2])
                    elif field_type == float:
                        option_popup.add_float_spin_input(caption, field, value, min_val = -1)
                    elif field_type == int:
                        option_popup.add_int_spin_input(caption, field, value, min_val = -1)

                mode.set_popup(option_popup)
                mode.refresh()

            callbacks = []

            field_list = map(lambda t: t[0], torrent_options)

            for tid in torrents:
                deferred = component.get("SessionProxy").get_torrent_status(tid, field_list)
                callbacks.append( deferred.addCallback(on_torrent_status) )

            callbacks = defer.DeferredList(callbacks)
            callbacks.addCallback(create_popup)

    if len(ids) == 1:
        mode.clear_marks()
    return True

# Creates the popup.  mode is the calling mode, tids is a list of torrents to take action upon
def torrent_actions_popup(mode,tids,details=False, action = None):
    if action != None:
        torrent_action(-1, action, mode, tids)
        return
    popup = SelectablePopup(mode,"Torrent Actions",torrent_action, (mode, tids))
    popup.add_line("_Pause",data=ACTION.PAUSE)
    popup.add_line("_Resume",data=ACTION.RESUME)
    if not details:
        popup.add_divider()
        popup.add_line("Queue",data=ACTION.QUEUE)
    popup.add_divider()
    popup.add_line("_Update Tracker",data=ACTION.REANNOUNCE)
    popup.add_divider()
    popup.add_line("Remo_ve Torrent",data=ACTION.REMOVE)
    popup.add_line("_Force Recheck",data=ACTION.RECHECK)
    popup.add_line("_Move Storage",data=ACTION.MOVE_STORAGE)
    popup.add_divider()
    if details:
        popup.add_line("Torrent _Details",data=ACTION.DETAILS)
    popup.add_line("Torrent _Options",data=ACTION.TORRENT_OPTIONS)
    mode.set_popup(popup)
