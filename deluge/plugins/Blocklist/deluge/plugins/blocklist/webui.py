# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging

from deluge.plugins.pluginbase import WebPluginBase

from .common import get_resource

log = logging.getLogger(__name__)

FORMAT_LIST = [
    ('gzmule', _('Emule IP list (GZip)')),
    ('spzip', _('SafePeer Text (Zipped)')),
    ('pgtext', _('PeerGuardian Text (Uncompressed)')),
    ('p2bgz', _('PeerGuardian P2B (GZip)')),
]


class WebUI(WebPluginBase):

    scripts = [get_resource('blocklist.js')]
    debug_scripts = scripts
