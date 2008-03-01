#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Martijn Voncken 2007 <mvoncken@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, write to:
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
#
#  In addition, as a special exception, the copyright holders give
#  permission to link the code of portions of this program with the OpenSSL
#  library.
#  You must obey the GNU General Public License in all respects for all of
#  the code used other than OpenSSL. If you modify file(s) with this
#  exception, you may extend this exception to your version of the file(s),
#  but you are not obligated to do so. If you do not wish to do so, delete
#  this exception statement from your version. If you delete this exception
#  statement from all source files in the program, then also delete it here.

"""
initializes config,render and proxy.
All hacks go here, so this is a really ugly source-file..
Support running in process0.5 ,run inside-gtk0.5 and run in process0.6
"""

import os
import deluge
import random
import pickle
import sys
import base64
from md5 import md5
import inspect

from deluge.log import LOG as log

from deluge.ui.client import sclient as proxy
from deluge.ui.client import aclient as async_proxy

random.seed()

try:
    _('translate something')
except:
    import gettext
    gettext.install('~/')
    log.error('no translations :(')


#constants
try:
    REVNO = open(os.path.join(os.path.dirname(__file__),'revno')).read()
except:
    REVNO = '<unknown:bzr-branch?>'
try:
    VERSION = open(os.path.join(os.path.dirname(__file__),'version')).read()
except:
    VERSION = '<unknown:bzr-branch?>'


TORRENT_KEYS = ['name', 'total_size', 'num_files', 'num_pieces', 'piece_length',
    'eta', 'ratio', 'file_progress', 'distributed_copies', 'total_done',
    'total_uploaded', 'state', 'paused', 'progress', 'next_announce',
    'total_payload_download', 'total_payload_upload', 'download_payload_rate',
    'upload_payload_rate', 'num_peers', 'num_seeds', 'total_peers', 'total_seeds',
    'total_wanted', 'tracker', 'trackers', 'tracker_status', 'save_path',
    'files', 'file_priorities', 'compact', 'max_connections',
    'max_upload_slots', 'max_download_speed', 'prioritize_first_last',
    'private','max_upload_speed','queue',

    #REMOVE:
    "is_seed","total_download","total_upload","uploaded_memory",
    "user_paused"

    ]

STATE_MESSAGES = [
    "Allocating",
    "Checking",
    "Downloading",
    "Seeding",
    "Paused",
    "Error"
    ]


CONFIG_DEFAULTS = {
    "port":8112,
    "button_style":2,
    "auto_refresh":False,
    "auto_refresh_secs": 10,
    "template":"advanced",
    "pwd_salt":"2\xe8\xc7\xa6(n\x81_\x8f\xfc\xdf\x8b\xd1\x1e\xd5\x90",
    "pwd_md5":".\xe8w\\+\xec\xdb\xf2id4F\xdb\rUc",
    "cache_templates":False,
    "use_https":False
}

#/constants


class Ws:
    """
    singleton
    important attributes here are environment dependent.

    Most important public attrs:
    ws.proxy
    ws.log
    ws.config

    Other:
    ws.env
    ws.config_dir
    ws.session_file
    ws.SESSIONS
    """
    def __init__(self):
        self.webui_path = os.path.dirname(__file__)
        self.env = 'UNKNOWN'
        self.config = {}

        try:
            self.config_dir = deluge.common.CONFIG_DIR
        except:
            self.config_dir = os.path.expanduser("~/.config/deluge")

        self.config_file = os.path.join(self.config_dir,'webui.conf')
        self.session_file = os.path.join(self.config_dir,'webui.sessions')
        self.SESSIONS = []

    def init_process(self):
        self.config = pickle.load(open(self.config_file))

    def init_06(self, uri = 'http://localhost:58846'):
        proxy.set_core_uri(uri)

        log.debug('cfg-file %s' % self.config_file)

        if not os.path.exists(self.config_file):
            log.debug('create cfg file %s' % self.config_file)
            #load&save defaults.
            f = file(self.config_file,'wb')
            pickle.dump(CONFIG_DEFAULTS,f)
            f.close()

        self.init_process()
        self.env   = '0.6'

    #utils for config:
    def get_templates(self):
        template_path = os.path.join(os.path.dirname(__file__), 'templates')
        return [dirname for dirname
            in os.listdir(template_path)
            if os.path.isdir(os.path.join(template_path, dirname))
                and not dirname.startswith('.')]

    def save_config(self):
        log.debug('Save Webui Config')
        data = pickle.dumps(self.config)
        f = open(self.config_file,'wb')
        f.write(data)
        f.close()

    def update_pwd(self,pwd):
        sm = md5()
        sm.update(str(random.getrandbits(5000)))
        salt = sm.digest()
        self.config["pwd_salt"] =  salt
        #
        m = md5()
        m.update(salt)
        m.update(pwd)
        self.config["pwd_md5"] =  m.digest()

    def check_pwd(self,pwd):
        m = md5()
        m.update(self.config.get('pwd_salt'))
        m.update(pwd)
        return (m.digest() == self.config.get('pwd_md5'))

ws =Ws()
