# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 bendikro <bro.devel+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.

import json
import logging
from urllib.parse import parse_qs

from twisted.internet.defer import Deferred
from twisted.web import http, resource, server

from deluge import component
from deluge.error import DelugeError
from deluge.ui.web.json_api import ERROR_RESPONSE_CODE, JsonAPIException
from deluge.ui.web.webapidoc.openapi_builder import OpenAPISpecBuilder

log = logging.getLogger(__name__)


class MethodNotAllowedException(JsonAPIException):
    pass


class JSONWebapi(resource.Resource, component.Component):
    """
    A Twisted Web resource that provides the webapi documentation with swagger-ui

    """

    def __init__(self, basename):
        resource.Resource.__init__(self)
        component.Component.__init__(self, 'JSONWebapi', depend=['JSON'])
        self._json = component.get('JSON')
        self.basename = basename
        self.spec_builder = OpenAPISpecBuilder(self._json, basename)

    def get_method_from_request(self, request):
        path = request.path.decode()
        method = path[len('/%s/' % self.basename) :].replace('/', '.')
        return method

    def _get_query_params(self, request):
        uri_parsed = http.urlparse(request.uri)
        query_param = parse_qs(uri_parsed.query.decode(), keep_blank_values=True)
        return query_param

    def _get_json_dumps_kwargs(self, request):
        """
        Check if we should prettify the json result
        """
        query_param = self._get_query_params(request)
        dumps_kwargs = {}
        if 'pretty' in query_param:
            dumps_kwargs['indent'] = 4
        return dumps_kwargs

    def _send_response(self, request, response):
        if request._disconnected:
            return ''
        dumps_kwargs = self._get_json_dumps_kwargs(request)
        response = json.dumps(response, **dumps_kwargs)
        request.setHeader(b'content-type', b'application/json')
        request.write(response.encode())
        request.finish()
        return server.NOT_DONE_YET

    def getChild(self, path, request):  # NOQA: N802
        return self

    def render_swagger(self, request):
        spec = self.spec_builder.build_spec()
        self._send_response(request, spec)

    def render(self, request):
        """
        Handles all the POST requests made to the /api controller.

        """
        if (
            request.method == b'GET'
            and request.path == '/{}/openapi.json'.format(self.basename).encode()
        ):
            self.render_swagger(request)
            return server.NOT_DONE_YET

        try:
            request.content.seek(0)
            request.json = request.content.read()
            method = self._verify_request_method(request)

            if method == 'POST':
                self._on_post_request(request)
            elif method == 'GET':
                self._on_get_request(request)
            else:
                request.setResponseCode(http.NOT_ALLOWED)
                request.finish()
                return server.NOT_DONE_YET

            return server.NOT_DONE_YET
        except MethodNotAllowedException:
            request.setResponseCode(http.NOT_ALLOWED)
            request.finish()
            return server.NOT_DONE_YET
        except Exception as ex:
            return self._json._on_json_request_failed(ex, request)

    def _verify_request_method(self, request):
        """
        Ensure that the request HTTP method matches the method the
        function is exported for.

        Args:
            request (Request): the request to process

        Returns:
            str: the HTTP method the python function is exported for

        Raises:
            MethodNotAllowedException: if the request method does not match the exported function

        """
        method = self.get_method_from_request(request)
        func = self._json._local_methods.get(method, None)
        _webapi = getattr(func, '_webapi')

        if request.method != _webapi['method'].encode():
            raise MethodNotAllowedException(request.method)
        return _webapi['method']

    def _get_request_id(self, request):
        query_param = self._get_query_params(request)
        request_id = None
        if 'id' in query_param:
            try:
                request_id = int(query_param['id'][0])
            except (KeyError, IndexError, ValueError):
                pass
        return request_id

    def _on_rpc_request_failed(self, reason, response, request):
        """
        Handles any failures that occurred while making an rpc call.
        """
        # If DelugeError, this is an error message from the function
        if isinstance(reason.value, DelugeError):
            response['error'] = {
                'message': '%s' % (reason.value),
                'code': ERROR_RESPONSE_CODE.DELUGE_ERROR,  # new
            }
        else:
            response['error'] = {
                'message': '%s: %s' % (reason.__class__.__name__, str(reason)),
                'code': ERROR_RESPONSE_CODE.RPC_ERROR,  # 4
            }
        return self._send_response(request, response)

    def _on_get_request(self, request):
        request_id = self._get_request_id(request)
        request_data = {}
        response = {'result': None, 'error': None, 'id': None}
        response['id'], d, response['error'] = self._handle_request_function_call(
            request, request_id, request_data
        )

        if isinstance(d, Deferred):
            d.addCallback(self._json._on_rpc_request_finished, response, request)
            d.addErrback(self._json._on_rpc_request_failed, response, request)
            return d
        else:
            response['result'] = d
            return self._send_response(request, response)

    def _on_post_request(self, request):
        """
        Handler to take the json data as a string and pass it on to the
        _handle_request method for further processing.
        """
        content_type = request.getHeader(b'content-type')
        if not content_type or content_type.decode() != 'application/json':
            message = 'Invalid JSON request content-type: %s' % content_type
            raise JsonAPIException(message)

        try:
            request_data = json.loads(request.json.decode())
        except (ValueError, TypeError):
            raise JsonAPIException('JSON not decodable')

        request_id = self._get_request_id(request)

        log.debug('json-request: %s', request.json)
        response = {'result': None, 'error': None, 'id': None}
        response['id'], d, response['error'] = self._handle_request_function_call(
            request, request_id, request_data
        )

        if isinstance(d, Deferred):
            d.addCallback(self._json._on_rpc_request_finished, response, request)
            d.addErrback(self._on_rpc_request_failed, response, request)
            return d
        else:
            response['result'] = d
            return self._send_response(request, response)

    def _handle_request_function_call(self, request, request_id, request_data):
        """
        Call the exported python function for the request

        Args:
            request (Request): The request
            request_data (dict): The request data with the function arguments

        """
        try:
            params = request_data.get('params', [])
            method = self.get_method_from_request(request)
        except Exception as ex:
            raise JsonAPIException(ex)
        return self._json._exec_method(request, method, params, request_id)
