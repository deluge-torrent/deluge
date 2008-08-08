#
# common.py
#
# Copyright (C) 2007, 2008 Andrew Resch ('andar') <andrewresch@gmail.com>
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
# 	Boston, MA    02110-1301, USA.
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

"""Common functions for various parts of Deluge to use."""

import os
import subprocess

import pkg_resources
import xdg, xdg.BaseDirectory

LT_TORRENT_STATE = {
    "Queued": 0,
    "Checking": 1,
    "Connecting": 2,
    "Downloading Metadata": 3,
    "Downloading": 4,
    "Finished": 5,
    "Seeding": 6,
    "Allocating": 7,
    "Paused": 8,
    0: "Queued",
    1: "Checking",
    2: "Connecting",
    3: "Downloading Metadata",
    4: "Downloading",
    5: "Finished",
    6: "Seeding",
    7: "Allocating",
    8: "Paused"
}

TORRENT_STATE = [
    "Allocating",
    "Checking",
    "Downloading",
    "Seeding",
    "Paused",
    "Error",
    "Queued"
]

FILE_PRIORITY = {
    0: "Do Not Download",
    1: "Normal Priority",
    2: "High Priority",
    5: "Highest Priority",
    "Do Not Download": 0,
    "Normal Priority": 1,
    "High Priority": 2,
    "Highest Priority": 5
}

def get_version():
    """Returns the program version from the egg metadata"""
    return pkg_resources.require("Deluge")[0].version.split("r")[0]

def get_revision():
    revision = ""
    try:
        f = open(pkg_resources.resource_filename("deluge", os.path.join("data", "revision")))
        revision = f.read()
        f.close()
    except IOError, e:
        pass
        
    return revision
    
def get_default_config_dir(filename=None):
    """ Returns the config path if no filename is specified
    Returns the config directory + filename as a path if filename is specified
    """
    if windows_check():
        if filename:
            return os.path.join(os.environ.get("APPDATA"), "deluge", filename)
        else:
            return os.path.join(os.environ.get("APPDATA"), "deluge")
    else:
        if filename:
            return os.path.join(xdg.BaseDirectory.save_config_path("deluge"), filename)
        else:
            return xdg.BaseDirectory.save_config_path("deluge")

def get_default_download_dir():
    """Returns the default download directory"""
    if windows_check():
        return os.path.expanduser("~")
    else:
        return os.environ.get("HOME")

def windows_check():
    """Checks if the current platform is Windows.  Returns True if it is Windows
        and False if not."""
    import platform
    if platform.system() in ('Windows', 'Microsoft'):
        return True
    else:
        return False

def get_pixmap(fname):
    """Returns a pixmap file included with deluge"""
    return pkg_resources.resource_filename("deluge", os.path.join("data", \
                                           "pixmaps", fname))

def get_logo(size):
    """Returns a deluge logo pixbuf based on the size parameter."""
    import gtk
    if windows_check(): 
        return gtk.gdk.pixbuf_new_from_file_at_size(get_pixmap("deluge.png"), \
            size, size)
    else:
        return gtk.gdk.pixbuf_new_from_file_at_size(get_pixmap("deluge.svg"), \
            size, size)

def open_file(path):
    """Opens a file or folder."""
    if windows_check():
        os.startfile("'%s'" % path)
    else:
        subprocess.Popen(["xdg-open", "%s" % path])

def open_url_in_browser(url):
    """Opens link in the desktop's default browser"""
    def start_browser():
        import threading
        import webbrowser
        class BrowserThread(threading.Thread):
            def __init__(self, url):
                threading.Thread.__init__(self)
                self.url = url
            def run(self):
                webbrowser.open(self.url)
        BrowserThread(url).start()
        return False
        
    import gobject
    gobject.idle_add(start_browser)


def build_menu_radio_list(value_list, callback, pref_value=None, 
    suffix=None, show_notset=False, notset_label=None, notset_lessthan=0, 
    show_other=False, show_activated=False, activated_label=None):
    # Build a menu with radio menu items from a list and connect them to 
    # the callback. The pref_value is what you would like to test for the 
    # default active radio item.
    import gtk
    if notset_label is None:
        notset_label = _("Unlimited")

    if activated_label is None:
        activated_label = _("Activated")

    menu = gtk.Menu()
    group = None
    if show_activated is False:
        if pref_value > -1 and pref_value not in value_list:
            value_list.pop()
            value_list.append(pref_value)
            
        for value in sorted(value_list):
            if suffix != None:
                menuitem = gtk.RadioMenuItem(group, str(value) + " " + \
                    suffix)
            else:
                menuitem = gtk.RadioMenuItem(group, str(value))
        
            group = menuitem

            if value == pref_value and pref_value != None:
                menuitem.set_active(True)

            if callback != None:
                menuitem.connect("toggled", callback)

            menu.append(menuitem)

    if show_activated is True:
        for value in sorted(value_list):
            menuitem = gtk.RadioMenuItem(group, str(activated_label))
        
            group = menuitem

            if value == pref_value and pref_value != None:
                menuitem.set_active(True)

            if callback != None:
                menuitem.connect("toggled", callback)

            menu.append(menuitem)

    if show_notset:
        menuitem = gtk.RadioMenuItem(group, notset_label)
        if pref_value < notset_lessthan and pref_value != None:
            menuitem.set_active(True)
        if show_activated and pref_value == 1:
            menuitem.set_active(True)
        menuitem.connect("toggled", callback)
        menu.append(menuitem)
        
    # Add the Other... menuitem
    if show_other is True:
        menuitem = gtk.SeparatorMenuItem()
        menu.append(menuitem)
        menuitem = gtk.MenuItem(_("Other..."))
        menuitem.connect("activate", callback)
        menu.append(menuitem)
                
    return menu

def show_other_dialog(string, default=None):
    """Shows a dialog to get an 'other' speed and return the value"""
    import gtk
    import gtk.glade
    dialog_glade = gtk.glade.XML(
        pkg_resources.resource_filename("deluge.ui.gtkui", 
                                    "glade/dgtkpopups.glade"))
    speed_dialog = dialog_glade.get_widget("speed_dialog")
    spin_title = dialog_glade.get_widget("spin_title")
    spin_title.set_text(_("%s" % string))
    spin_speed = dialog_glade.get_widget("spin_speed")
    if default != None:
        spin_speed.set_value(default)
    spin_speed.select_region(0, -1)
    response = speed_dialog.run()
    if response == 1: # OK Response
        value = spin_speed.get_value()
    else:
        speed_dialog.destroy()
        return None
        
    speed_dialog.destroy()
    return value
        
## Formatting text functions

def fsize(fsize_b):
    """Returns formatted string describing filesize
       fsize_b should be in bytes
       Returned value will be in either KB, MB, or GB
    """    
    fsize_kb = fsize_b / 1024.0
    if fsize_kb < 1000:
        return "%.1f KiB" % fsize_kb
    fsize_mb = fsize_kb / 1024.0
    if fsize_mb < 1000:
        return "%.1f MiB" % fsize_mb
    fsize_gb = fsize_mb / 1024.0
    return "%.1f GiB" % fsize_gb

def fpcnt(dec):
    """Returns a formatted string representing a percentage"""
    return '%.2f%%' % (dec * 100)

def fspeed(bps):
    """Returns a formatted string representing transfer speed"""
    return '%s/s' % (fsize(bps))

def fpeer(num_peers, total_peers):
    """Returns a formatted string num_peers (total_peers)"""
    if total_peers > -1:
        return "%d (%d)" % (num_peers, total_peers)
    else:
        return "%d" % num_peers
    
def ftime(seconds):
    """Returns a formatted time string"""
    if seconds == 0:
        return "Infinity"
    if seconds < 60:
        return '%ds' % (seconds)
    minutes = seconds / 60
    seconds = seconds % 60
    if minutes < 60:
        return '%dm %ds' % (minutes, seconds)
    hours = minutes / 60
    minutes = minutes % 60
    if hours < 24:
        return '%dh %dm' % (hours, minutes)
    days = hours / 24
    hours = hours % 24
    if days < 7:
        return '%dd %dh' % (days, hours)
    weeks = days / 7
    days = days % 7
    if weeks < 10:
        return '%dw %dd' % (weeks, days)
    return 'unknown'

def is_url(url):
    """A simple regex test to check if the URL is valid."""
    import re
    return bool(re.search('^(https?|ftp)://', url))

def fetch_url(url):
    """Downloads a torrent file from a given 
    URL and checks the file's validity."""
    import urllib
    from deluge.log import LOG as log
    try:
        filename, headers = urllib.urlretrieve(url)
    except IOError:
        log.debug("Network error while trying to fetch torrent from %s", url)
    else:
        if filename.endswith(".torrent") or headers["content-type"] ==\
        "application/x-bittorrent":
            return filename
        else:
            log.debug("URL doesn't appear to be a valid torrent file: %s", url)
            return None
            
def pythonize(var):
    """Translates DBUS types back to basic Python types."""
    if isinstance(var, list):
        return [pythonize(value) for value in var]
    if isinstance(var, tuple):
        return tuple([pythonize(value) for value in var])
    if isinstance(var, dict):
        return dict(
        [(pythonize(key), pythonize(value)) for key, value in var.iteritems()]
        )

    for klass in [unicode, str, bool, int, float, long]:
        if isinstance(var, klass):
            return klass(var)
    return var
