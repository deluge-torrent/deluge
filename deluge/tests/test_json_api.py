# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 bendikro <bro.devel+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import json as json_lib

from mock import MagicMock
from twisted.internet import base, defer
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

base.DelayedCall.debug = True


class JSONBase(BaseTestCase, DaemonBase):

    def connect_client(self, *args, **kwargs):
        return client.connect(
            'localhost', self.listen_port, username=kwargs.get('user', ''),
            password=kwargs.get('password', '')
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
        self.assertEquals(type(methods), tuple)
        self.assertTrue(len(methods) > 0)

    def test_render_fail_disconnected(self):
        json = JSON()
        request = MagicMock()
        request.method = 'POST'
        request._disconnected = True
        # When disconnected, returns empty string
        self.assertEquals(json.render(request), '')

    def test_render_fail(self):
        json = JSON()
        request = MagicMock()
        request.method = 'POST'

        def compress(contents, request):
            return contents
        self.patch(deluge.ui.web.json_api, 'compress', compress)

        def write(response_str):
            request.write_was_called = True
            response = json_lib.loads(response_str)
            self.assertEquals(response['result'], None)
            self.assertEquals(response['id'], None)
            self.assertEquals(response['error']['message'], 'JSONException: JSON not decodable')
            self.assertEquals(response['error']['code'], 5)

        request.write = write
        request.write_was_called = False
        request._disconnected = False
        self.assertEquals(json.render(request), server.NOT_DONE_YET)
        self.assertTrue(request.write_was_called)

    def test_handle_request_invalid_method(self):
        json = JSON()
        request = MagicMock()
        json_data = {'method': 'no-existing-module.test', 'id': 0, 'params': []}
        request.json = json_lib.dumps(json_data)
        request_id, result, error = json._handle_request(request)
        self.assertEquals(error, {'message': 'Unknown method', 'code': 2})

    def test_handle_request_invalid_json_request(self):
        json = JSON()
        request = MagicMock()
        request.json = json_lib.dumps({'id': 0, 'params': []})
        self.assertRaises(JSONException, json._handle_request, request)
        request.json = json_lib.dumps({'method': 'some.method', 'params': []})
        self.assertRaises(JSONException, json._handle_request, request)
        request.json = json_lib.dumps({'method': 'some.method', 'id': 0})
        self.assertRaises(JSONException, json._handle_request, request)


class JSONCustomUserTestCase(JSONBase):

    def set_up(self):
        d = self.common_set_up()
        d.addCallback(self.start_core)
        return d

    @defer.inlineCallbacks
    def test_handle_request_auth_error(self):
        yield self.connect_client()
        json = JSON()
        auth_conf = {'session_timeout': 10, 'sessions': []}
        Auth(auth_conf)  # Must create the component

        # Must be called to update remote methods in json object
        yield json.get_remote_methods()

        request = MagicMock()
        request.getCookie = MagicMock(return_value='bad_value')
        json_data = {'method': 'core.get_libtorrent_version', 'id': 0, 'params': []}
        request.json = json_lib.dumps(json_data)
        request_id, result, error = json._handle_request(request)
        self.assertEquals(error, {'message': 'Not authenticated', 'code': 1})


class RPCRaiseDelugeErrorJSONTestCase(JSONBase):

    def set_up(self):
        d = self.common_set_up()
        custom_script = """
    from deluge.error import DelugeError
    from deluge.core.rpcserver import export
    class TestClass(object):
        @export()
        def test(self):
            raise DelugeError("DelugeERROR")

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
        auth_conf = {'session_timeout': 10, 'sessions': []}
        auth = Auth(auth_conf)
        request = Request(MagicMock(), False)
        request.base = ''
        auth._create_session(request)
        methods = yield json.get_remote_methods()
        # Verify the function has been registered
        self.assertTrue('testclass.test' in methods)

        request = MagicMock()
        request.getCookie = MagicMock(return_value=auth.config['sessions'].keys()[0])
        json_data = {'method': 'testclass.test', 'id': 0, 'params': []}
        request.json = json_lib.dumps(json_data)
        request_id, result, error = json._handle_request(request)
        result.addCallback(self.fail)

        def on_error(error):
            self.assertEquals(error.type, DelugeError)
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
                raise DelugeError("DelugeERROR")

            return task.deferLater(reactor, 1, test_raise_error)

    test = TestClass()
    daemon.rpcserver.register_object(test)
"""
        from twisted.internet.defer import Deferred
        extra_callback = {'deferred': Deferred(), 'types': ['stderr'],
                          'timeout': 10,
                          'triggers': [{'expr': 'in test_raise_error',
                                        'value': lambda reader, data, data_all: 'Test'}]}

        def on_test_raise(*args):
            self.assertTrue('Unhandled error in Deferred:' in self.core.stderr_out)
            self.assertTrue('in test_raise_error' in self.core.stderr_out)

        extra_callback['deferred'].addCallback(on_test_raise)
        d.addCallback(self.start_core, custom_script=custom_script, print_stderr=False,
                      timeout=5, extra_callbacks=[extra_callback])
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
        self.mock_compress_body()

        def write(response_str):
            request.write_was_called = True
            response = json_lib.loads(response_str)
            self.assertEquals(response['result'], None, 'BAD RESULT')
            self.assertEquals(response['id'], 0)
            self.assertEquals(response['error']['message'],
                              'Failure: [Failure instance: Traceback (failure with no frames):'
                              " <class 'deluge.error.DelugeError'>: DelugeERROR\n]")
            self.assertEquals(response['error']['code'], 4)

        request.write = write
        request.write_was_called = False
        request._disconnected = False
        json_data = {'method': 'testclass.test', 'id': 0, 'params': []}
        request.json = json_lib.dumps(json_data)
        d = json._on_json_request(request)

        def on_success(arg):
            self.assertEquals(arg, server.NOT_DONE_YET)
            return True
        d.addCallbacks(on_success, self.fail)
        yield d
