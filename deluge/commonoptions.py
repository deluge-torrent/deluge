# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import logging
import optparse
import os
import platform
import sys

import deluge.common
import deluge.configmanager
from deluge.log import setup_logger


def version_callback(option, opt_str, value, parser):
    print(os.path.basename(sys.argv[0]) + ": " + deluge.common.get_version())
    try:
        from deluge._libtorrent import lt
        print("libtorrent: %s" % lt.version)
    except ImportError:
        pass
    print("Python: %s" % platform.python_version())
    for version in (platform.linux_distribution(), platform.win32_ver(), platform.mac_ver(), ("n/a",)):
        if filter(None, version):  # pylint: disable=bad-builtin
            print("OS: %s %s" % (platform.system(), " ".join(version)))
            break
    raise SystemExit


class CommonOptionParser(optparse.OptionParser):
    def __init__(self, *args, **kwargs):
        optparse.OptionParser.__init__(self, *args, **kwargs)
        self.common_group = optparse.OptionGroup(self, _("Common Options"))
        self.common_group.add_option("-v", "--version", action="callback", callback=version_callback,
                                     help="Show program's version number and exit")
        self.common_group.add_option("-c", "--config", dest="config", action="store", type="str",
                                     help="Set the config folder location")
        self.common_group.add_option("-l", "--logfile", dest="logfile", action="store", type="str",
                                     help="Output to designated logfile instead of stdout")
        self.common_group.add_option("-L", "--loglevel", dest="loglevel", action="store", type="str",
                                     help="Set the log level: none, info, warning, error, critical, debug")
        self.common_group.add_option("-q", "--quiet", dest="quiet", action="store_true", default=False,
                                     help="Sets the log level to 'none', this is the same as `-L none`")
        self.common_group.add_option("-r", "--rotate-logs", action="store_true", default=False,
                                     help="Rotate logfiles.")
        self.add_option_group(self.common_group)

    def parse_args(self, *args):
        options, args = optparse.OptionParser.parse_args(self, *args)

        # Setup the logger
        if options.quiet:
            options.loglevel = "none"
        if options.loglevel:
            options.loglevel = options.loglevel.lower()

        logfile_mode = 'w'
        if options.rotate_logs:
            logfile_mode = 'a'

        # Setup the logger
        setup_logger(level=options.loglevel, filename=options.logfile, filemode=logfile_mode)

        if options.config:
            if not deluge.configmanager.set_config_dir(options.config):
                log = logging.getLogger(__name__)
                log.error("There was an error setting the config dir! Exiting..")
                sys.exit(1)
        else:
            if not os.path.exists(deluge.common.get_default_config_dir()):
                os.makedirs(deluge.common.get_default_config_dir())

        return options, args
