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


torrent = Extension('torrent',
                    include_dirs = ['./library/include', './library/include/libtorrent',
												'/usr/include/python' + pythonVersion],
                    libraries = ['boost_filesystem', 'boost_date_time',
											'boost_program_options', 'boost_regex',
											'boost_serialization', 'boost_thread', 'z', 'pthread'],
                    sources = ['library/alert.cpp',
										 'library/allocate_resources.cpp',
										 'library/bt_peer_connection.cpp',
										 'library/entry.cpp',
										 'library/escape_string.cpp',
										 'library/file.cpp',
										 'library/http_tracker_connection.cpp',
					                'library/identify_client.cpp',
										 'library/ip_filter.cpp',
 										 'library/peer_connection.cpp',
						             'library/piece_picker.cpp',     
										 'library/policy.cpp',           
										 'library/python-libtorrent.cpp',
					                'library/session.cpp',   
					                'library/session_impl.cpp',
                               'library/sha1.cpp',
									    'library/stat.cpp',
									    'library/storage.cpp',
								       'library/torrent.cpp',
										 'library/torrent_handle.cpp',
										 'library/torrent_info.cpp',
										 'library/tracker_manager.cpp',
										 'library/udp_tracker_connection.cpp',
					                'library/web_peer_connection.cpp',
										 './library/kademlia/closest_nodes.cpp',
										 './library/kademlia/dht_tracker.cpp',
										 './library/kademlia/find_data.cpp',
										 './library/kademlia/node.cpp',
										 './library/kademlia/node_id.cpp',
										 './library/kademlia/refresh.cpp',
										 './library/kademlia/routing_table.cpp',
										 './library/kademlia/rpc_manager.cpp',
										 './library/kademlia/traversal_algorithm.cpp'])

setup(name="Deluge", fullname="Deluge Bittorrent Client", version="0.5.0",
	author="Zach Tibbitts",
	description="A bittorrent client written in PyGTK",
	url="http://deluge-torrent.org",
	license="GPLv2",
	
	scripts=["scripts/deluge-gtk", "scripts/deluge-tools"],
	py_modules=["dcommon", "deluge", "delugegtk", "dexml"],
	data_files=[("glade", ["glade/delugegtk.glade"])],
	ext_modules=[torrent]
	)
