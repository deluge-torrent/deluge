#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Zach Tibbitts 2006 <zach@collegegeek.org>
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

import os.path
import xdg.BaseDirectory

PROGRAM_NAME = "Deluge"
PROGRAM_VERSION = "0.5.4"

CLIENT_CODE = "DE"
CLIENT_VERSION = "".join(PROGRAM_VERSION.split('.'))+"0"*(4 - len(PROGRAM_VERSION.split('.'))) 
CONFIG_DIR = xdg.BaseDirectory.save_config_path('deluge')

# the necessary substitutions are made at installation time
INSTALL_PREFIX = '@datadir@'
GLADE_DIR  = os.path.join(INSTALL_PREFIX, 'share', 'deluge', 'glade')
PIXMAP_DIR = os.path.join(INSTALL_PREFIX, 'share', 'deluge', 'pixmaps')
PLUGIN_DIR = os.path.join(INSTALL_PREFIX, 'share', 'deluge', 'plugins')

def estimate_eta(state):
    try:
        return ftime(get_eta(state["total_wanted"], state["total_done"], 
                             state["download_rate"]))
    except ZeroDivisionError:
        return _("Infinity")
    
def get_eta(size, done, speed):
    # raise ZeroDivisionError for Infinity in estimate_eta()
    if (size - done) == 0:
        raise ZeroDivisionError
    return (size - done) / speed

# Returns formatted string describing filesize
# fsize_b should be in bytes
# Returned value will be in either KB, MB, or GB
def fsize(fsize_b):
    fsize_kb = float (fsize_b / 1024.0)
    if fsize_kb < 1000:
        return "%.1f %s" % (fsize_kb, _("KiB"))
    fsize_mb = float (fsize_kb / 1024.0)
    if fsize_mb < 1000:
        return "%.1f %s" % (fsize_mb, _("MiB"))
    fsize_gb = float (fsize_mb / 1024.0)
    if fsize_gb < 1000:
        return "%.1f %s" % (fsize_gb, _("GiB"))
    fsize_tb = float (fsize_gb / 1024.0)
    if fsize_tb < 1000:
        return "%.1f %s" % (fsize_tb, _("TiB"))
    fsize_pb = float (fsize_tb / 1024.0)
    return "%.1f %s" % (fsize_pb, _("PiB"))

# Returns a formatted string representing a percentage
def fpcnt(dec):
    return '%.2f%%'%(dec * 100)

# Returns a formatted string representing transfer speed
def fspeed(bps):
    return '%s/s'%(fsize(bps))

def fseed(state):
    return str(str(state['num_seeds']) + " (" + str(state['total_seeds']) + ")")
    
def fpeer(state):
    return str(str(state['num_peers']) + " (" + str(state['total_peers']) + ")")
    
def ftime(seconds):
    if seconds < 60:
        return '%ds'%(seconds)
    minutes = int(seconds/60)
    seconds = seconds % 60
    if minutes < 60:
        return '%dm %ds'%(minutes, seconds)
    hours = int(minutes/60)
    minutes = minutes % 60
    if hours < 24:
        return '%dh %dm'%(hours, minutes)
    days = int(hours/24)
    hours = hours % 24
    if days < 7:
        return '%dd %dh'%(days, hours)
    weeks = int(days/7)
    days = days % 7
    if weeks < 10:
        return '%dw %dd'%(weeks, days)
    return 'unknown'

def fpriority(priority):
    from core import PRIORITY_DICT
    
    return PRIORITY_DICT[priority]

def get_glade_file(fname):
    return os.path.join(GLADE_DIR, fname)

def get_pixmap(fname):
    return os.path.join(PIXMAP_DIR, fname)
    
def open_url_in_browser(link):
    import platform
    if platform.system() == "Windows":
        import webbrowser
        webbrowser.open(link)
    else:
        exec_deluge_command('browser.py', link)

def is_url(url):
    import re
    
    return bool(re.search('^(https?|ftp)://', url))

def fetch_url(url):
    import urllib

    try:
        filename, headers = urllib.urlretrieve(url)
    except IOError:
        print 'Network error while trying to fetch torrent from %s' % url
    else:
        if filename.endswith(".torrent") or \
           headers["content-type"]=="application/x-bittorrent":
            return filename
        else:
            print "URL doesn't appear to be a valid torrent file:", url
            
    return None

def exec_command(executable, *parameters):
    from subprocess import Popen

    command = [executable]
    command.extend(parameters)    
    Popen(command)

def exec_deluge_command(script, *parameters):
    """Execute deluge's command like browser.py, update.py and others"""
    
    import sys
    
    py_version = sys.version[:3]
    full_path = os.path.join(INSTALL_PREFIX, 'lib', 'python' + py_version, 
                             'site-packages', 'deluge', script)
    exec_command('python', full_path, *parameters)

# Encryption States
class EncState:
    forced, enabled, disabled = range(3)
    
class EncLevel:
    plaintext, rc4, both = range(3)

class ProxyType:
    none, socks4, socks5, socks5_pw, http, http_pw = range(6)
class FileManager:
    choose_one, konqueror, nautilus, thunar = range(4)
