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

import platform, os, glob
from distutils.core import setup, Extension

## Modify the build arguments
from distutils import sysconfig

pythonVersion = platform.python_version()[0:3]

removals = ['-g', '-DNDEBUG', '-O2', '-Wstrict-prototypes']
additions = ['-DNDEBUG', '-O2']

if pythonVersion == '2.5':
	cv_opt = sysconfig.get_config_vars()["CFLAGS"]
	for removal in removals:
		cv_opt = cv_opt.replace(removal, " ")
	for addition in additions:
		cv_opt = cv_opt + " " + addition
	sysconfig.get_config_vars()["CFLAGS"] = ' '.join(cv_opt.split())
else:
	cv_opt = sysconfig.get_config_vars()["OPT"]
	for removal in removals:
		cv_opt = cv_opt.replace(removal, " ")
	for addition in additions:
		cv_opt = cv_opt + " " + addition
	sysconfig.get_config_vars()["OPT"] = ' '.join(cv_opt.split())




deluge_core = Extension('deluge_core',
                    include_dirs = ['./libtorrent', './libtorrent/include', './libtorrent/include/libtorrent',
												'/usr/include/python' + pythonVersion],
                    libraries = ['boost_filesystem', 'boost_date_time',
											'boost_program_options', 'boost_regex',
											'boost_serialization', 'boost_thread', 'z', 'pthread'],
                    extra_compile_args = ["-Wno-missing-braces"],
                    sources = ['src/deluge_core.cpp',
                    					 'libtorrent/src/alert.cpp',
										 'libtorrent/src/allocate_resources.cpp',
										 'libtorrent/src/bt_peer_connection.cpp',
										 'libtorrent/src/entry.cpp',
										 'libtorrent/src/escape_string.cpp',
										 'libtorrent/src/file.cpp',
										 'libtorrent/src/http_tracker_connection.cpp',
					                	 'libtorrent/src/identify_client.cpp',
										 'libtorrent/src/ip_filter.cpp',
 										 'libtorrent/src/peer_connection.cpp',
						             	 'libtorrent/src/piece_picker.cpp',     
										 'libtorrent/src/policy.cpp',       
					                	 'libtorrent/src/session.cpp',   
					                	 'libtorrent/src/session_impl.cpp',
                               			 'libtorrent/src/sha1.cpp',
									     'libtorrent/src/stat.cpp',
									     'libtorrent/src/storage.cpp',
								       	 'libtorrent/src/torrent.cpp',
										 'libtorrent/src/torrent_handle.cpp',
										 'libtorrent/src/torrent_info.cpp',
										 'libtorrent/src/tracker_manager.cpp',
										 'libtorrent/src/udp_tracker_connection.cpp',
					                	 'libtorrent/src/web_peer_connection.cpp',
										 'libtorrent/src/kademlia/closest_nodes.cpp',
										 'libtorrent/src/kademlia/dht_tracker.cpp',
										 'libtorrent/src/kademlia/find_data.cpp',
										 'libtorrent/src/kademlia/node.cpp',
										 'libtorrent/src/kademlia/node_id.cpp',
										 'libtorrent/src/kademlia/refresh.cpp',
										 'libtorrent/src/kademlia/routing_table.cpp',
										 'libtorrent/src/kademlia/rpc_manager.cpp',
										 'libtorrent/src/kademlia/traversal_algorithm.cpp'])

data = [('share/deluge/glade',  glob.glob('glade/*.glade')),
        ('share/deluge/pixmaps', glob.glob('pixmaps/*.png')),
        ('share/applications' , ['deluge.desktop']),
        ('share/pixmaps' , ['deluge.xpm'])]

for plugin in glob.glob('plugins/*'):
	data.append( ('share/deluge/' + plugin, glob.glob(plugin + '/*')) )

setup(name="deluge", fullname="Deluge BitTorrent Client", version="0.4.90.1",
	author="Zach Tibbitts, Alon Zakai",
	author_email="zach@collegegeek.org, kripkensteiner@gmail.com",
	description="A bittorrent client written in PyGTK",
	url="http://deluge-torrent.org",
	license="GPLv2",
	scripts=["scripts/deluge"],
	packages=['deluge'],
	package_dir = {'deluge': 'src'},
	data_files=data,
    ext_package='deluge',
	ext_modules=[deluge_core]
	)
