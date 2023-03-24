#
# Copyright (C) 2016 bendikro <bro.devel+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import json as json_lib
from unittest.mock import MagicMock

import pytest
import pytest_twisted
from twisted.internet.defer import Deferred
from twisted.web import server
from twisted.web.http import Request

import deluge.common
import deluge.ui.web.auth
import deluge.ui.web.json_api
from deluge.error import DelugeError
from deluge.ui.web.auth import Auth
from deluge.ui.web.json_api import JSON, JSONException

from . import common
from .common_web import WebServerMockBase

common.disable_new_release_check()


@pytest.mark.usefixtures('daemon', 'client', 'component')
class TestJSON:
    async def test_get_remote_methods(self):
        json = JSON()
        methods = await json.get_remote_methods()
        assert type(methods) == tuple
        assert len(methods) > 0

    def test_render_fail_disconnected(self):
        json = JSON()
        request = MagicMock()
        request.method = b'POST'
        request._disconnected = True
        # When disconnected, returns empty string
        assert json.render(request) == ''

    def test_render_fail(self):
        json = JSON()
        request = MagicMock()
        request.method = b'POST'

        def write(response_str):
            request.write_was_called = True
            response = json_lib.loads(response_str.decode())
            assert response['result'] is None
            assert response['id'] is None
            assert response['error']['message'] == 'JSONException: JSON not decodable'
            assert response['error']['code'] == 5

        request.write = write
        request.write_was_called = False
        request._disconnected = False
        request.getHeader.return_value = b'application/json'
        assert json.render(request) == server.NOT_DONE_YET
        assert request.write_was_called

    def test_handle_request_invalid_method(self):
        json = JSON()
        request = MagicMock()
        json_data = {'method': 'no-existing-module.test', 'id': 0, 'params': []}
        request.json = json_lib.dumps(json_data).encode()
        request_id, result, error = json._handle_request(request)
        assert error == {'message': 'Unknown method', 'code': 2}

    def test_handle_request_invalid_json_request(self):
        json = JSON()
        request = MagicMock()
        json_data = {'id': 0, 'params': []}
        request.json = json_lib.dumps(json_data).encode()
        with pytest.raises(JSONException):
            json._handle_request(request)
        json_data = {'method': 'some.method', 'params': []}
        request.json = json_lib.dumps(json_data).encode()
        with pytest.raises(JSONException):
            json._handle_request(request)
        json_data = {'method': 'some.method', 'id': 0}
        request.json = json_lib.dumps(json_data).encode()
        with pytest.raises(JSONException):
            json._handle_request(request)

    def test_on_json_request_invalid_content_type(self):
        """Test for exception with content type not application/json"""
        json = JSON()
        request = MagicMock()
        request.getHeader.return_value = b'text/plain'
        json_data = {'method': 'some.method', 'id': 0, 'params': []}
        request.json = json_lib.dumps(json_data).encode()
        with pytest.raises(JSONException):
            json._on_json_request(request)

    def test_on_json_request_valid_content_type(self):
        """Ensure content-type application/json is accepted"""
        json = JSON()
        request = MagicMock()
        request.getHeader.return_value = b'application/json'
        json_data = {'method': 'some.method', 'id': 0, 'params': []}
        request.json = json_lib.dumps(json_data).encode()
        json._on_json_request(request)

    def test_on_json_request_valid_content_type_with_charset(self):
        """Ensure content-type parameters such as charset are ignored"""
        json = JSON()
        request = MagicMock()
        request.getHeader.return_value = b'application/json;charset=utf-8'
        json_data = {'method': 'some.method', 'id': 0, 'params': []}
        request.json = json_lib.dumps(json_data).encode()
        json._on_json_request(request)


@pytest.mark.usefixtures('daemon', 'client', 'component')
class TestJSONCustomUserTestCase:
    @pytest_twisted.inlineCallbacks
    def test_handle_request_auth_error(self):
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
        assert error == {'message': 'Not authenticated', 'code': 1}


@pytest.mark.usefixtures('daemon', 'client', 'component')
class TestRPCRaiseDelugeErrorJSON:
    daemon_custom_script = """
    from deluge.error import DelugeError
    from deluge.core.rpcserver import export
    class TestClass(object):
        @export()
        def test(self):
            raise DelugeError('DelugeERROR')

    test = TestClass()
    daemon.rpcserver.register_object(test)
"""

    async def test_handle_request_method_raise_delugeerror(self):
        json = JSON()

        def get_session_id(s_id):
            return s_id

        self.patch(deluge.ui.web.auth, 'get_session_id', get_session_id)
        auth_conf = {'session_timeout': 10, 'sessions': {}}
        auth = Auth(auth_conf)
        request = Request(MagicMock(), False)
        request.base = b''
        auth._create_session(request)
        methods = await json.get_remote_methods()
        # Verify the function has been registered
        assert 'testclass.test' in methods

        request = MagicMock()
        session_id = list(auth.config['sessions'])[0]
        request.getCookie = MagicMock(return_value=session_id.encode())
        json_data = {'method': 'testclass.test', 'id': 0, 'params': []}
        request.json = json_lib.dumps(json_data).encode()
        request_id, result, error = json._handle_request(request)
        with pytest.raises(DelugeError):
            await result


class TestJSONRequestFailed(WebServerMockBase):
    @pytest_twisted.async_yield_fixture(autouse=True)
    async def set_up(self, config_dir):
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
            assert 'Unhandled error in Deferred:' in daemon.stderr_out
            assert 'in test_raise_error' in daemon.stderr_out

        d, daemon = common.start_core(
            custom_script=custom_script,
            print_stdout=True,
            print_stderr=False,
            timeout=5,
            extra_callbacks=[extra_callback],
            config_directory=config_dir,
        )
        extra_callback['deferred'].addCallback(on_test_raise, daemon)

        await d
        yield
        await daemon.kill()

    @pytest_twisted.inlineCallbacks
    def test_render_on_rpc_request_failed(self, component, client):
        json = JSON()

        methods = yield json.get_remote_methods()
        # Verify the function has been registered
        assert 'testclass.test' in methods

        request = MagicMock()

        # Circumvent authentication
        auth = Auth({})
        self.mock_authentication_ignore(auth)

        def write(response_str):
            request.write_was_called = True
            response = json_lib.loads(response_str.decode())
            assert response['result'] is None, 'BAD RESULT'
            assert response['id'] == 0
            assert (
                response['error']['message']
                == 'Failure: [Failure instance: Traceback (failure with no frames):'
                " <class 'deluge.error.DelugeError'>: DelugeERROR\n]"
            )
            assert response['error']['code'] == 4

        request.write = write
        request.write_was_called = False
        request._disconnected = False
        request.getHeader.return_value = b'application/json'
        json_data = {'method': 'testclass.test', 'id': 0, 'params': []}
        request.json = json_lib.dumps(json_data).encode()
        d = json._on_json_request(request)

        def on_success(arg):
            assert arg == server.NOT_DONE_YET
            return True

        d.addCallbacks(on_success, pytest.fail)
        yield d
