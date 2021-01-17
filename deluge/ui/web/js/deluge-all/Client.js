/**
 * Deluge.Client.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.namespace('Ext.ux.util');

/**
 * A class that connects to a json-rpc resource and adds the available
 * methods as functions to the class instance.
 * @class Ext.ux.util.RpcClient
 * @namespace Ext.ux.util
 */
Ext.ux.util.RpcClient = Ext.extend(Ext.util.Observable, {
    _components: [],

    _methods: [],

    _requests: {},

    _url: null,

    _optionKeys: ['scope', 'success', 'failure'],

    /**
     * @event connected
     * Fires when the client has retrieved the list of methods from the server.
     * @param {Ext.ux.util.RpcClient} this
     */
    constructor: function (config) {
        Ext.ux.util.RpcClient.superclass.constructor.call(this, config);
        this._url = config.url || null;
        this._id = 0;

        this.addEvents(
            // raw events
            'connected',
            'error'
        );
        this.reloadMethods();
    },

    reloadMethods: function () {
        this._execute('system.listMethods', {
            success: this._setMethods,
            scope: this,
        });
    },

    _execute: function (method, options) {
        options = options || {};
        options.params = options.params || [];
        options.id = this._id;

        var request = Ext.encode({
            method: method,
            params: options.params,
            id: options.id,
        });
        this._id++;

        return Ext.Ajax.request({
            url: this._url,
            method: 'POST',
            success: this._onSuccess,
            failure: this._onFailure,
            scope: this,
            jsonData: request,
            options: options,
        });
    },

    _onFailure: function (response, requestOptions) {
        var options = requestOptions.options;
        errorObj = {
            id: options.id,
            result: null,
            error: {
                msg: 'HTTP: ' + response.status + ' ' + response.statusText,
                code: 255,
            },
        };

        this.fireEvent('error', errorObj, response, requestOptions);

        if (Ext.type(options.failure) != 'function') return;
        if (options.scope) {
            options.failure.call(
                options.scope,
                errorObj,
                response,
                requestOptions
            );
        } else {
            options.failure(errorObj, response, requestOptions);
        }
    },

    _onSuccess: function (response, requestOptions) {
        var responseObj = Ext.decode(response.responseText);
        var options = requestOptions.options;
        if (responseObj.error) {
            this.fireEvent('error', responseObj, response, requestOptions);

            if (Ext.type(options.failure) != 'function') return;
            if (options.scope) {
                options.failure.call(
                    options.scope,
                    responseObj,
                    response,
                    requestOptions
                );
            } else {
                options.failure(responseObj, response, requestOptions);
            }
        } else {
            if (Ext.type(options.success) != 'function') return;
            if (options.scope) {
                options.success.call(
                    options.scope,
                    responseObj.result,
                    responseObj,
                    response,
                    requestOptions
                );
            } else {
                options.success(
                    responseObj.result,
                    responseObj,
                    response,
                    requestOptions
                );
            }
        }
    },

    _parseArgs: function (args) {
        var params = [];
        Ext.each(args, function (arg) {
            params.push(arg);
        });

        var options = params[params.length - 1];
        if (Ext.type(options) == 'object') {
            var keys = Ext.keys(options),
                isOption = false;

            Ext.each(this._optionKeys, function (key) {
                if (keys.indexOf(key) > -1) isOption = true;
            });

            if (isOption) {
                params.remove(options);
            } else {
                options = {};
            }
        } else {
            options = {};
        }
        options.params = params;
        return options;
    },

    _setMethods: function (methods) {
        var components = {},
            self = this;

        Ext.each(methods, function (method) {
            var parts = method.split('.');
            var component = components[parts[0]] || {};

            var fn = function () {
                var options = self._parseArgs(arguments);
                return self._execute(method, options);
            };
            component[parts[1]] = fn;
            components[parts[0]] = component;
        });

        for (var name in components) {
            self[name] = components[name];
        }
        Ext.each(
            this._components,
            function (component) {
                if (!component in components) {
                    delete this[component];
                }
            },
            this
        );
        this._components = Ext.keys(components);
        this.fireEvent('connected', this);
    },
});
