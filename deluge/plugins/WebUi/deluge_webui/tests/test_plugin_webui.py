#
# Copyright (C) 2016 bendikro <bro.devel+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
import pytest
import pytest_twisted

from deluge.core.core import Core
from deluge.core.rpcserver import RPCServer
from deluge.tests import common

common.disable_new_release_check()


class TestWebUIPlugin:
    @pytest_twisted.async_yield_fixture(autouse=True)
    async def set_up(self, request, component):
        self = request.instance
        self.rpcserver = RPCServer(listen=False)
        self.core = Core()
        await component.start()

        yield

        await component.shutdown()
        del self.rpcserver
        del self.core

    def test_enable_webui(self):
        if 'WebUi' not in self.core.get_available_plugins():
            pytest.skip('WebUi plugin not available for testing')

        d = self.core.enable_plugin('WebUi')

        def result_cb(result):
            if 'WebUi' not in self.core.get_enabled_plugins():
                self.fail('Failed to enable WebUi plugin')
            assert result

        d.addBoth(result_cb)
        return d
