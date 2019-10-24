# -*- coding: utf-8 -*-
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import print_function, unicode_literals

import os.path

import pytest
from twisted.internet import defer
from twisted.internet.error import CannotListenError

import deluge.component as component
from deluge.common import windows_check

from . import common


@pytest.mark.usefixtures('get_pytest_basetemp')
class DaemonBase(object):
    basetemp = None

    if windows_check():
        skip = 'windows cant start_core not enough arguments for format string'

    @pytest.fixture
    def get_pytest_basetemp(self, request):
        self.basetemp = request.config.option.basetemp

    def common_set_up(self):
        common.set_tmp_config_dir()
        self.listen_port = 58900
        self.core = None
        return component.start()

    def terminate_core(self, *args):
        if args[0] is not None:
            if hasattr(args[0], 'getTraceback'):
                print('terminate_core: Errback Exception: %s' % args[0].getTraceback())

        if not self.core.killed:
            d = self.core.kill()
            return d

    @defer.inlineCallbacks
    def start_core(
        self,
        arg,
        custom_script='',
        logfile='',
        print_stdout=True,
        print_stderr=True,
        timeout=5,
        port_range=10,
        extra_callbacks=None,
    ):
        if logfile == '':
            logfile = 'daemon_%s.log' % self.id()

        # We are running py.test
        if hasattr(pytest, 'config'):
            if self.basetemp:
                if not os.path.exists(self.basetemp):
                    os.makedirs(self.basetemp)
                logfile = os.path.join(self.basetemp, logfile)

        for dummy in range(port_range):
            try:
                d, self.core = common.start_core(
                    listen_port=self.listen_port,
                    logfile=logfile,
                    timeout=timeout,
                    timeout_msg='Timeout!',
                    custom_script=custom_script,
                    print_stdout=print_stdout,
                    print_stderr=print_stderr,
                    extra_callbacks=extra_callbacks,
                )
                yield d
            except CannotListenError as ex:
                exception_error = ex
                self.listen_port += 1
            except (KeyboardInterrupt, SystemExit):
                raise
            else:
                return
        raise exception_error
