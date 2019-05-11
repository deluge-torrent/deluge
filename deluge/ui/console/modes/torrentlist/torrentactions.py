# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging
import os

from twisted.internet import defer

import deluge.component as component
from deluge.ui.client import client
from deluge.ui.common import TORRENT_DATA_FIELD
from deluge.ui.console.modes.torrentlist.queue_mode import QueueMode
from deluge.ui.console.utils import colors
from deluge.ui.console.utils.common import TORRENT_OPTIONS
from deluge.ui.console.widgets.popup import InputPopup, MessagePopup, SelectablePopup

from . import ACTION

log = logging.getLogger(__name__)


def action_error(error, mode):
    mode.report_message('Error Occurred', error.getErrorMessage())
    mode.refresh()


def action_remove(mode=None, torrent_ids=None, **kwargs):
    def do_remove(*args, **kwargs):
        data = args[0] if args else None
        if data is None or kwargs.get('close', False):
            mode.pop_popup()
            return True

        mode.torrentview.clear_marked()
        remove_data = data['remove_files']['value']

        def on_removed_finished(errors):
            if errors:
                error_msgs = ''
                for t_id, e_msg in errors:
                    error_msgs += 'Error removing torrent %s : %s\n' % (t_id, e_msg)
                mode.report_message(
                    'Error(s) occured when trying to delete torrent(s).', error_msgs
                )
                mode.refresh()

        d = client.core.remove_torrents(torrent_ids, remove_data)
        d.addCallback(on_removed_finished)
        mode.pop_popup()

    def got_status(status):
        return (status['name'], status['state'])

    callbacks = []
    for tid in torrent_ids:
        d = client.core.get_torrent_status(tid, ['name', 'state'])
        callbacks.append(d.addCallback(got_status))

    def remove_dialog(status):
        status = [t_status[1] for t_status in status]

        if len(torrent_ids) == 1:
            rem_msg = '{!info!}Remove the following torrent?{!input!}'
        else:
            rem_msg = '{!info!}Remove the following %d torrents?{!input!}' % len(
                torrent_ids
            )

        show_max = 6
        for i, (name, state) in enumerate(status):
            color = colors.state_color[state]
            rem_msg += '\n %s* {!input!}%s' % (color, name)
            if i == show_max - 1:
                if i < len(status) - 1:
                    rem_msg += '\n  {!red!}And %i more' % (len(status) - show_max)
                break

        popup = InputPopup(
            mode,
            '(Esc to cancel, Enter to remove)',
            close_cb=do_remove,
            border_off_west=1,
            border_off_north=1,
        )
        popup.add_text(rem_msg)
        popup.add_spaces(1)
        popup.add_select_input(
            'remove_files',
            '{!info!}Torrent files:',
            ['Keep', 'Remove'],
            [False, True],
            False,
        )
        mode.push_popup(popup)

    defer.DeferredList(callbacks).addCallback(remove_dialog)


def action_torrent_info(mode=None, torrent_ids=None, **kwargs):
    popup = MessagePopup(mode, 'Torrent options', 'Querying core, please wait...')
    mode.push_popup(popup)
    torrents = torrent_ids
    options = {}

    def _do_set_torrent_options(torrent_ids, result):
        options = {}
        for opt, val in result.items():
            if val['value'] not in ['multiple', None]:
                options[opt] = val['value']
        client.core.set_torrent_options(torrent_ids, options)

    def on_torrent_status(status):
        for key in status:
            if key not in options:
                options[key] = status[key]
            elif options[key] != status[key]:
                options[key] = 'multiple'

    def create_popup(status):
        mode.pop_popup()

        def cb(result, **kwargs):
            if result is None:
                return
            _do_set_torrent_options(torrent_ids, result)
            if kwargs.get('close', False):
                mode.pop_popup()
                return True

        option_popup = InputPopup(
            mode,
            ' Set Torrent Options ',
            close_cb=cb,
            border_off_west=1,
            border_off_north=1,
            base_popup=kwargs.get('base_popup', None),
        )
        for field in TORRENT_OPTIONS:
            caption = '{!info!}' + TORRENT_DATA_FIELD[field]['name']
            value = options[field]
            if isinstance(value, ''.__class__):
                option_popup.add_text_input(field, caption, value)
            elif isinstance(value, bool):
                choices = (['Yes', 'No'], [True, False], [True, False].index(value))
                option_popup.add_select_input(
                    field, caption, choices[0], choices[1], choices[2]
                )
            elif isinstance(value, float):
                option_popup.add_float_spin_input(
                    field, caption, value=value, min_val=-1
                )
            elif isinstance(value, int):
                option_popup.add_int_spin_input(field, caption, value=value, min_val=-1)

        mode.push_popup(option_popup)

    callbacks = []
    for tid in torrents:
        deferred = component.get('SessionProxy').get_torrent_status(
            tid, list(TORRENT_OPTIONS)
        )
        callbacks.append(deferred.addCallback(on_torrent_status))

    callbacks = defer.DeferredList(callbacks)
    callbacks.addCallback(create_popup)


def torrent_action(action, *args, **kwargs):
    retval = False
    torrent_ids = kwargs.get('torrent_ids', None)
    mode = kwargs.get('mode', None)

    if torrent_ids is None:
        return

    if action == ACTION.PAUSE:
        log.debug('Pausing torrents: %s', torrent_ids)
        client.core.pause_torrents(torrent_ids).addErrback(action_error, mode)
        retval = True
    elif action == ACTION.RESUME:
        log.debug('Resuming torrents: %s', torrent_ids)
        client.core.resume_torrents(torrent_ids).addErrback(action_error, mode)
        retval = True
    elif action == ACTION.QUEUE:
        queue_mode = QueueMode(mode, torrent_ids)
        queue_mode.popup(**kwargs)
    elif action == ACTION.REMOVE:
        action_remove(**kwargs)
        retval = True
    elif action == ACTION.MOVE_STORAGE:

        def do_move(res, **kwargs):
            if res is None or kwargs.get('close', False):
                mode.pop_popup()
                return True

            if os.path.exists(res['path']['value']) and not os.path.isdir(
                res['path']['value']
            ):
                mode.report_message(
                    'Cannot Move Download Folder',
                    '{!error!}%s exists and is not a directory' % res['path']['value'],
                )
            else:
                log.debug('Moving %s to: %s', torrent_ids, res['path']['value'])
                client.core.move_storage(torrent_ids, res['path']['value']).addErrback(
                    action_error, mode
                )

        popup = InputPopup(
            mode, 'Move Download Folder', close_cb=do_move, border_off_east=1
        )
        popup.add_text_input('path', 'Enter path to move to:', complete=True)
        mode.push_popup(popup)
    elif action == ACTION.RECHECK:
        log.debug('Rechecking torrents: %s', torrent_ids)
        client.core.force_recheck(torrent_ids).addErrback(action_error, mode)
        retval = True
    elif action == ACTION.REANNOUNCE:
        log.debug('Reannouncing torrents: %s', torrent_ids)
        client.core.force_reannounce(torrent_ids).addErrback(action_error, mode)
        retval = True
    elif action == ACTION.DETAILS:
        log.debug('Torrent details')
        tid = mode.torrentview.current_torrent_id()
        if tid:
            mode.show_torrent_details(tid)
        else:
            log.error('No current torrent in _torrentaction, this is a bug')
    elif action == ACTION.TORRENT_OPTIONS:
        action_torrent_info(**kwargs)

    return retval


# Creates the popup.  mode is the calling mode, tids is a list of torrents to take action upon
def torrent_actions_popup(mode, torrent_ids, details=False, action=None, close_cb=None):

    if action is not None:
        torrent_action(action, mode=mode, torrent_ids=torrent_ids)
        return

    popup = SelectablePopup(
        mode,
        'Torrent Actions',
        torrent_action,
        cb_args={'mode': mode, 'torrent_ids': torrent_ids},
        close_cb=close_cb,
        border_off_north=1,
        border_off_west=1,
        border_off_east=1,
    )
    popup.add_line(ACTION.PAUSE, '_Pause')
    popup.add_line(ACTION.RESUME, '_Resume')
    if details:
        popup.add_divider()
        popup.add_line(ACTION.QUEUE, 'Queue')
    popup.add_divider()
    popup.add_line(ACTION.REANNOUNCE, '_Update Tracker')
    popup.add_divider()
    popup.add_line(ACTION.REMOVE, 'Remo_ve Torrent')
    popup.add_line(ACTION.RECHECK, '_Force Recheck')
    popup.add_line(ACTION.MOVE_STORAGE, '_Move Download Folder')
    popup.add_divider()
    if details:
        popup.add_line(ACTION.DETAILS, 'Torrent _Details')
    popup.add_line(ACTION.TORRENT_OPTIONS, 'Torrent _Options')
    mode.push_popup(popup)
