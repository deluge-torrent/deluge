#! /usr/bin/env python

from twisted.plugin import IPlugin
from twisted.trial.itrial import IReporter
from twisted.trial.reporter import TreeReporter
from zope.interface import implements


class _Reporter(object):
    implements(IPlugin, IReporter)

    def __init__(self, name, module, description, longOpt, shortOpt, klass):  # NOQA
        self.name = name
        self.module = module
        self.description = description
        self.longOpt = longOpt
        self.shortOpt = shortOpt
        self.klass = klass

deluge = _Reporter("Deluge reporter that suppresses Stacktrace from TODO tests",
                   "twisted.plugins.delugereporter",
                   description="Deluge Reporter",
                   longOpt="deluge-reporter",
                   shortOpt=None,
                   klass="DelugeReporter")


class DelugeReporter(TreeReporter):

    def __init__(self, *args, **kwargs):
        TreeReporter.__init__(self, *args, **kwargs)

    def addExpectedFailure(self, *args):  # NOQA
        # super(TreeReporter, self).addExpectedFailure(*args)
        self.endLine('[TODO]', self.TODO)
