# -*- coding: utf-8 -*-
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
#               2007-2009 Andrew Resch <andrewresch@gmail.com>
#               2009 Damien Churchill <damoxc@gmail.com>
#               2010 Pedro Algarvio <pedro@algarvio.me>
#               2017 Calum Lind <calumlind+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import os.path

from pkg_resources import resource_filename


def get_resource(filename, subdir=False):
    folder = os.path.join('data', 'autoadd_options') if subdir else 'data'
    return resource_filename(__package__, os.path.join(folder, filename))
