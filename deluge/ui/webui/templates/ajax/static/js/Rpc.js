/*
Script: Rpc.js
    A JSON-RPC proxy built ontop of mootools.

 *
 * Copyright (C) Damien Churchill 2008 <damoxc@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, write to:
 *     The Free Software Foundation, Inc.,
 *     51 Franklin Street, Fifth Floor
 *     Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

 *

    Class: JSON.RPC
        Class to create a proxy to a json-rpc interface on a server.

    Example:
        client = new JSON.RPC('/json/rpc');
        client.hello_world({
            onSuccess: function(result) {
                alert(result);
            }
        });
        alert(client.hello_world({async: false;}));
        client.add_name('Damien', {
            onSuccess: function(result) {
                alert(result);
            }
        });

    Returns:
        The proxy that can be used to directly call methods on the server.
*/
JSON.RPC = new Class({
	Implements: Options,

	options: {
		async: true,
		methods: []
	},

	initialize: function(url, options) {
		this.setOptions(options)
		this.url = url
		if (this.options.methods.length == 0) {
			this._execute('system.listMethods', {async: false}).each(function(method) {
			this[method] = function() {
				var options = this._parseargs(arguments)
				return this._execute(method, options)
			}.bind(this)
		}, this)
		}
	},

	/*
	    Property: _parseargs
	        Internal method for parsing the arguments given to the method

        Arguments:
            args - A list of the methods arguments

        Returns:
            An options object with the arguments set as options.params

	*/
	_parseargs: function(args) {
		var params = $A(args), options = params.getLast()
		if ($type(options) == 'object') {
			var option_keys = ['async', 'onRequest', 'onComplete',
			'onSuccess', 'onFailure', 'onException', 'onCancel'], keys =
				new Hash(options).getKeys(), is_option = false

			option_keys.each(function(key) {
				if (keys.contains(key)) {
					is_option = true
				}
			})

			if (is_option) {
				params.erase(options)
			} else {
				options = {}
			}
		} else { options = {} }
		options.params = params
		return options
	},

	/*
	    Property: _execute
	        An internal method to make the call to the rpc page

        Arguements:
            method - the name of the method
            options - An options dict providing any additional options for the
                      call.

        Example:
            alert(client.hello_world({async: false;}));

        Returns:
            If not async returns the json result
    */
	_execute: function(method, options) {
		options = $pick(options, {})
		options.params = $pick(options.params, [])
		options.async = $pick(options.async, this.options.async)

		data = JSON.encode({
			method: method,
			params: options.params,
			id: 1
		})

		var request = new Request.JSON({
			url: this.url,
			async: options.async,
			onRequest: options.onRequest,
			onComplete: options.onComplete,
			onSuccess: function(response) {
				if (options.onSuccess) {options.onSuccess(response.result)}
			},
			onFailure: options.onFailure,
			onException: options.onException,
			onCancel: options.onCancel
		}).send(data)
		if (!options.async) {
			return request.response.json.result
		}
	}
})
