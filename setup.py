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


from distutils import sysconfig

pythonVersion = platform.python_version()[0:3]



#
# NOTE: The following "hack" removes the -g and -Wstrict-prototypes
# build options from the command that will compile the C++ module,
# deluge_core.  While we understand that you aren't generally
# encouraged to do this, we have done so for the following reasons:
# 1) The -g compiler option produces debugging information about
#	the compiled module.  However, this option increases the 
#	size of deluge_core.so from ~1.9MB to 13.6MB and slows down
#	the program's execution without offering any benefits 
#	whatsoever.
# 2) -Wstrict-prototypes is not a valid C++ build option, and the
#	compiler will throw a number of warnings at compile time.
#	While this does not really impact anything, it makes it
#	seem as if something is going wrong with the compile, and
#	it has been removed to prevent confusion.
#

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



#
# NOTE: The Rasterbar Libtorrent source code is in the libtorrent/ directory
# inside of Deluge's source tarball.  On several occasions, it has been 
# pointed out to us that we should build against the system's installed 
# libtorrent rather than our internal copy, and a few people even submitted
# patches to do just that. However, as of now, this version
# of libtorrent is not available in Debian, and as a result, Ubuntu. Once
# libtorrent-rasterbar is available in the repositories of these distributions,
# we will probably begin to build against a system libtorrent, but at the
# moment, we are including the source code to make packaging on Debian and
# Ubuntu possible.
#
deluge_core = Extension('deluge_core',
                    include_dirs = ['./libtorrent', './libtorrent/include', 
                    			'./libtorrent/include/libtorrent', 
                    			'/usr/include/python' + pythonVersion],
                    libraries = ['boost_filesystem', 'boost_date_time',
					'boost_program_options', 'boost_regex',
					'boost_serialization', 'boost_thread', 
					'z', 'pthread'],
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

# Thanks to Iain Nicol for code to save the location for installed prefix
# At runtime, we need to know where we installed the data to.
import shutil
from distutils import cmd
from distutils.command.install import install as _install

class write_data_install_path(cmd.Command):
	description = 'saves the data installation path for access at runtime'
	
	def initialize_options(self):
		self.data_install_dir = None
		self.lib_build_dir = None

	def finalize_options(self):
		self.set_undefined_options('install',
			('install_data', 'data_install_dir')
		)		
		self.set_undefined_options('build',
			('build_lib', 'lib_build_dir')
		)

	def run(self):
		conf_filename = os.path.join(self.lib_build_dir,
			'deluge', 'dcommon.py')

		conf_file = open(conf_filename, 'r')
		data = conf_file.read()
		conf_file.close()
		data = data.replace('@datadir@', self.data_install_dir)

		conf_file = open(conf_filename, 'w')
		conf_file.write(data)
		conf_file.close()

class unwrite_data_install_path(cmd.Command):
	description = 'undoes write_data_install_path'

	def initialize_options(self):
		self.lib_build_dir = None

	def finalize_options(self):		
		self.set_undefined_options('build',
			('build_lib', 'lib_build_dir')
		)

	def run(self):
		dest = os.path.join(self.lib_build_dir,
			'deluge', 'dcommon.py')
		shutil.copyfile('src/dcommon.py', dest)

class install(_install):
	sub_commands = [('write_data_install_path', None)] + \
		_install.sub_commands + [('unwrite_data_install_path', None)]

cmdclass = {
	'install': install,
	'write_data_install_path': write_data_install_path,
	'unwrite_data_install_path': unwrite_data_install_path,
}


setup(name="deluge", fullname="Deluge BitTorrent Client", version="0.4.90.3",
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
	ext_modules=[deluge_core],
	cmdclass=cmdclass
	)
