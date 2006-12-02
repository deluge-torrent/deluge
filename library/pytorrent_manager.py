# 
# Copyright (c) 2006 Alon Zakai ('Kripken') <kripkensteiner@gmail.com>
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

# pytorrent-manager: backend/non-gui routines, that are not part of the core
# pytorrent module. pytorrent itself is mainly an interface to libtorrent,
# with some arrangements of exception classes for Python, etc.; also, some
# additional code that fits in well at the C++ level of libtorrent. All other
# backend routines should be in pytorrent-manager. (Just an idea)

import pytorrent

