#
# common.py
#
# Copyright (C) 2007 Andrew Resch ('andar') <andrewresch@gmail.com>
# 
# Deluge is free software.
# 
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 2 of the License, or (at your option)
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

import pkg_resources
import xdg, xdg.BaseDirectory

def get_version():
    """Returns the program version from the egg metadata"""
    return pkg_resources.require("Deluge")[0].version
    
def get_config_dir(filename=None):
    """ Returns the config path if no filename is specified
    Returns the config directory + filename as a path if filename is specified
    """
    if filename != None:
        return os.path.join(xdg.BaseDirectory.save_config_path("deluge"), 
                                                                    filename)
    else:
        return xdg.BaseDirectory.save_config_path("deluge")

def get_default_download_dir():
    """Returns the default download directory"""
    return os.environ.get("HOME")

def get_default_torrent_dir():
    """Returns the default torrent directory"""
    return os.path.join(get_config_dir(), "torrentfiles")
    
def get_default_plugin_dir():
    """Returns the default plugin directory"""
    return os.path.join(get_config_dir(), "plugins")

## Formatting text functions

def estimate_eta(total_size, total_done, download_rate):
    """Returns a string with the estimated ETA and will return 'Unlimited'
       if the torrent is complete
    """
    try:
        return ftime(get_eta(total_size, total_done, download_rate))
    except ZeroDivisionError:
        return "Infinity"
    
def get_eta(size, done, speed):
    """Returns the ETA in seconds
       Will raise an exception if the torrent is completed
    """
    if (size - done) == 0:
        raise ZeroDivisionError
    return (size - done) / speed

def fsize(fsize_b):
    """Returns formatted string describing filesize
       fsize_b should be in bytes
       Returned value will be in either KB, MB, or GB
    """    
    fsize_kb = float (fsize_b / 1024.0)
    if fsize_kb < 1000:
        return "%.1f KiB" % fsize_kb
    fsize_mb = float (fsize_kb / 1024.0)
    if fsize_mb < 1000:
        return "%.1f MiB" % fsize_mb
    fsize_gb = float (fsize_mb / 1024.0)
    return "%.1f GiB" % fsize_gb

def fpcnt(dec):
    """Returns a formatted string representing a percentage"""
    return '%.2f%%' % (dec * 100)

def fspeed(bps):
    """Returns a formatted string representing transfer speed"""
    return '%s/s' % (fsize(bps))

def fseed(num_seeds, total_seeds):
    """Returns a formatted string num_seeds (total_seeds)"""
    return str(str(num_seeds) + " (" + str(total_seeds) + ")")
    
def fpeer(num_peers, total_peers):
    """Returns a formatted string num_peers (total_peers)"""
    return str(str(num_peers) + " (" + str(total_peers) + ")")
    
def ftime(seconds):
    """Returns a formatted time string"""
    if seconds < 60:
        return '%ds' % (seconds)
    minutes = int(seconds/60)
    seconds = seconds % 60
    if minutes < 60:
        return '%dm %ds' % (minutes, seconds)
    hours = int(minutes/60)
    minutes = minutes % 60
    if hours < 24:
        return '%dh %dm' % (hours, minutes)
    days = int(hours/24)
    hours = hours % 24
    if days < 7:
        return '%dd %dh' % (days, hours)
    weeks = int(days/7)
    days = days % 7
    if weeks < 10:
        return '%dw %dd' % (weeks, days)
    return 'unknown'
