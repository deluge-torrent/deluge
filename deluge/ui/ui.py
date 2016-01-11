# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging

import deluge.common
import deluge.configmanager
import deluge.log
from deluge.ui.baseargparser import BaseArgParser

log = logging.getLogger(__name__)

try:
    from setproctitle import setproctitle
except ImportError:
    def setproctitle(title):
        return

if 'dev' not in deluge.common.get_version():
    import warnings
    warnings.filterwarnings('ignore', category=DeprecationWarning, module='twisted')


class UI(object):

    def __init__(self, name="gtk", parser=None):
        self.__name = name
        self.__parser = parser if parser else BaseArgParser()
        deluge.common.setup_translations(setup_pygtk=(name == "gtk"))

    def parse_args(self, args=None):
        options = self.parser.parse_args(args)
        if not hasattr(options, "remaining"):
            options.remaining = []
        return options

    @property
    def name(self):
        return self.__name

    @property
    def parser(self):
        return self.__parser

    @property
    def options(self):
        return self.__options

    def start(self, extra_args=None):
        args = deluge.common.unicode_argv()[1:]
        if extra_args:
            args.extend(extra_args)

        self.__options = self.parse_args(args)

        setproctitle("deluge-%s" % self.__name)

        log.info("Deluge ui %s", deluge.common.get_version())
        log.debug("options: %s", self.__options)
        log.info("Starting %s ui..", self.__name)
