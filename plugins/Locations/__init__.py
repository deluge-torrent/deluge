# -*- coding: utf-8 -*-
# Locations plugin for Deluge - keep different settings for each location.
# Copyright (C) 2007 - Kristoffer Lundén <kristoffer.lunden@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

plugin_name = _("Locations")
plugin_author = "Kristoffer Lundén"
plugin_version = "0.2"
plugin_description = _("""Automagically remembers relevant settings for different locations.

When this plugin is active, it will remember a lot of useful network-specific preferences, such as up- or download limits, open ports and proxy information. Just change preferences to suit each location while connected, and Deluge will automagically use those settings the next time you connect at that location. There is no other configuration needed.

The plugin determines location by identifying the unique MAC address of the Gateway used for the connection. It is therefore possible to have different settings for home and work, or for broadband, 3G and dial-up on the fly.
""")

def deluge_init(deluge_path):
    global path
    path = deluge_path

from Locations.plugin import plugin_Locations

def enable(core, interface):
    global path
    return plugin_Locations(path, core, interface)

