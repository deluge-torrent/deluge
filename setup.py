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
                    sources = ['cpp/alert.cpp',
										 'cpp/allocate_resources.cpp',
										 'cpp/bt_peer_connection.cpp',
										 'cpp/entry.cpp',
										 'cpp/escape_string.cpp',
										 'cpp/file.cpp',
										 'cpp/http_tracker_connection.cpp',
					                	 'cpp/identify_client.cpp',
										 'cpp/ip_filter.cpp',
 										 'cpp/peer_connection.cpp',
						             	 'cpp/piece_picker.cpp',     
										 'cpp/policy.cpp',           
										 'cpp/deluge_core.cpp',
					                	 'cpp/session.cpp',   
					                	 'cpp/session_impl.cpp',
                               			 'cpp/sha1.cpp',
									     'cpp/stat.cpp',
									     'cpp/storage.cpp',
								       	 'cpp/torrent.cpp',
										 'cpp/torrent_handle.cpp',
										 'cpp/torrent_info.cpp',
										 'cpp/tracker_manager.cpp',
										 'cpp/udp_tracker_connection.cpp',
					                	 'cpp/web_peer_connection.cpp',
										 'cpp/kademlia/closest_nodes.cpp',
										 'cpp/kademlia/dht_tracker.cpp',
										 'cpp/kademlia/find_data.cpp',
										 'cpp/kademlia/node.cpp',
										 'cpp/kademlia/node_id.cpp',
										 'cpp/kademlia/refresh.cpp',
										 'cpp/kademlia/routing_table.cpp',
										 'cpp/kademlia/rpc_manager.cpp',
										 'cpp/kademlia/traversal_algorithm.cpp'])


setup(name="deluge", fullname="Deluge BitTorrent Client", version="0.5.0",
	author="Zach Tibbitts, Alon Zakai",
	author_email="zach@collegegeek.org, kripkensteiner@gmail.com",
	description="A bittorrent client written in PyGTK",
	url="http://deluge-torrent.org",
	license="GPLv2",
	scripts=["scripts/deluge"],
	packages=['deluge'],
	package_dir = {'deluge': 'src'},
	package_data={'deluge': ['glade/*.glade', 'pixmaps/*.png']},
	ext_package='deluge',
	ext_modules=[deluge_core]
	)
