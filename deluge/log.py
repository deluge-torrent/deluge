#
# log.py
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#
#


"""Logging functions"""

import logging

levels = {
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "none": logging.CRITICAL,
    "debug": logging.DEBUG
}
def setupLogger(level="error", filename=None, filemode="w"):
    """
    Sets up the basic logger and if `:param:filename` is set, then it will log
    to that file instead of stdout.

    :param level: str, the level to log
    :param filename: str, the file to log to
    """

    if not level or level not in levels:
        level = "error"

    logging.basicConfig(
        level=levels[level],
        format="[%(levelname)-8s] %(asctime)s %(module)s:%(lineno)d %(message)s",
        datefmt="%H:%M:%S",
        filename=filename,
        filemode=filemode
    )

def setLoggerLevel(level):
    """
    Sets the logger level.

    :param level: str, a string representing the desired level

    """
    if level not in levels:
        return

    global LOG
    LOG.setLevel(levels[level])

# Get the logger
LOG = logging.getLogger("deluge")
