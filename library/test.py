#/* 
#Copyright: A. Zakai ('Kripken') <kripkensteiner@gmail.com> http://6thsenseless.blogspot.com
#
#2006-15-9
#
#This code is licensed under the terms of the GNU General Public License (GPL),
#version 2 or above; See /usr/share/common-licenses/GPL , or see
#http://www.fsf.org/licensing/licenses/gpl.html
#*/


import pytorrent
from   time    import sleep
import os

manager = pytorrent.manager("PT", "0500", "pytorrent - testing only",
									 os.path.expanduser("~") + "/Temp")

#manager.prefs['max_active_torrents'] = 1

my_torrent = manager.add_torrent("xubuntu-6.10-desktop-i386.iso.torrent", ".", True)

#print "Unique ID:", my_torrent

print "PREFS:", manager.prefs

try:
	while True:
		print "STATE:", manager.get_state()
		print "# torrents:", manager.get_num_torrents()
		for unique_ID in manager.get_unique_IDs():
			print unique_ID, manager.get_torrent_state(unique_ID)
		manager.handle_events()
		print ""
		sleep(2)
except KeyboardInterrupt:
	manager.quit()
