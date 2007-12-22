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
from lib.webpy022 import template

random.seed()
webui_path = os.path.dirname(__file__)
ENV = 'UNKNOWN'
config_defaults = {
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

try:
    _('translate something')
except:
    import gettext
    gettext.install('~/')
    #log.error('no translations :(')

try:
    config_dir = deluge.common.CONFIG_DIR
except:
    config_dir = os.path.expanduser("~/.config/deluge")

config_file = os.path.join(config_dir,'webui.conf')
session_file = os.path.join(config_dir,'webui.sessions')


class subclassed_render(object):
    """
    try to use the html template in configured dir.
    not available : use template in /deluge/
    """
    def __init__(self, template_dirname, cache=False):
        self.base_template = template.render(
            os.path.join(webui_path, 'templates/deluge/'),
            cache=cache)

        self.sub_template = template.render(
            os.path.join(webui_path, 'templates/%s/' % template_dirname),
            cache=cache)

    def __getattr__(self, attr):
        if hasattr(self.sub_template, attr):
            return getattr(self.sub_template, attr)
        else:
            return getattr(self.base_template, attr)

def init_process():
    globals()['config'] = pickle.load(open(config_file))
    globals()['render'] = subclassed_render(config.get('template'),
        config.get('cache_templates'))

def init_06():
    import deluge.ui.client as proxy
    from deluge.log import LOG as log
    globals()['log']    = log

    proxy.set_core_uri('http://localhost:58846') #How to configure this?

    def add_torrent_filecontent(name , data_b64):
        log.debug('monkeypatched add_torrent_filecontent:%s,len(data:%s))' %
            (name , len(data_b64)))

        name =  name.replace('\\','/')
        name = 'deluge06_' + str(random.random()) + '_'  + name.split('/')[-1]
        filename = os.path.join('/tmp', name)

        log.debug('write: %s' % filename)
        f = open(filename,"wb")
        f.write(base64.b64decode(data_b64))
        f.close()

        proxy.add_torrent_file([filename])




    proxy.add_torrent_filecontent = add_torrent_filecontent
    log.debug('cfg-file %s' % config_file)
    if not os.path.exists(config_file):
        log.debug('create cfg file %s' % config_file)
        #load&save defaults.
        f = file(config_file,'wb')
        pickle.dump(config_defaults,f)
        f.close()

    init_process()
    globals()['proxy'] = proxy
    globals()['ENV']    = '0.6'



def init_05():
    import dbus
    init_process()
    bus = dbus.SessionBus()
    proxy = bus.get_object("org.deluge_torrent.dbusplugin"
        , "/org/deluge_torrent/DelugeDbusPlugin")

    globals()['proxy'] = proxy
    globals()['ENV']    = '0.5_process'
    init_logger()

def init_gtk_05():
    #appy possibly changed config-vars, only called in when runing inside gtk.
    from dbus_interface import get_dbus_manager
    globals()['proxy'] =  get_dbus_manager()
    globals()['config']  = deluge.pref.Preferences(config_file, False)
    globals()['render'] = subclassed_render(config.get('template'),
        config.get('cache_templates'))
    globals()['ENV']    = '0.5_gtk'
    init_logger()

def init_logger():
    #only for 0.5..
    import logging
    logging.basicConfig(level=logging.DEBUG,
        format="[%(levelname)s] %(message)s")
    globals()['log'] = logging


#hacks to determine environment, TODO: clean up.
if 'env=0.5' in sys.argv:
    init_05()
elif 'env=0.6' in sys.argv:
    init_06()
elif hasattr(deluge, 'ui'):
    init_06()
elif not hasattr(deluge,'pref'):
    init_05()


#constants
REVNO = open(os.path.join(os.path.dirname(__file__),'revno')).read()
VERSION = open(os.path.join(os.path.dirname(__file__),'version')).read()

TORRENT_KEYS = ['distributed_copies', 'download_payload_rate',
    'download_rate', 'eta', 'is_seed', 'name', 'next_announce',
    'num_files', 'num_peers', 'num_pieces', 'num_seeds', 'paused',
    'piece_length','progress', 'ratio', 'total_done', 'total_download',
    'total_payload_download', 'total_payload_upload', 'total_peers',
    'total_seeds', 'total_size', 'total_upload', 'total_wanted',
    'tracker_status', 'upload_payload_rate', 'upload_rate',
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

#try:
#    SESSIONS = pickle.load(open(session_file))
#except:
SESSIONS = []





