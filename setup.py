# setup.py
#
# Copyright (c) 2007 Andrew Resch ('andar') <andrewresch@gmail.com>
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
#
#  In addition, as a special exception, the copyright holders give
#  permission to link the code of portions of this program with the OpenSSL
#  library.
#  You must obey the GNU General Public License in all respects for all of
#  the code used other than OpenSSL. If you modify file(s) with this
#  exception, you may extend this exception to your version of the file(s),
#  but you are not obligated to do so. If you do not wish to do so, delete
#  this exception statement from your version. If you delete this exception
#  statement from all source files in the program, then also delete it here.

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages, Extension
import platform
import glob

python_version = platform.python_version()[0:3]

# The libtorrent extension
__extra_compile_args = [
  "-Wno-missing-braces",
  "-DHAVE_INCLUDE_LIBTORRENT_ASIO____ASIO_HPP=1", 
  "-DHAVE_INCLUDE_LIBTORRENT_ASIO_SSL_STREAM_HPP=1", 
  "-DHAVE_INCLUDE_LIBTORRENT_ASIO_IP_TCP_HPP=1", 
  "-DHAVE_PTHREAD=1",
  "-DTORRENT_USE_OPENSSL=1",
  "-DHAVE_SSL=1"
]

__include_dirs = [
  './libtorrent',
  './libtorrent/include',
  './libtorrent/include/libtorrent',
  '/usr/include/python' + python_version
]
            
__libraries = [
  'boost_filesystem',
  'boost_date_time',
  'boost_thread',
  'z',
  'pthread',
  'ssl'
]
			
__sources = glob.glob("./libtorrent/src/*.cpp") + glob.glob("./libtorrent/src/kademelia/*.cpp") + glob.glob("./libtorrent/bindings/python/src/*.cpp")

# Remove file_win.cpp as it is only for Windows builds
for source in __sources:
  if "file_win.cpp" in source:
    __sources.remove(source)
    break

libtorrent = Extension(
  'libtorrent',
  include_dirs = __include_dirs,
  libraries = __libraries,
  extra_compile_args = __extra_compile_args,
  sources = __sources
)

print find_packages("deluge")
# Main setup

__data_files = [
 # ('share/deluge/glade',  glob.glob("share/deluge/glade/*.glade")),
 # ('share/deluge/pixmaps', glob.glob('share/deluge/pixmaps/*.png')),
  ('share/applications' , ["deluge/share/applications/deluge.desktop"]),
  ('share/pixmaps' , ["deluge/share/pixmaps/deluge.xpm"])
]
        
setup(
  name = "deluge",
  fullname = "Deluge Bittorent Client",
  version = "0.6",
  author = "Zach Tibbitts, Alon Zakai, Marcos Pinto, Andrew Resch",
  author_email = "zach@collegegeek.org, kripkensteiner@gmail.com, marcospinto@dipconsultants.com, andrewresch@gmail.com",
  description = "GTK+ bittorrent client",
  url = "http://deluge-torrent.org",
  license = "GPLv2",
  
#  packages = find_packages("deluge"),
  include_package_data = True,
  #scripts = ["scripts/deluge"],
  data_files = __data_files,
  ext_package = "deluge",
  ext_modules = [libtorrent],
  packages=['deluge'],
  package_dir = {'deluge': 'deluge/src'},
  entry_points = """
    [console_scripts]
      deluge = deluge.main:main
  """
)
