# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Ido Abramovich <ido.deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

UI_PATH = __path__[0]  # NOQA Ignore 'E402 module level import not at top of file'

from deluge.ui.console.console import Console


def start():
    Console().start()
