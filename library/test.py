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

manager = pytorrent.manager("PT", "0500", "pytorrent - testing only", "test_state.dat")

my_torrent = manager.add_torrent("ubuntu.torrent", ".", True)

print "Unique ID:", my_torrent

while True:
	print "STATE:"
	print manager.get_state(my_torrent)
	print ""

	sleep(2)
