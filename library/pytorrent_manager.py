# 
# Copyright (C) 2006 Zach Tibbitts <zach@collegegeek.org>
# Copyright (C) 2006 Alon Zakai ('Kripken') <kripkensteiner@gmail.com>
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

# pytorrent-manager: backend/non-gui routines, that are not part of the core
# pytorrent module. pytorrent itself is mainly an interface to libtorrent,
# with some arrangements of exception classes for Python, etc.; also, some
# additional code that fits in well at the C++ level of libtorrent. All other
# backend routines should be in pytorrent-manager.
#
# Things which pytorrent-manager should do:
#
# 1. Save/Load torrent states (list of torrents in system, + their states) to file
#    (AutoSaveTorrents in deluge.py)
# 2. Manage basic queuing: how many active downloads, and autopause the rest (this
#    is currently spread along deluge.py and torrenthandler.py)
# 2a.Queue up and queue down, etc., functions (in deluge.py)
# 3. Save/Load a preferences file, with all settings (max ports, listen port, use
#    DHT, etc. etc.)
# 4. Manage autoseeding to a certain share % (currently in torrenthandler.py)
# 5. Handle caching of .torrent files and so forth (currently in deluge.py)
# 6. A 'clear completed' function, that works on the BACKEND data, unlike the
#    current implementation which works on the frontend (in torrenthander.py)
# 7. Various statistics-reporting functions - # of active torrents, etc. etc.
#    (getNumActiveTorrents in torrenthandler.py)
# 8. Remove torrent's data (in deluge.py)
#

import pytorrent

