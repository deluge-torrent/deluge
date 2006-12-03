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
									 os.path.expanduser("~") + "/Temp",
									 "test_state.dat")

#my_torrent = manager.add_torrent("ubuntu.torrent", ".", True)

#print "Unique ID:", my_torrent

for i in range(2):
	print "STATE:"
	print manager.get_state(0)#my_torrent)
	print ""

	sleep(2)

manager.quit()
