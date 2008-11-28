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
# 	Boston, MA    02110-1301, USA.
#


"""Logging functions"""

import logging

# Setup the logger
logging.basicConfig(
    level=logging.ERROR,
    format="[%(levelname)-8s] %(asctime)s %(module)s:%(lineno)d %(message)s",
    datefmt="%H:%M:%S"
)

def setLoggerLevel(level):
    """
    Sets the logger level.

    :param level: str, a string representing the desired level

    """
    levels = {
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "none": logging.CRITICAL,
        "debug": logging.DEBUG
    }

    if level not in levels:
        return

    global LOG
    LOG.setLevel(levels[level])

# Get the logger
LOG = logging.getLogger("deluge")
