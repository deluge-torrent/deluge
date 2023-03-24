#
# Copyright (C) 2016 bendikro <bro.devel+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import json as json_lib
from io import BytesIO

import pytest
import twisted.web.client
from twisted.internet import reactor
from twisted.web.client import Agent, FileBodyProducer
from twisted.web.http_headers import Headers

from . import common
from .common import get_test_data_file
from .common_web import WebServerMockBase, WebServerTestBase

common.disable_new_release_check()


class TestWebServer(WebServerTestBase, WebServerMockBase):
    async def test_get_torrent_info(self):
        agent = Agent(reactor)

        self.mock_authentication_ignore(self.deluge_web.auth)

        # This torrent file contains an uncommon field 'filehash' which must be hex
        # encoded to allow dumping the torrent info to json. Otherwise it will fail with:
        # UnicodeDecodeError: 'utf8' codec can't decode byte 0xe5 in position 0: invalid continuation byte
        filename = get_test_data_file('filehash_field.torrent')
        input_file = (
            '{"params": ["%s"], "method": "web.get_torrent_info", "id": 22}'
            % filename.replace('\\', '\\\\')
        )
        headers = {
            b'User-Agent': ['Twisted Web Client Example'],
            b'Content-Type': ['application/json'],
        }
        url = 'http://127.0.0.1:%s/json' % self.deluge_web.port

        response = await agent.request(
            b'POST',
            url.encode(),
            Headers(headers),
            FileBodyProducer(BytesIO(input_file.encode())),
        )
        body = await twisted.web.client.readBody(response)

        try:
            json = json_lib.loads(body.decode())
        except Exception:
            print('aoeu')
        assert json['error'] is None
        assert 'torrent_filehash' == json['result']['name']

    @pytest.mark.parametrize('base', ['', '/', 'deluge'])
    async def test_base_with_config(self, base):
        agent = Agent(reactor)
        root_url = f'http://127.0.0.1:{self.deluge_web.port}'
        base_url = f'{root_url}/{base}'

        self.deluge_web.base = base

        response = await agent.request(b'GET', root_url.encode())
        assert response.code == 200
        body = await twisted.web.client.readBody(response)
        assert 'Deluge WebUI' in body.decode()

        response = await agent.request(b'GET', base_url.encode())
        assert response.code == 200

    @pytest.mark.parametrize('base', ['/', 'deluge'])
    async def test_base_with_config_recurring_basepath(self, base):
        agent = Agent(reactor)
        base_url = f'http://127.0.0.1:{self.deluge_web.port}/{base}'

        self.deluge_web.base = base

        response = await agent.request(b'GET', base_url.encode())
        assert response.code == 200

        recursive_url = f'{base_url}/{base}'
        response = await agent.request(b'GET', recursive_url.encode())
        assert response.code == 404 if base.strip('/') else 200

        recursive_url = f'{recursive_url}/{base}'
        response = await agent.request(b'GET', recursive_url.encode())
        assert response.code == 404 if base.strip('/') else 200

    async def test_base_with_deluge_header(self):
        """Ensure base path is set and HTML contains path"""
        agent = Agent(reactor)
        base = 'deluge'
        url = f'http://127.0.0.1:{self.deluge_web.port}'
        headers = Headers({'X-Deluge-Base': [base]})

        response = await agent.request(b'GET', url.encode(), headers)
        body = await twisted.web.client.readBody(response)
        assert f'href="/{base}/' in body.decode()

        # Header only changes HTML base path so ensure no resource at server path
        url = f'{url}/{base}'
        response = await agent.request(b'GET', url.encode(), headers)
        assert response.code == 404
