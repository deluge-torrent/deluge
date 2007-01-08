# 
# Copyright (c) 2006 Alon Zakai ('Kripken') <kripkensteiner@gmail.com>
#
# 2006-15-9
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#

import time
import BaseHTTPServer
import sys, os

import deluge


# Constants

HOST_NAME = 'localhost'
PORT_NUMBER = 9999


# WebUI Core class

class WebUICore:
	def __init__(self):
		self.running = False

	def start(self):
		self.manager = deluge.manager("DE", "0511", "Deluge WebUI",
		                                 os.path.expanduser("~") + "/Temp")#, blank_slate=True)
		self.running = True

	def quit(self):
		self.manager.quit()
		self.manager = None

		self.running = False

	def get_state(self):
		return self.manager.get_state()

#		print "# torrents:", manager.get_num_torrents()
#		for unique_ID in manager.get_unique_IDs():
#			print unique_ID, manager.get_torrent_state(unique_ID)
#		manager.handle_events()
#		print ""

BUTTONS = { "Start" : WebUICore.start,
            "Quit"  : WebUICore.quit }

# WebUIHandler class - respond to http requests

class WebUIHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	def do_HEAD(self):
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()

	def do_GET(self):
		"""Respond to a GET request."""
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()

		self.wfile.write("<html><head><title>WebUI</title></head><body>")

		if not self.path[-(len(self.get_secret_str())):] == self.get_secret_str():
			self.wfile.write("<p>Invalid access. Run 'webui SECRET', then access 'localhost:9999/?SECRET'.</p>")
		else:
			self.handle_request()

		self.wfile.write("</body></html>")

	def handle_request(self):
		self.wfile.write("<h1>WebUI 0.5.1.1</h1>")

		command = self.path[1:self.path.find("?")]
		print command
		if command[:len("button")] == "button":
			# Execute button command
			command = command[len("button"):]
			BUTTONS[command](core)

		# Main screen
		self.write_buttons()
		if core.running:
			self.write_dict(core.get_state())

#	def get_self_ref(self):
#		return ""#self.client_address[0] + ":" + str(self.client_address[1]) + "/"

	def get_secret_str(self):
		return "?" + secret

	def write_buttons(self):
		self.wfile.write("<table><tr>")
		print core.running
		if core.running:
			self.wfile.write("<tr><td><input type='button' value='Quit' onclick='location.href=" +'"buttonQuit' + self.get_secret_str() + '"' + "'></td></tr>")
		else:
			self.wfile.write("<tr><td><input type='button' value='Start' onclick='location.href=" +'"buttonStart' + self.get_secret_str() + '"' + "'></td></tr>")

		self.wfile.write("</table>")

	def write_dict(self, data):
		if data is not None:
			keys = data.keys()
			keys.sort()

			self.wfile.write("<table>")
			for key in keys:
				self.wfile.write("<tr><td>" + key + "</td><td>" + str(data[key]) + "</td></tr>")
			self.wfile.write("</table>")


########
# Main #
########

print "-------------"
print "WebUI 0.5.1.1"
print "-------------"
print ""

try:
	secret = sys.argv[1]
except IndexError:
	print "USAGE: 'webui.py S', where S is the secret password used to access WebUI via a browser"
	secret = ""

if not secret == "":
	core   = WebUICore()

	httpd = BaseHTTPServer.HTTPServer((HOST_NAME, PORT_NUMBER), WebUIHandler)

	print time.asctime(), "Server Started - %s:%s" % (HOST_NAME, PORT_NUMBER)

	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		pass

	print time.asctime(), "Server Stopped - %s:%s" % (HOST_NAME, PORT_NUMBER)

	core.quit()
