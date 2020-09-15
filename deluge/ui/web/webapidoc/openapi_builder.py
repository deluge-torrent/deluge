# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 bendikro <bro.devel+deluge@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.

import ast
import copy
import logging
import re
import sys

import six
from apispec import APISpec, BasePlugin
from apispec.yaml_utils import load_operations_from_docstring

log = logging.getLogger(__name__)


class DeprecatedPlugin(BasePlugin):
    def operation_helper(self, func, operations, **kwargs):
        """Operation helper that add `deprecated`
        """
        if func is None:
            return

        _webapi = getattr(func, '_webapi', None)
        deprecated = _webapi['export_kwargs'].get('deprecated', False)
        if deprecated is True or isinstance(deprecated, six.string_types):
            for key, value in operations.items():
                value['deprecated'] = True
                if isinstance(deprecated, six.string_types):
                    value['summary'] = deprecated


class JsonAPIPlugin(BasePlugin):
    """
    Apispec plugin to handle special API functions

    auth.login:
        Add descriptions for successful response including the Set-Cookie header
    json:
        Add available values for the method parameter (all exported functions)
    """

    def __init__(self, json_component):
        self.json_component = json_component

    def operation_helper(self, method_name, path, func, operations, **kwargs):
        """Operation helper that handles special API methods
        """
        if method_name == 'auth.login':
            resp_200 = operations['post']['responses']['200']
            resp_200['description'] = (
                'Successfully authenticated.'
                'The session id returned in a cookie named `_session_id`. '
                'You need to include this cookie in subsequent requests.'
            )

            example_session_cookie = (
                '_session_id=b67535d4c123a857d4cbc21d8f73d3b165c204d415396d5960f131adc0991bd64329; '
                'Expires=Tue, 15 Oct 2019 18:14:57 GMT; Path=/json'
            )
            resp_200['headers'] = {
                'Set-Cookie': {
                    'schema': {'type': 'string', 'example': example_session_cookie}
                }
            }
        elif path == '/json':
            # Get all the exported methods
            functions = []
            for name, func in self.json_component._local_methods.items():
                if getattr(func, '_webapi', False):
                    functions.append(name)

            example_method = 'auth.login'
            example_params = ['deluge']

            body_param = {
                'type': 'object',
                'properties': [
                    {'name': 'method', 'type': 'string', 'enum': functions},
                    {'name': 'params', 'type': 'array', 'items': {}},
                ],
            }

            for param in operations['post']['parameters']:
                if param['name'] == 'params':
                    param['schema'].update({'example': example_params})
                    break

            # Insert method before params parameter (index 2)
            operations['post']['parameters'].insert(
                2,
                {
                    'in': 'body',
                    'required': True,
                    'name': 'method',
                    'schema': {
                        'type': 'string',
                        'enum': functions,
                        'example': example_method,
                    },
                },
            )

            json_content = operations['post']['requestBody']['content'][
                'application/json'
            ]
            json_content.update(
                {
                    'schema': body_param,
                    'example': '{"method": "%s", "params": ["%s"]}'
                    % (example_method, '", "'.join(example_params)),
                }
            )


class GoogleStyleDocPlugin(BasePlugin):
    """
    Apispec plugin to parse Google style method docs
    """

    def init_spec(self, spec):
        super().init_spec(spec)
        self.openapi_major_version = spec.openapi_version.major

    def operation_helper(self, operations, func, **kwargs):
        """
        Operation helper that parses docstrings for operations. Adds a
        ``func`` parameter to `apispec.APISpec.path`.
        """
        if func is None:
            return

        func_docs = func.__doc__
        doc_operations = load_operations_from_docstring(func_docs)

        method = None
        if 'post' in operations:
            method = 'post'
        elif 'get' in operations:
            method = 'get'
        else:
            log.warning('HTTP method not found for function:', func.__qualname__)
            return

        try:
            # Import docstring_parser here as it only supports python >= 3.6
            import docstring_parser  # noqa

            docstring = docstring_parser.parse(func_docs)
        except ValueError as err:
            log.warning(
                'Error parsing docstrings for function "%s": %s', func.__qualname__, err
            )
            log.warning('Doc string : %s', func_docs)
            return

        operations[method]['description'] = docstring.short_description
        params_example = []
        params_description = 'The parameters to use\n\n'

        def extract_example(description):
            """
            Extract example code from the function description (Parameters of return value)

            Everything after 'Example::' is regarded as valid python example code

            """
            try:
                example_pattern = 'Example::'
                index = description.index(example_pattern)
                description_without_example = description[:index]
                example = description[index + len(example_pattern) :].strip()
                return description_without_example, example
            except ValueError:
                pass
            return description, None

        def get_evaled_example(example):
            """
            Call eval on example code to ensure it is valid python code
            """
            if example is None:
                return
            try:
                # Try to convert the example to python type
                example_eval = ast.literal_eval(example)
                return example_eval
            except (SyntaxError, ValueError) as err:
                log.info(
                    "Failed to evaluate return type example '%s': %s" % (example, err)
                )
                return (
                    'Failed to evaluate doc example (%s): %s. Please fix your doc style!'
                    % (example, err)
                )

        for param in docstring.params:
            param_description = param.description
            description, example = extract_example(param.description)
            eval_example = get_evaled_example(example)

            if eval_example is not None:
                params_example.append(eval_example)
            else:
                params_example.append(param.arg_name)

            if example is not None:
                param_description = description + 'Example: ```%s```' % (example)

            # Supports CommonMark https://swagger.io/docs/specification/basic-structure/
            # (https://spec.commonmark.org/0.27/)
            params_description += '* {name} ({type}): {description}\n'.format(
                name=param.arg_name, type=param.type_name, description=param_description
            )
        # Get the 'params' parameter
        params = None
        for par in operations[method]['parameters']:
            if par['name'] == 'params':
                params = par
                break

        if params is not None:
            assert params['name'] == 'params'
            params['description'] = params_description

            if params_example:
                rbody_content = operations[method]['requestBody']['content']
                rbody_content['application/json']['schema']['example'][
                    'params'
                ] = params_example
                params['schema']['example'] = params_example

        success_response = {'description': 'Reponse description missing'}

        # Docstring contains a Returns section
        if docstring.returns:
            success_response_example = {'result': None, 'error': None, 'id': 1}

            description, example = extract_example(docstring.returns.description)
            response_type = docstring.returns.type_name

            if example:
                eval_example = get_evaled_example(example)
                if eval_example:
                    example = eval_example
                success_response_example['result'] = example

            if response_type:
                m = re.search(r'Deferred\((.\S+)\)', response_type)
                if m:
                    groups = m.groups()
                    response_type = groups[0]

            # Python types tuple and list must be specified as array
            if response_type in ['tuple', 'list']:
                response_type = 'array'

            response_description = description
            if response_type:
                response_description = 'result ({}): {}'.format(
                    response_type, response_description
                )

            success_response.update(
                {
                    'description': response_description,
                    'content': {
                        'application/json': {
                            'schema': {'type': response_type, 'items': {}},
                            'example': success_response_example,
                        }
                    },
                }
            )

        operations[method]['responses']['200'].update(success_response)

        # Apply conditional processing
        if self.openapi_major_version < 3:
            '...Mutating doc_operations for OpenAPI v2...'
        else:
            '...Mutating doc_operations for OpenAPI v3+...'
        operations.update(doc_operations)


class OpenAPISpecBuilder(object):
    def __init__(self, json_component, basename):
        self.json_component = json_component
        self.basename = basename

    def get_parameter_id(self, example_id=None):
        param_id = {
            'name': 'id',
            'in': 'query',
            'required': False,
            'schema': {'type': 'string'},
        }
        if example_id is not None:
            param_id['schema']['example'] = example_id
        return param_id

    def get_parameter_pretty(self):
        return {
            'name': 'pretty',
            'in': 'query',
            'required': False,
            'schema': {'type': 'string', 'example': 'pretty'},
        }

    def build_spec(self):
        plugins = [DeprecatedPlugin(), JsonAPIPlugin(self.json_component)]
        # docstring_parser supports >= 3.6
        if (sys.version_info.major, sys.version_info.minor) >= (3, 6):
            plugins.insert(0, GoogleStyleDocPlugin())

        self.spec = APISpec(
            title='Deluge Webapi',
            version='1.0.0',
            openapi_version='3.0.2',
            plugins=plugins,
        )

        self.add_post_method('json', '/json', '/json')

        for name, func in self.json_component._local_methods.items():
            if getattr(func, '_webapi', False):
                method_path = name.replace('.', '/')
                webapi_conf = getattr(func, '_webapi')
                path = '/{}/{}'.format(self.basename, method_path)

                if webapi_conf.get('method', None) == 'GET':
                    self.add_get_method(
                        name, method_path, path, func=func, webapi_conf=webapi_conf
                    )
                    continue

                if webapi_conf.get('method', None) == 'POST':
                    self.add_post_method(
                        name, method_path, path, func=func, webapi_conf=webapi_conf
                    )
                    continue

        return self.spec.to_dict()

    def add_post_method(self, name, method_path, path, func=None, webapi_conf=None):
        """
        Add a post method to the openapi spec

        """
        parameters = []
        tags = []
        params_description = {'params': []}
        example_id = '1'
        defaults = {}

        if webapi_conf:
            defaults = webapi_conf.get('defaults', {})
            params_description['params'].extend(webapi_conf['args'])
            export_kwargs = webapi_conf.get('export_kwargs', {})
            tags.extend(export_kwargs.get('tags', []))

        parameters.append(self.get_parameter_id(example_id=example_id))
        parameters.append(self.get_parameter_pretty())
        parameters.append(
            {
                'in': 'body',
                'required': True,
                'name': 'params',
                'schema': {'type': 'array', 'items': {}, 'example': params_description},
            }
        )

        example_body = {}
        example_body.update(copy.deepcopy(params_description))
        example_params = copy.deepcopy(params_description)

        params = list(example_params['params'])
        for i, param in enumerate(params):
            if param in defaults:
                example_params['params'][i] = defaults[param]

        example_body.update(example_params)
        responses = {'200': {'description': 'standard response'}}
        description = 'Description for %s' % method_path

        self.spec.path(
            method_name=name,
            func=func,
            path=path,
            parameters=parameters,
            operations={
                'post': {
                    'description': description,
                    'responses': responses,
                    'parameters': parameters,
                    'operationId': name,
                    'tags': tags,
                    'requestBody': {
                        'description': "The request body for '%s'" % name,
                        'required': True,
                        'content': {
                            'application/json': {
                                'schema': {
                                    'type': 'array',
                                    'items': {},
                                    'example': example_body,
                                },
                            },
                        },
                    },
                }
            },
            description='Not used...',
        )

    def add_get_method(self, name, method_path, path, func=None, webapi_conf=None):
        """
        Add a get method to the openapi spec

        """
        parameters = []
        tags = []
        example_params = {'params': []}
        example_id = '1'

        if webapi_conf:
            example_params['params'].extend(webapi_conf['args'])
            parameters.append(self.get_parameter_id(example_id=example_id))
            parameters.append(self.get_parameter_pretty())
            export_kwargs = webapi_conf.get('export_kwargs', {})
            tags.extend(export_kwargs.get('tags', []))

        example_body = {}
        example_body.update(example_params)
        responses = {'200': {'description': 'standard response'}}

        self.spec.path(
            method_name=name,
            func=func,
            path=path,
            parameters=parameters,
            operations={
                'get': {
                    'responses': responses,
                    'parameters': parameters,
                    'operationId': name,
                    'tags': tags,
                }
            },
            description='Not used...',
        )
