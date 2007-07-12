#
# common.py
#
# Copyright (C) Andrew Resch  2007 <andrewresch@gmail.com> 
# 
# Deluge is free software.
# 
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 2 of the License, or (at your option)
# any later version.
# 
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with deluge.  If not, write to:
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

import logging
import pkg_resources
import xdg, xdg.BaseDirectory
import os.path

# Get the logger
log = logging.getLogger("deluge")

def get_version():
  """Returns the program version from the egg metadata"""
  return pkg_resources.require("Deluge")[0].version
  
def get_config_dir(filename=None):
  """ Returns the CONFIG_DIR path if no filename is specified
  Returns the CONFIG_DIR + filename as a path if filename is specified
  """
  if filename != None:
    return os.path.join(xdg.BaseDirectory.save_config_path("deluge"), filename)
  else:
    return xdg.BaseDirectory.save_config_path("deluge")

