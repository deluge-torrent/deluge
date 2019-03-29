#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import os

from twisted.plugin import IPlugin
from twisted.trial.itrial import IReporter
from twisted.trial.reporter import TreeReporter
from zope.interface import implements


class _Reporter(object):
    implements(IPlugin, IReporter)

    def __init__(
        self, name, module, description, longOpt, shortOpt, klass  # noqa: N803
    ):
        self.name = name
        self.module = module
        self.description = description
        self.longOpt = longOpt
        self.shortOpt = shortOpt
        self.klass = klass


deluge = _Reporter(
    'Deluge reporter that suppresses Stacktrace from TODO tests',
    'twisted.plugins.delugereporter',
    description='Deluge Reporter',
    longOpt='deluge-reporter',
    shortOpt=None,
    klass='DelugeReporter',
)


class DelugeReporter(TreeReporter):
    def __init__(self, *args, **kwargs):
        os.environ['DELUGE_REPORTER'] = 'true'
        TreeReporter.__init__(self, *args, **kwargs)

    def addExpectedFailure(self, *args):  # NOQA: N802
        # super(TreeReporter, self).addExpectedFailure(*args)
        self.endLine('[TODO]', self.TODO)
