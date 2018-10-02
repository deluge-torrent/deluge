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

import deluge.common
from deluge.ui.client import client
from deluge.ui.console.widgets.popup import InputPopup, SelectablePopup

log = logging.getLogger(__name__)


def report_add_status(torrentlist, succ_cnt, fail_cnt, fail_msgs):
    if fail_cnt == 0:
        torrentlist.report_message(
            'Torrents Added', '{!success!}Successfully added %d torrent(s)' % succ_cnt
        )
    else:
        msg = (
            '{!error!}Failed to add the following %d torrent(s):\n {!input!}' % fail_cnt
        ) + '\n '.join(fail_msgs)
        if succ_cnt != 0:
            msg += '\n \n{!success!}Successfully added %d torrent(s)' % succ_cnt
        torrentlist.report_message('Torrent Add Report', msg)


def show_torrent_add_popup(torrentlist):
    def do_add_from_url(data=None, **kwargs):
        torrentlist.pop_popup()
        if not data or kwargs.get('close', False):
            return

        def fail_cb(msg, url):
            log.debug('failed to add torrent: %s: %s', url, msg)
            error_msg = '{!input!} * %s: {!error!}%s' % (url, msg)
            report_add_status(torrentlist, 0, 1, [error_msg])

        def success_cb(tid, url):
            if tid:
                log.debug('added torrent: %s (%s)', url, tid)
                report_add_status(torrentlist, 1, 0, [])
            else:
                fail_cb('Already in session (probably)', url)

        url = data['url']['value']
        if not url:
            return

        t_options = {
            'download_location': data['path']['value'],
            'add_paused': data['add_paused']['value'],
        }

        if deluge.common.is_magnet(url):
            client.core.add_torrent_magnet(url, t_options).addCallback(
                success_cb, url
            ).addErrback(fail_cb, url)
        elif deluge.common.is_url(url):
            client.core.add_torrent_url(url, t_options).addCallback(
                success_cb, url
            ).addErrback(fail_cb, url)
        else:
            torrentlist.report_message(
                'Error', '{!error!}Invalid URL or magnet link: %s' % url
            )
            return

        log.debug(
            'Adding Torrent(s): %s (dl path: %s) (paused: %d)',
            url,
            data['path']['value'],
            data['add_paused']['value'],
        )

    def show_add_url_popup():
        add_paused = 1 if 'add_paused' in torrentlist.coreconfig else 0
        popup = InputPopup(
            torrentlist, 'Add Torrent (Esc to cancel)', close_cb=do_add_from_url
        )
        popup.add_text_input('url', 'Enter torrent URL or Magnet link:')
        popup.add_text_input(
            'path',
            'Enter save path:',
            torrentlist.coreconfig.get('download_location', ''),
            complete=True,
        )
        popup.add_select_input(
            'add_paused', 'Add Paused:', ['Yes', 'No'], [True, False], add_paused
        )
        torrentlist.push_popup(popup)

    def option_chosen(selected, *args, **kwargs):
        if not selected or selected == 'cancel':
            torrentlist.pop_popup()
            return
        if selected == 'file':
            torrentlist.consoleui.set_mode('AddTorrents')
        elif selected == 'url':
            show_add_url_popup()

    popup = SelectablePopup(torrentlist, 'Add torrent', option_chosen)
    popup.add_line('file', '- From _File(s)', use_underline=True)
    popup.add_line('url', '- From _URL or Magnet', use_underline=True)
    popup.add_line('cancel', '- _Cancel', use_underline=True)
    torrentlist.push_popup(popup, clear=True)
