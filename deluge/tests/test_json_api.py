# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 bendikro <bro.devel+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

from __future__ import unicode_literals

import json as json_lib

from mock import MagicMock
from twisted.internet import defer
from twisted.web import server
from twisted.web.http import Request

import deluge.common
import deluge.component as component
import deluge.ui.web.auth
import deluge.ui.web.json_api
from deluge.error import DelugeError
from deluge.ui.client import client
from deluge.ui.web.auth import Auth
from deluge.ui.web.json_api import JSON, JSONException

from . import common
from .basetest import BaseTestCase
from .common_web import WebServerMockBase
from .daemon_base import DaemonBase

common.disable_new_release_check()


class JSONBase(BaseTestCase, DaemonBase):
    def connect_client(self, *args, **kwargs):
        return client.connect(
            'localhost',
            self.listen_port,
            username=kwargs.get('user', ''),
            password=kwargs.get('password', ''),
        )

    def disconnect_client(self, *args):
        return client.disconnect()

    def tear_down(self):
        d = component.shutdown()
        d.addCallback(self.disconnect_client)
        d.addCallback(self.terminate_core)
        return d


class JSONTestCase(JSONBase):
    def set_up(self):
        d = self.common_set_up()
        d.addCallback(self.start_core)
        d.addCallbacks(self.connect_client, self.terminate_core)
        return d

    @defer.inlineCallbacks
    def test_get_remote_methods(self):
        json = JSON()
        methods = yield json.get_remote_methods()
        self.assertEqual(type(methods), tuple)
        self.assertTrue(len(methods) > 0)

    def test_render_fail_disconnected(self):
        json = JSON()
        request = MagicMock()
        request.method = b'POST'
        request._disconnected = True
        # When disconnected, returns empty string
        self.assertEqual(json.render(request), '')

    def test_render_fail(self):
        json = JSON()
        request = MagicMock()
        request.method = b'POST'

        def write(response_str):
            request.write_was_called = True
            response = json_lib.loads(response_str.decode())
            self.assertEqual(response['result'], None)
            self.assertEqual(response['id'], None)
            self.assertEqual(
                response['error']['message'], 'JSONException: JSON not decodable'
            )
            self.assertEqual(response['error']['code'], 5)

        request.write = write
        request.write_was_called = False
        request._disconnected = False
        request.getHeader.return_value = b'application/json'
        self.assertEqual(json.render(request), server.NOT_DONE_YET)
        self.assertTrue(request.write_was_called)

    def test_handle_request_invalid_method(self):
        json = JSON()
        request = MagicMock()
        json_data = {'method': 'no-existing-module.test', 'id': 0, 'params': []}
        request.json = json_lib.dumps(json_data).encode()
        request_id, result, error = json._handle_request(request)
        self.assertEqual(error, {'message': 'Unknown method', 'code': 2})

    def test_handle_request_invalid_json_request(self):
        json = JSON()
        request = MagicMock()
        json_data = {'id': 0, 'params': []}
        request.json = json_lib.dumps(json_data).encode()
        self.assertRaises(JSONException, json._handle_request, request)
        json_data = {'method': 'some.method', 'params': []}
        request.json = json_lib.dumps(json_data).encode()
        self.assertRaises(JSONException, json._handle_request, request)
        json_data = {'method': 'some.method', 'id': 0}
        request.json = json_lib.dumps(json_data).encode()
        self.assertRaises(JSONException, json._handle_request, request)

    def test_on_json_request_invalid_content_type(self):
        """Test for exception with content type not application/json"""
        json = JSON()
        request = MagicMock()
        request.getHeader.return_value = b'text/plain'
        json_data = {'method': 'some.method', 'id': 0, 'params': []}
        request.json = json_lib.dumps(json_data).encode()
        self.assertRaises(JSONException, json._on_json_request, request)


class JSONCustomUserTestCase(JSONBase):
    def set_up(self):
        d = self.common_set_up()
        d.addCallback(self.start_core)
        return d

    @defer.inlineCallbacks
    def test_handle_request_auth_error(self):
        yield self.connect_client()
        json = JSON()
        auth_conf = {'session_timeout': 10, 'sessions': {}}
        Auth(auth_conf)  # Must create the component

        # Must be called to update remote methods in json object
        yield json.get_remote_methods()

        request = MagicMock()
        request.getCookie = MagicMock(return_value=b'bad_value')
        json_data = {'method': 'core.get_libtorrent_version', 'id': 0, 'params': []}
        request.json = json_lib.dumps(json_data).encode()
        request_id, result, error = json._handle_request(request)
        self.assertEqual(error, {'message': 'Not authenticated', 'code': 1})


class RPCRaiseDelugeErrorJSONTestCase(JSONBase):
    def set_up(self):
        d = self.common_set_up()
        custom_script = """
    from deluge.error import DelugeError
    from deluge.core.rpcserver import export
    class TestClass(object):
        @export()
        def test(self):
            raise DelugeError('DelugeERROR')

    test = TestClass()
    daemon.rpcserver.register_object(test)
"""
        d.addCallback(self.start_core, custom_script=custom_script)
        d.addCallbacks(self.connect_client, self.terminate_core)
        return d

    @defer.inlineCallbacks
    def test_handle_request_method_raise_delugeerror(self):
        json = JSON()

        def get_session_id(s_id):
            return s_id

        self.patch(deluge.ui.web.auth, 'get_session_id', get_session_id)
        auth_conf = {'session_timeout': 10, 'sessions': {}}
        auth = Auth(auth_conf)
        request = Request(MagicMock(), False)
        request.base = b''
        auth._create_session(request)
        methods = yield json.get_remote_methods()
        # Verify the function has been registered
        self.assertTrue('testclass.test' in methods)

        request = MagicMock()
        session_id = list(auth.config['sessions'])[0]
        request.getCookie = MagicMock(return_value=session_id.encode())
        json_data = {'method': 'testclass.test', 'id': 0, 'params': []}
        request.json = json_lib.dumps(json_data).encode()
        request_id, result, error = json._handle_request(request)
        result.addCallback(self.fail)

        def on_error(error):
            self.assertEqual(error.type, DelugeError)

        result.addErrback(on_error)
        yield result


class JSONRequestFailedTestCase(JSONBase, WebServerMockBase):
    def set_up(self):
        d = self.common_set_up()
        custom_script = """
    from deluge.error import DelugeError
    from deluge.core.rpcserver import export
    from twisted.internet import reactor, task
    class TestClass(object):
        @export()
        def test(self):
            def test_raise_error():
                raise DelugeError('DelugeERROR')

            return task.deferLater(reactor, 1, test_raise_error)

    test = TestClass()
    daemon.rpcserver.register_object(test)
"""
        from twisted.internet.defer import Deferred

        extra_callback = {
            'deferred': Deferred(),
            'types': ['stderr'],
            'timeout': 10,
            'triggers': [
                {
                    'expr': 'in test_raise_error',
                    'value': lambda reader, data, data_all: 'Test',
                }
            ],
        }

        def on_test_raise(*args):
            self.assertTrue('Unhandled error in Deferred:' in self.core.stderr_out)
            self.assertTrue('in test_raise_error' in self.core.stderr_out)

        extra_callback['deferred'].addCallback(on_test_raise)
        d.addCallback(
            self.start_core,
            custom_script=custom_script,
            print_stdout=False,
            print_stderr=False,
            timeout=5,
            extra_callbacks=[extra_callback],
        )
        d.addCallbacks(self.connect_client, self.terminate_core)
        return d

    @defer.inlineCallbacks
    def test_render_on_rpc_request_failed(self):
        json = JSON()

        methods = yield json.get_remote_methods()
        # Verify the function has been registered
        self.assertTrue('testclass.test' in methods)

        request = MagicMock()

        # Circumvent authentication
        auth = Auth({})
        self.mock_authentication_ignore(auth)

        def write(response_str):
            request.write_was_called = True
            response = json_lib.loads(response_str.decode())
            self.assertEqual(response['result'], None, 'BAD RESULT')
            self.assertEqual(response['id'], 0)
            self.assertEqual(
                response['error']['message'],
                'Failure: [Failure instance: Traceback (failure with no frames):'
                " <class 'deluge.error.DelugeError'>: DelugeERROR\n]",
            )
            self.assertEqual(response['error']['code'], 4)

        request.write = write
        request.write_was_called = False
        request._disconnected = False
        request.getHeader.return_value = b'application/json'
        json_data = {'method': 'testclass.test', 'id': 0, 'params': []}
        request.json = json_lib.dumps(json_data).encode()
        d = json._on_json_request(request)

        def on_success(arg):
            self.assertEqual(arg, server.NOT_DONE_YET)
            return True

        d.addCallbacks(on_success, self.fail)
        yield d
