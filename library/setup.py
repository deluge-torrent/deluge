#/* 
#Copyright: A. Zakai ('Kripken') <kripkensteiner@gmail.com> http://6thsenseless.blogspot.com
#
#2006-15-9
#
#This code is licensed under the terms of the GNU General Public License (GPL),
#version 2 or above; See /usr/share/common-licenses/GPL , or see
#http://www.fsf.org/licensing/licenses/gpl.html
#*/

import platform

pythonVersion = platform.python_version()[0:3]

print "========================================="
print "Creating python-libtorrent for Python " + pythonVersion
print "========================================="

from distutils.core import setup, Extension

module1 = Extension('torrent',
                    include_dirs = ['./include', './include/libtorrent',
												'/usr/include/python' + pythonVersion],
                    libraries = ['boost_filesystem', 'boost_date_time',
											'boost_program_options', 'boost_regex',
											'boost_serialization', 'boost_thread', 'z', 'pthread'],
                    sources = ['alert.cpp',
										 'allocate_resources.cpp',
										 'bt_peer_connection.cpp',
										 'entry.cpp',
										 'escape_string.cpp',
										 'file.cpp',
										 'http_tracker_connection.cpp',
					                'identify_client.cpp',
										 'ip_filter.cpp',
 										 'peer_connection.cpp',
						             'piece_picker.cpp',     
										 'policy.cpp',           
										 'python-libtorrent.cpp',
					                'session.cpp',   
					                'session_impl.cpp',
                               'sha1.cpp',
									    'stat.cpp',
									    'storage.cpp',
								       'torrent.cpp',
										 'torrent_handle.cpp',
										 'torrent_info.cpp',
										 'tracker_manager.cpp',
										 'udp_tracker_connection.cpp',
					                'web_peer_connection.cpp',
										 './kademlia/closest_nodes.cpp',
										 './kademlia/dht_tracker.cpp',
										 './kademlia/find_data.cpp',
										 './kademlia/node.cpp',
										 './kademlia/node_id.cpp',
										 './kademlia/refresh.cpp',
										 './kademlia/routing_table.cpp',
										 './kademlia/rpc_manager.cpp',
										 './kademlia/traversal_algorithm.cpp'])

setup (name = 'Python-libtorrent',
       version = '0.3.1',
       description = 'Wrapper code for libtorrent C++ torrent library (Sourceforge, not Rakshasa)',
       ext_modules = [module1])
