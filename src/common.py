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

import os
import xdg.BaseDirectory

PROGRAM_NAME = "Deluge"
PROGRAM_VERSION = "0.5.6"

CLIENT_CODE = "DE"
CLIENT_VERSION = "".join(PROGRAM_VERSION.split('.'))+"0"*(4 - len(PROGRAM_VERSION.split('.')))

def windows_check():
    import platform
    if platform.system() in ('Windows', 'Microsoft'):
        return True
    else:
        return False

import sys 
if hasattr(sys, "frozen"):
    INSTALL_PREFIX = ''
    os.chdir(os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding( ))))
    sys.stdout = open("deluge.stdout.log", "w")
    sys.stderr = open("deluge.stderr.log", "w")
else:
    # the necessary substitutions are made at installation time
    INSTALL_PREFIX = '@datadir@'
    
if windows_check(): 
    if os.path.isdir(os.path.expanduser("~")):
        CONFIG_DIR = os.path.join(os.path.expanduser("~"), 'deluge')
    else:
        CONFIG_DIR = os.path.join(INSTALL_PREFIX, 'deluge')
    if not os.path.exists(CONFIG_DIR):
        os.mkdir(CONFIG_DIR)
else:
    CONFIG_DIR = xdg.BaseDirectory.save_config_path('deluge')

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

def get_logo(size):
    import gtk
    if windows_check(): 
        return gtk.gdk.pixbuf_new_from_file_at_size(get_pixmap("deluge.png"), \
            size, size)
    else:
        return gtk.gdk.pixbuf_new_from_file_at_size(get_pixmap("deluge.svg"), \
            size, size)
    
def open_url_in_browser(link):
    import threading
    import webbrowser
    class BrowserThread(threading.Thread):
       def __init__(self, link):
           threading.Thread.__init__(self)
           self.url = link
       def run(self):
           webbrowser.open(self.url)
    BrowserThread(link).start()

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
    try:
        Popen(command)
    except OSError:
        import gtk
         
        warning = gtk.MessageDialog(parent = None, 
                      flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, 
                      buttons= gtk.BUTTONS_OK, 
                      message_format='%s %s %s' % (_("External command"),
                                                   executable, _("not found")), 
                      type = gtk.MESSAGE_WARNING) 
        warning.run()
        warning.destroy()

def send_info():
    import urllib
    import platform
    import gtk
    import os
    import common

    pygtk = '%i.%i.%i' %(gtk.pygtk_version[0],gtk.pygtk_version[1],gtk.pygtk_version[2])

    urllib.urlopen("http://download.deluge-torrent.org/stats.php?processor=" + \
        platform.machine() + "&python=" + platform.python_version() \
        + "&os=" + platform.system() + "&pygtk=" + pygtk)

    f = open(os.path.join(CONFIG_DIR, 'infosent'), 'w')
    f.write("")
    f.close

def new_release_check():
    import urllib
    try:
        new_release = urllib.urlopen("http://download.deluge-torrent.org/\
version").read().strip()
    except IOError:
        print "Network error while trying to check for a newer version of \
Deluge"
        new_release = ""

    if new_release >  PROGRAM_VERSION:
        import gtk
        import dialogs
        gtk.gdk.threads_enter()
        result = dialogs.show_popup_question(None, _("There is a newer version \
of Deluge.  Would you like to be taken to our download site?"))
        gtk.gdk.threads_leave()
        if result:
            open_url_in_browser('http://download.deluge-torrent.org/')
        else:
            pass

# Encryption States
class EncState:
    forced, enabled, disabled = range(3)
    
class EncLevel:
    plaintext, rc4, both = range(3)

class ProxyType:
    none, socks4, socks5, socks5_pw, http, http_pw = range(6)
    
class FileManager:
    xdg, konqueror, nautilus, thunar = range(4)
