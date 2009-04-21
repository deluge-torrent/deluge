/*
Script: Deluge.Client.js
    A JSON-RPC proxy built on top of ext-core.

Copyright:
    (C) Damien Churchill 2009 <damoxc@gmail.com>
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3, or (at your option)
    any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, write to:
        The Free Software Foundation, Inc.,
        51 Franklin Street, Fifth Floor
        Boston, MA  02110-1301, USA.
*/

Ext.namespace('Ext.ux.util');
(function() {
    Ext.ux.util.RpcClient = Ext.extend(Ext.util.Observable, {

        _methods: [],
        
        _requests: {},
        
        _url: null,
        
        _optionKeys: ['scope', 'success', 'failure'],
        
        constructor: function(config) {
            Ext.ux.util.RpcClient.superclass.constructor.call(this, config);
            this._url = config.url || null;
            this._id = 0;
            
            this.addEvents(
                // raw events
                /**
                 * @event ready
                 * Fires when the client has retrieved the list of methods from the server.
                 * @param {Ext.ux.util.RpcClient} this
                 */
                 'ready'
            );
            
            this._execute('system.listMethods', {
                success: this._setMethods,
                scope: this
            });
        },
    
        _execute: function(method, options) {
            options = options || {};
            options.params = options.params || [];
            options.id = this._id;
            
            var request = Ext.encode({
                method: method,
                params: options.params,
                id: options.id
            });
            this._id++;
            
            return Ext.Ajax.request({
                url: this._url,
                method: 'POST',
                success: this._onSuccess,
                failure: this._onFailure,
                scope: this,
                jsonData: request,
                options: options
            });
        },
        
        _onFailure: function(response, options) {
            if (response.status == 500) {
                //error
            }
            errorObj = {
                id: options.options.id
            }
            alert(Ext.encode(errorObj));
        },
        
        _onSuccess: function(response, requestOptions) {
            var responseObj = Ext.decode(response.responseText);
            var options = requestOptions.options;
            if (responseObj.error) {
                if (Ext.type(options.failure) != 'function') return;
                if (options.scope) {
                    options.failure.call(options.scope, responseObj.error, responseObj, response);
                } else {
                    options.failure(responseObj.error, responseObj, response);
                }
            } else {
                if (Ext.type(options.success) != 'function') return;
                if (options.scope) {
                    options.success.call(options.scope, responseObj.result, responseObj, response);
                } else {
                    options.success(responseObj.result, responseObj, response);
                }
            }
        },
        
        _parseArgs: function(args) {
            var params = [];
            Ext.each(args, function(arg) {
                params.push(arg);
            });
            
            var options = params[params.length - 1];
            if (Ext.type(options) == 'object') {
                var keys = Ext.keys(options), isOption = false;
                
                Ext.each(this._optionKeys, function(key) {
                    if (keys.indexOf(key) > -1) isOption = true;
                });
                
                if (isOption) {
                    params.remove(options)
                } else {
                    options = {}
                }
            } else {
                options = {}
            }
            options.params = params;
            return options;
        },
    
        _setMethods: function(methods) {
            var components = {}, self = this;
            
            Ext.each(methods, function(method) {
                var parts = method.split('.');
                var component = components[parts[0]] || {};
                
                var fn = function() {
                    var options = self._parseArgs(arguments);
                    return self._execute(method, options);
                }
                component[parts[1]] = fn;
                components[parts[0]] = component;
            });
            
            for (var name in components) {
                self[name] = components[name];
            }
            
            this.fireEvent('ready', this);
        }
    });
})();
