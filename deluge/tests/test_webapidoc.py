# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 bendikro <bro.devel+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import sys

import twisted.web.client
import twisted.web.http
from twisted.internet import defer, reactor
from twisted.web.client import Agent, RedirectAgent
from twisted.web.http_headers import Headers

from deluge.ui.web.auth import Auth
from deluge.ui.web.json_api import JSON, WebApi, WebUtils
from deluge.ui.web.webapidoc.openapi_builder import OpenAPISpecBuilder

from . import common
from .basetest import BaseTestCase
from .common_web import WebServerMockBase, WebServerTestBase

common.disable_new_release_check()


class WebapiDocsSpecTestCase(BaseTestCase):
    def set_up(self):
        self.json = JSON()
        self.web_utils = WebUtils()
        self.web_api = WebApi()
        auth_conf = {'session_timeout': 10, 'sessions': {}}
        self.auth = Auth(auth_conf)
        self.spec_builder = OpenAPISpecBuilder(self.json, 'api')
        self.spec = self.spec_builder.build_spec()

    def test_webapidocs_spec(self):
        endpoints = self.spec['paths'].keys()

        for endpoint in [
            '/json',
            '/api/webutils/get_languages',
            '/api/web/add_host',
            '/api/web/add_torrents',
            '/api/web/connect',
            '/api/web/connected',
            '/api/web/deregister_event_listener',
            '/api/web/disconnect',
            '/api/web/download_torrent_from_url',
            '/api/web/edit_host',
            '/api/web/get_config',
            '/api/web/get_events',
            '/api/web/get_host_status',
            '/api/web/get_hosts',
            '/api/web/get_magnet_info',
            '/api/web/get_methods',
            '/api/web/get_plugin_info',
            '/api/web/get_plugin_resources',
            '/api/web/get_plugins',
            '/api/web/get_torrent_files',
            '/api/web/get_torrent_info',
            '/api/web/get_torrent_status',
            '/api/web/register_event_listener',
            '/api/web/remove_host',
            '/api/web/set_config',
            '/api/web/start_daemon',
            '/api/web/stop_daemon',
            '/api/web/update_ui',
            '/api/web/upload_plugin',
        ]:
            self.assertIn(endpoint, endpoints)

        self.assertEqual('Deluge Webapi', self.spec['info']['title'])

    def test_webapidocs_spec_json_api_get_torrent_info(self):
        """
        Test the output of the parsed function documentation for json_api.py:get_torrent_info

        """
        get_torrent_info = self.spec['paths']['/api/web/get_torrent_info']

        self.assertEqual('Not used...', get_torrent_info['description'])

        param_id = {
            'name': 'id',
            'in': 'query',
            'required': False,
            'schema': {'type': 'string', 'example': '1'},
        }
        param_pretty = {
            'name': 'pretty',
            'in': 'query',
            'required': False,
            'schema': {'type': 'string', 'example': 'pretty'},
        }
        param_func = {
            'name': 'params',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'array',
                'items': {},
                'example': {'params': ['filename']},
            },
        }

        # parameters
        self.assertIn(param_id, get_torrent_info['parameters'])
        self.assertIn(param_pretty, get_torrent_info['parameters'])
        self.assertIn(param_func, get_torrent_info['parameters'])

        # post
        expected_description = 'Return information about a torrent on the filesystem.'
        if (sys.version_info.major, sys.version_info.minor) < (3, 6):
            expected_description = 'Description for web/get_torrent_info'

        self.assertEqual(expected_description, get_torrent_info['post']['description'])
        self.assertEqual(
            (
                'result (dict): information about the torrent\n::\n'
                '{\n    "name": the torrent name,\n'
                '    "files_tree": the files the torrent contains,\n'
                '    "info_hash" the torrents info_hash\n}'
            ),
            get_torrent_info['post']['responses']['200']['description'],
        )

        self.assertEqual(
            {
                'application/json': {
                    'schema': {'type': 'dict', 'items': {}},
                    'example': {'result': None, 'error': None, 'id': 1},
                }
            },
            get_torrent_info['post']['responses']['200']['content'],
        )
        self.assertEqual(
            'web.get_torrent_info', get_torrent_info['post']['operationId']
        )
        self.assertEqual(['torrents'], get_torrent_info['post']['tags'])
        self.assertEqual(
            {
                'description': "The request body for 'web.get_torrent_info'",
                'required': True,
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'array',
                            'items': {},
                            'example': {'params': ['filename']},
                        }
                    }
                },
            },
            get_torrent_info['post']['requestBody'],
        )


class WebApiDocServerTestCase(WebServerTestBase, WebServerMockBase):

    headers = {
        b'User-Agent': ['Twisted Web Client Example'],
        b'Content-Type': ['text/html'],
    }

    def set_up(self):
        d = super().set_up()
        return d

    @defer.inlineCallbacks
    def test_webapidocs(self):
        agent = Agent(reactor)
        agent = RedirectAgent(agent)
        url = 'http://127.0.0.11:%s/webapidoc' % self.webserver_listen_port
        d = yield agent.request(b'GET', url.encode('utf-8'), Headers(self.headers))
        self.assertEqual(['text/html'], d.headers.getRawHeaders('content-type'))
        body = yield twisted.web.client.readBody(d)
        resp = body.decode()
        self.assertIn('url: "/api/openapi.json",', resp)

    @defer.inlineCallbacks
    def test_webapidocs_index(self):
        agent = Agent(reactor)
        url = 'http://127.0.0.11:%s/webapidoc/index.html' % self.webserver_listen_port
        d = yield agent.request(b'GET', url.encode('utf-8'), Headers(self.headers))
        self.assertEqual(twisted.web.http.OK, d.code)

    @defer.inlineCallbacks
    def test_webapidocs_index_redirect(self):
        agent = Agent(reactor)
        url = 'http://127.0.0.11:%s/webapidoc' % self.webserver_listen_port
        d = yield agent.request(b'GET', url.encode('utf-8'), Headers(self.headers))
        # FOUND (302) == redirect
        self.assertEqual(twisted.web.http.FOUND, d.code)
