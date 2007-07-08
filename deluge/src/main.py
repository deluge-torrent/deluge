#
# main.py
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

# The main starting point for the program.  This function is called when the 
# user runs the command 'deluge'.

import logging
import os
import signal
from optparse import OptionParser

from deluge.daemon import Daemon
from deluge.ui import Ui
import deluge.common

# Setup the logger
logging.basicConfig(
  level=logging.DEBUG,
  format="[%(levelname)-8s] %(name)s:%(module)s:%(lineno)d %(message)s"
)
# Get the logger for deluge
log = logging.getLogger("deluge")

def main():
  # Setup the argument parser
  # FIXME: need to use deluge.common to fill in version
  parser = OptionParser(usage="%prog [options] [actions]", 
                        version=deluge.common.get_version())
  parser.add_option("--daemon", dest="daemon", help="Start Deluge daemon",
            metavar="DAEMON", action="store_true", default=False)
  parser.add_option("--ui", dest="ui", help="Start Deluge UI",
            metavar="UI", action="store_true", default=False)

  # Get the options and args from the OptionParser
  (options, args) = parser.parse_args()

  log.info("Deluge %s", deluge.common.get_version())
  
  log.debug("options: %s", options)
  log.debug("args: %s", args)
    
  daemon = None
  pid = None
  uri = None
  
  # Start the daemon
  if options.daemon:
    log.info("Starting daemon..")
    # We need to fork() the process to run it in the background...
    # FIXME: We cannot use fork() on Windows
    pid = os.fork()
    if not pid:
      # Since we are starting daemon this process will not start a UI
      options.ui = False
      # Create the daemon object
      daemon = Daemon()

  # Start the UI
  if options.ui:
    log.info("Starting ui..")
    ui = Ui()
  
  # Stop Deluge
  log.info ("Stopping Deluge..")
  
  # Kill the daemon
  if pid:
    log.info("Killing daemon..")
    os.kill(pid, signal.SIGTERM)

