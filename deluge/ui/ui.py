# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import logging

import deluge.common
import deluge.configmanager
import deluge.log
from deluge.argparserbase import ArgParserBase
from deluge.i18n import setup_translation

log = logging.getLogger(__name__)

try:
    from setproctitle import setproctitle
except ImportError:

    def setproctitle(title):
        return


class UI(object):
    """
    Base class for UI implementations.

    """

    cmd_description = """Override with command description"""

    def __init__(self, name, **kwargs):
        self.__name = name
        self.ui_args = kwargs.pop('ui_args', None)
        setup_translation()
        self.__parser = ArgParserBase(**kwargs)

    def parse_args(self, parser, args=None):
        options = parser.parse_args(args)
        if not hasattr(options, 'remaining'):
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

    def start(self, parser=None):
        args = deluge.common.unicode_argv()[1:]
        if parser is None:
            parser = self.parser
        self.__options = self.parse_args(parser, args)

        setproctitle('deluge-%s' % self.__name)

        log.info('Deluge ui %s', deluge.common.get_version())
        log.debug('options: %s', self.__options)
        log.info('Starting %s ui..', self.__name)
