#!/usr/bin/env python2.4

import xmlrpclib

try:
	# Try and connect to current instance
	proxy = xmlrpclib.ServerProxy('http://localhost:8888')
	print proxy.open_file('server already exists')
except:
	# if connecting failed
	print "couldn't connect to socket"
	import xmlrpc_simple_server
	xmlrpc_simple_server.Server()