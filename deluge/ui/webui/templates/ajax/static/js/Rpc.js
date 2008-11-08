/*
Script: Rpc.js
    A JSON-RPC proxy built ontop of mootools.

Copyright:
    Damien Churchill (c) 2008 <damoxc@gmail.com>

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
