# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2011 Nick Lanham <nick@afternight.org>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import glob
import logging
import os
from base64 import b64encode

from six import unichr as chr  # noqa: A001 shadowing

import deluge.common
from deluge.ui.client import client
from deluge.ui.common import TorrentInfo

log = logging.getLogger(__name__)


def _bracket_fixup(path):
    if path.find('[') == -1 and path.find(']') == -1:
        return path
    sentinal = 256
    while path.find(chr(sentinal)) != -1:
        sentinal += 1
        if sentinal > 65535:
            log.error(
                'Cannot fix brackets in path, path contains all possible sentinal characters'
            )
            return path
    newpath = path.replace(']', chr(sentinal))
    newpath = newpath.replace('[', '[[]')
    newpath = newpath.replace(chr(sentinal), '[]]')
    return newpath


def add_torrent(t_file, options, success_cb, fail_cb, ress):
    t_options = {}
    if options['path']:
        t_options['download_location'] = os.path.expanduser(options['path'])
    t_options['add_paused'] = options['add_paused']

    is_url = (options['path_type'] != 1) and (
        deluge.common.is_url(t_file) or options['path_type'] == 2
    )
    is_magnet = (
        not (is_url) and (options['path_type'] != 1) and deluge.common.is_magnet(t_file)
    )

    if is_url or is_magnet:
        files = [t_file]
    else:
        files = glob.glob(_bracket_fixup(t_file))
    num_files = len(files)
    ress['total'] = num_files

    if num_files <= 0:
        fail_cb('Does not exist', t_file, ress)

    for f in files:
        if is_url:
            client.core.add_torrent_url(f, t_options).addCallback(
                success_cb, f, ress
            ).addErrback(fail_cb, f, ress)
        elif is_magnet:
            client.core.add_torrent_magnet(f, t_options).addCallback(
                success_cb, f, ress
            ).addErrback(fail_cb, f, ress)
        else:
            if not os.path.exists(f):
                fail_cb('Does not exist', f, ress)
                continue
            if not os.path.isfile(f):
                fail_cb('Is a directory', f, ress)
                continue

            try:
                TorrentInfo(f)
            except Exception as ex:
                fail_cb(ex.message, f, ress)
                continue

            filename = os.path.split(f)[-1]
            with open(f, 'rb') as _file:
                filedump = b64encode(_file.read())

            client.core.add_torrent_file_async(
                filename, filedump, t_options
            ).addCallback(success_cb, f, ress).addErrback(fail_cb, f, ress)
