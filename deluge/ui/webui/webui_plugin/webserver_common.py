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

random.seed()

try:
    _('translate something')
except:
    import gettext
    gettext.install('~/')
    #log.error('no translations :(')


#constants
try:
    REVNO = open(os.path.join(os.path.dirname(__file__),'revno')).read()
except:
    REVNO = '<unknown:bzr-branch?>'
try:
    VERSION = open(os.path.join(os.path.dirname(__file__),'version')).read()
except:
    VERSION = '<unknown:bzr-branch?>'

TORRENT_KEYS = ['distributed_copies', 'download_payload_rate',
    'eta', 'is_seed', 'name', 'next_announce',
    'num_files', 'num_peers', 'num_pieces', 'num_seeds', 'paused',
    'piece_length','progress', 'ratio', 'total_done', 'total_download',
    'total_payload_download', 'total_payload_upload', 'total_peers',
    'total_seeds', 'total_size', 'total_upload', 'total_wanted',
    'tracker_status', 'upload_payload_rate',
    'uploaded_memory','tracker','state','queue_pos','user_paused']

STATE_MESSAGES = (_("Queued"),
    _("Checking"),
    _("Connecting"),
    _("Downloading Metadata"),
    _("Downloading"),
    _("Finished"),
    _("Seeding"),
    _("Allocating"))

SPEED_VALUES = [
        (-1, 'Unlimited'),
        (5, '5.0 Kib/sec'),
        (10, '10.0 Kib/sec'),
        (15, '15.0 Kib/sec'),
        (25, '25.0 Kib/sec'),
        (30, '30.0 Kib/sec'),
        (50, '50.0 Kib/sec'),
        (80, '80.0 Kib/sec'),
        (300, '300.0 Kib/sec'),
        (500, '500.0 Kib/sec')
    ]
CONFIG_DEFAULTS = {
    "port":8112,
    "button_style":2,
    "auto_refresh":False,
    "auto_refresh_secs": 10,
    "template":"advanced",
    "pwd_salt":"2540626806573060601127357001536142078273646936492343724296134859793541603059837926595027859394922651189016967573954758097008242073480355104215558310954",
    "pwd_md5":"\xea\x8d\x90\x98^\x9f\xa9\xe2\x19l\x7f\x1a\xca\x82u%",
    "cache_templates":False,
    "use_https":False
}

#/constants


class SyncProxyFunction:
    """
    helper class for SyncProxy
    """
    def __init__(self,client, func_name):
        self.func_name = func_name
        self.client = client

    def __call__(self,*args,**kwargs):
        sync_result = []
        func = getattr(self.client,self.func_name)

        if self.has_callback(func):
            func(sync_result.append,*args, **kwargs)
            self.client.force_call(block=True)
            return sync_result[0]
        else:
            ws.log.debug('no-cb: %s' % self.func_name)
            func(*args, **kwargs)
            self.client.force_call(block=True)
            return

    @staticmethod
    def has_callback(func):
        return  "callback" in inspect.getargspec(func)[0]

class SyncProxy(object):
    """acts like the old synchonous proxy"""
    def __init__(self, client):
        self.client = client

    def __getattr__(self, attr,*args,**kwargs):
        return SyncProxyFunction(self.client, attr)


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
        import deluge.ui.client as async_proxy
        from deluge.log import LOG as log
        self.log = log
        async_proxy.set_core_uri(uri)
        self.async_proxy = async_proxy

        self.proxy = SyncProxy(self.async_proxy)



        #MONKEY PATCH, TODO->REMOVE!!!
        def add_torrent_filecontent(name , data_b64):
            self.log.debug('monkeypatched add_torrent_filecontent:%s,len(data:%s))' %
                (name , len(data_b64)))

            name =  name.replace('\\','/')
            name = 'deluge06_' + str(random.random()) + '_'  + name.split('/')[-1]
            filename = os.path.join('/tmp', name)

            self.log.debug('write: %s' % filename)
            f = open(filename,"wb")
            f.write(base64.b64decode(data_b64))
            f.close()

            self.proxy.add_torrent_file([filename])

        self.proxy.add_torrent_filecontent = add_torrent_filecontent
        self.log.debug('cfg-file %s' % self.config_file)

        if not os.path.exists(self.config_file):
            self.log.debug('create cfg file %s' % self.config_file)
            #load&save defaults.
            f = file(self.config_file,'wb')
            pickle.dump(CONFIG_DEFAULTS,f)
            f.close()

        self.init_process()
        self.env   = '0.6'

    def init_05(self):
        import dbus
        self.init_process()
        bus = dbus.SessionBus()
        self.proxy = bus.get_object("org.deluge_torrent.dbusplugin"
            , "/org/deluge_torrent/DelugeDbusPlugin")

        self.env = '0.5_process'
        self.init_logger()

    def init_gtk_05(self):
        #appy possibly changed config-vars, only called in when runing inside gtk.
        #new bug ws.render will not update!!!!
        #other bug: must warn if blocklist plugin is active!
        from dbus_interface import get_dbus_manager
        self.proxy =  get_dbus_manager()
        self.config  = deluge.pref.Preferences(self.config_file, False)
        self.env = '0.5_gtk'
        self.init_logger()

    def init_logger(self):
        #only for 0.5..
        import logging
        logging.basicConfig(level=logging.DEBUG,
            format="[%(levelname)s] %(message)s")
        self.log = logging


    #utils for config:
    def get_templates(self):
        template_path = os.path.join(os.path.dirname(__file__), 'templates')
        return [dirname for dirname
            in os.listdir(template_path)
            if os.path.isdir(os.path.join(template_path, dirname))
                and not dirname.startswith('.')]

    def save_config(self):
        self.log.debug('Save Webui Config')
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



