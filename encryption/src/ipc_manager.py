# ipc_manager.py
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
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.


# Code for dbus_importing borrowed from Listen (http://listen-project.org)
# I couldn't figure out how to use dbus without breaking on versions past
# 0.80.0.  I finally found a solution by reading the source code from the
# Listen project. 
try:
	import dbus, dbus.service
	dbus_version = getattr(dbus, 'version', (0,0,0))
	if dbus_version >= (0,41,0) and dbus_version < (0,80,0):
		dbus.SessionBus()
		import dbus.glib
	elif dbus_version >= (0,80,0):
		from dbus.mainloop.glib import DBusGMainLoop
		DBusGMainLoop(set_as_default=True)
		dbus.SessionBus()
	else:
		pass
except: dbus_imported = False
else: dbus_imported = True

if dbus_imported:
	class Manager(dbus.service.Object):
		def __init__(self, interface, object_path='/org/deluge_torrent/DelugeObject'):
			self.interface = interface
			self.bus = dbus.SessionBus()
			bus_name = dbus.service.BusName("org.deluge_torrent.Deluge", bus=self.bus)
			dbus.service.Object.__init__(self, bus_name, object_path)

		## external_add_torrent should only be called from outside the class	
		@dbus.service.method('org.deluge_torrent.Deluge')
		def external_add_torrent(self, torrent_file):
			self.interface.external_add_torrent(torrent_file)
else:
	# This is a fallback class in case dbus is not available
	class Manager:
		def __init__(self, interface, object_path=None):
			self.interface = interface
		
		def external_add_torrent(self, torrent_file):
			print "I can't do anything with this."
