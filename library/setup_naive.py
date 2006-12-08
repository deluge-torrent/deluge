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

import platform

pythonVersion = platform.python_version()[0:3]

from distutils.core import setup, Extension

module1 = Extension('flood_core',
                    include_dirs = ['./include', './include/libtorrent',
												'/usr/include/python' + pythonVersion],
                    libraries = ['boost_filesystem', 'boost_date_time',
											'boost_program_options', 'boost_regex',
											'boost_serialization', 'boost_thread', 'z', 'pthread'],
                    extra_compile_args = ["-Wno-missing-braces"],
#                    extra_link_args = [""],
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
										 'cpp/flood_core.cpp',
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

setup(name = 'flood_core',
      version = '0.5.0',
      description = "A module for the bittorrent protocol. Built using Rasterbar's libtorrent.",
		author="Alon Zakai ('Kripken'), Zach Tibbitts",
		author_email="kripkensteiner@gmail.com",
		url="http://www.deluge-torrent.org",
      ext_modules = [module1])
