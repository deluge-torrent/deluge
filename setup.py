# 
# Copyright © 2006 Zach Tibbitts ('zachtib') <zach@collegegeek.org>
#
# 2006-15-9
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#

import platform, os

pythonVersion = platform.python_version()[0:3]

from distutils.core import setup, Extension


setup(name="Deluge", fullname="Deluge Bittorrent Client", version="0.5.0",
	author="Zach Tibbitts",
	description="A bittorrent client written in PyGTK",
	url="http://deluge-torrent.org",
	license="GPLv2",
	
	scripts=["scripts/deluge-gtk", "scripts/deluge-tools"],
	py_modules=["dcommon", "deluge", "delugegtk", "dexml"],
	data_files=[("glade", ["glade/delugegtk.glade"])],
	##ext_modules=[torrent]
	)
