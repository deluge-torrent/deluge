#/* 
#Copyright: A. Zakai ('Kripken') <kripkensteiner@gmail.com> http://6thsenseless.blogspot.com
#
#2006-15-9
#
#This code is licensed under the terms of the GNU General Public License (GPL),
#version 2 or above; See /usr/share/common-licenses/GPL , or see
#http://www.fsf.org/licensing/licenses/gpl.html
#*/


import pytorrent_core
from   time    import sleep

pytorrent_core.init("PT", 0, 5, 0, 0, "pytorrent - testing only")

myTorrent = pytorrent_core.add_torrent("ubuntu.torrent", ".", True)

while True:
	print "STATE:"
	print pytorrent_core.get_state(myTorrent)
	print ""

	sleep(1)
