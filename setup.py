#!/usr/bin/env python
# 
# Copyright (c) 2006 Zach Tibbitts ('zachtib') <zach@collegegeek.org>
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


## Modify the build arguments
from distutils import sysconfig

removals = ['-g', '-DNDEBUG', '-O2', '-Wstrict-prototypes']
additions = ['-DNDEBUG', '-O2']

cv = sysconfig.get_config_vars()
for removal in removals:
	cv["OPT"] = cv["OPT"].replace(" " + removal + " ", " ")
for addition in additions:
	cv["OPT"] = cv["OPT"] + " " + addition

import platform, os

pythonVersion = platform.python_version()[0:3]

from distutils.core import setup, Extension

deluge_core = Extension('deluge_core',
                    include_dirs = ['./include', './include/libtorrent',
												'/usr/include/python' + pythonVersion],
                    libraries = ['boost_filesystem', 'boost_date_time',
											'boost_program_options', 'boost_regex',
											'boost_serialization', 'boost_thread', 'z', 'pthread'],
                    extra_compile_args = ["-Wno-missing-braces"],
                    sources = ['src/deluge_core.cpp',
                    					 'include/cpp/alert.cpp',
										 'include/cpp/allocate_resources.cpp',
										 'include/cpp/bt_peer_connection.cpp',
										 'include/cpp/entry.cpp',
										 'include/cpp/escape_string.cpp',
										 'include/cpp/file.cpp',
										 'include/cpp/http_tracker_connection.cpp',
					                	 'include/cpp/identify_client.cpp',
										 'include/cpp/ip_filter.cpp',
 										 'include/cpp/peer_connection.cpp',
						             	 'include/cpp/piece_picker.cpp',     
										 'include/cpp/policy.cpp',       
					                	 'include/cpp/session.cpp',   
					                	 'include/cpp/session_impl.cpp',
                               			 'include/cpp/sha1.cpp',
									     'include/cpp/stat.cpp',
									     'include/cpp/storage.cpp',
								       	 'include/cpp/torrent.cpp',
										 'include/cpp/torrent_handle.cpp',
										 'include/cpp/torrent_info.cpp',
										 'include/cpp/tracker_manager.cpp',
										 'include/cpp/udp_tracker_connection.cpp',
					                	 'include/cpp/web_peer_connection.cpp',
										 'include/cpp/kademlia/closest_nodes.cpp',
										 'include/cpp/kademlia/dht_tracker.cpp',
										 'include/cpp/kademlia/find_data.cpp',
										 'include/cpp/kademlia/node.cpp',
										 'include/cpp/kademlia/node_id.cpp',
										 'include/cpp/kademlia/refresh.cpp',
										 'include/cpp/kademlia/routing_table.cpp',
										 'include/cpp/kademlia/rpc_manager.cpp',
										 'include/cpp/kademlia/traversal_algorithm.cpp'])


setup(name="deluge", fullname="Deluge BitTorrent Client", version="0.5.0",
	author="Zach Tibbitts, Alon Zakai",
	author_email="zach@collegegeek.org, kripkensteiner@gmail.com",
	description="A bittorrent client written in PyGTK",
	url="http://deluge-torrent.org",
	license="GPLv2",
	scripts=["scripts/deluge"],
	packages=['deluge'],
	package_dir = {'deluge': 'src'},
	data_files=[("share/deluge/glade", ["glade/delugegtk.glade", "glade/dgtkpopups.glade", "glade/dgtkpref.glade"]),
                                ("share/deluge/pixmaps", ["pixmaps/deluge32.png","pixmaps/deluge128.png", "pixmaps/deluge256.png"])],
    ext_package='deluge',
	ext_modules=[deluge_core]
	)
