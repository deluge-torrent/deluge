# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import print_function

import logging
import sys

import deluge.common
import deluge.configmanager
import deluge.log
from deluge.commonoptions import CommonOptionParser

try:
    from setproctitle import setproctitle
except ImportError:
    def setproctitle(title):
        return

DEFAULT_PREFS = {
    "default_ui": "gtk"
}

if 'dev' not in deluge.common.get_version():
    import warnings
    warnings.filterwarnings('ignore', category=DeprecationWarning, module='twisted')


class _UI(object):

    def __init__(self, name="gtk"):
        self.__name = name

        if name == "gtk":
            deluge.common.setup_translations(setup_pygtk=True)
        else:
            deluge.common.setup_translations()

        self.__parser = CommonOptionParser()

    @property
    def name(self):
        return self.__name

    @property
    def parser(self):
        return self.__parser

    @property
    def options(self):
        return self.__options

    @property
    def args(self):
        return self.__args

    def start(self):
        # Make sure all arguments are unicode
        argv = deluge.common.unicode_argv()[1:]
        (self.__options, self.__args) = self.__parser.parse_args(argv)

        log = logging.getLogger(__name__)

        setproctitle("deluge-%s" % self.__name)

        log.info("Deluge ui %s", deluge.common.get_version())
        log.debug("options: %s", self.__options)
        log.debug("args: %s", self.__args)
        log.info("Starting %s ui..", self.__name)
