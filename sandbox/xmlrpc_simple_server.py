#!/usr/bin/env python2.4

import SimpleXMLRPCServer

class Server:
	def __init__(self):
		print "Starting simple server, registering"
		self.server = StoppableXMLRPCServer(('localhost',8888))
		self.server.register_instance(self)
		self.server.serve_forever()
	
	def open_file(self, *args):
		print "Opening files", args
		return args

	def shut_down(self, *args):
		print "Shutting down the server"
		self.server.stop = True
		
######
class StoppableXMLRPCServer(SimpleXMLRPCServer.SimpleXMLRPCServer):
	"""Override of TIME_WAIT"""
	allow_reuse_address = True

	def serve_forever(self):
		self.stop = False
		while not self.stop:
			self.handle_request()
######
