#/* 
#Copyright: A. Zakai ('Kripken') <kripkensteiner@gmail.com> http://6thsenseless.blogspot.com
#
#2006-15-9
#
#This code is licensed under the terms of the GNU General Public License (GPL),
#version 2 or above; See /usr/share/common-licenses/GPL , or see
#http://www.fsf.org/licensing/licenses/gpl.html
#*/


import deluge
from   time    import sleep
import os

manager = deluge.Manager("DL", "0500", "deluge - testing only",
									 os.path.expanduser("~") + "/Temp")# blank_slate=True)

#manager.set_pref('max_upload_rate', 6*1024)

##my_torrent = manager.add_torrent("ubuntu.iso.torrent", ".", True)

##print "Unique ID:", my_torrent

print "PREFS:", manager.prefs

try:
	while True:
		print "STATE:", manager.get_state()
		print "# torrents:", manager.get_num_torrents()
		for unique_ID in manager.get_unique_IDs():
			state =  manager.get_torrent_state(unique_ID)
			for key in state.keys():
				print key, state[key]
		manager.handle_events()
		print ""
		sleep(2)
except KeyboardInterrupt:
	print "Shutting down..."
	manager.quit()
