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

# Docs:
#
# All httpserver-related issues are done through GET (html, javascript, css,
# etc.). All torrentcore issues are doen through POST.
#

import time
import BaseHTTPServer
import sys, os
import webbrowser

sys.path.append("/media/sda2/svn/deluge-trac/trunk/library")

import flood # or whatever the core is renamed to be
import json

# Constants

HOST_NAME = 'localhost'
PORT_NUMBER = 9999

HTML_DIR = "www/com.WebUI.WebUIApp"

HEADERS_TEXT = "text/plain"
HEADERS_HTML = "text/html"
HEADERS_CSS  = "text/css"
HEADERS_JS   = "text/javascript"

manager = None
httpd   = None

class webuiServerHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	def get_secret_str(self):
		return "?" + secret

	def pulse(self):
		global manager

		manager.handle_events()

	def write_headers(self, content_type, data_length=None):
		self.send_response(200)
		self.send_header("Content-type", content_type)
		if data_length is not None:
			self.send_header("Content-length", data_length)
		self.end_headers()

	def do_POST(self):
		global manager

		input_length = int(self.headers.get('Content-length'))
		command = self.rfile.read(input_length)
		print "POST command:", command

		if command == "quit":
			httpd.ready = False

#			self.write_headers(HEADERS_TEXT)
#			self.wfile.write("OK: quit")
		# List torrents, and pulse the heartbeat
		elif command == "list":
			self.pulse() # Start by ticking the clock

			data = []
			unique_IDs = manager.get_unique_IDs()
			for unique_ID in unique_IDs:
				temp = manager.get_torrent_state(unique_ID)
				temp["unique_ID"] = unique_ID # We add the unique_ID ourselves
				data.append(temp)

			self.write_headers(HEADERS_TEXT)
			self.wfile.write(json.write(data))
		else:
			# Basically we can just send Python commands, to be run in exec(command)... but that
			# would be slow, I guess
			print "UNKNOWN POST COMMAND:", command

	def do_GET(self):
#		self.wfile.write("<h1>webuiServer 0.5.1.1</h1>")

		print "Contacted from:", self.client_address

		if "?" in self.path:
			command   = self.path[1:self.path.find("?")]
		else:
			command   = self.path[1:]

		if command == "":
			command = "WebUI.html"

			if not self.path[-(len(self.get_secret_str())):] == self.get_secret_str():
				self.write_headers(HEADERS_HTML)
				self.wfile.write("<html><head><title>webuiServer</title></head><body>")
				self.wfile.write("<p>Invalid access. Run 'webuiserver SECRET', then access 'localhost:9999/?SECRET'.</p>")
				self.wfile.write("</body></html>")
				return

		if "." in command:
			extension = command[command.rfind("."):]
		else:
			extension = ""

		print "Handling: ", self.path, ":", command, ":", extension

		try:
			filey = open("./" + HTML_DIR + "/" + command, 'rb')
			lines = filey.readlines()
			filey.close()

			data = "".join(lines)

			if extension == ".html":
				self.write_headers(HEADERS_HTML, len(data))
			elif extension == ".js":
				self.write_headers(HEADERS_JS, len(data))
			elif extension == ".css":
				self.write_headers(HEADERS_CSS, len(data))
			else:
				print "What is this?", extension

			self.wfile.write(data)
		except IOError:
			self.write_headers(HEADERS_HTML)
			self.wfile.write("<html><head><title>webuiServer</title></head><body>")
			self.wfile.write("<h1>webuiServer 0.5.1.1</h1>")
			self.wfile.write("No such command: " + command)


class webuiServer(BaseHTTPServer.HTTPServer):
	def serve_forever(self):
		self.ready = True
		while self.ready:
			self.handle_request()
		self.server_close()

########
# Main #
########

print "-------------------"
print "webuiServer 0.5.1.1"
print "-------------------"
print ""

try:
	secret = sys.argv[1]
except IndexError:
	print "USAGE: 'webuiserver.py S', where S is the secret password used to access via a browser"
	secret = ""

if not secret == "":

#	manager.add_torrent("xubuntu-6.10-desktop-i386.iso.torrent",
#	                    os.path.expanduser("~") + "/Temp", True)

	httpd = webuiServer((HOST_NAME, PORT_NUMBER), webuiServerHandler)
	print time.asctime(), "HTTP Server Started - %s:%s" % (HOST_NAME, PORT_NUMBER)

	manager = flood.manager("FL", "0500", "webui",
	                             os.path.expanduser("~") + "/Temp")#, blank_slate=True)

	webbrowser.open("localhost:9999/?" + secret)

	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		pass

	print time.asctime(), "HTTP Server Stopped - %s:%s" % (HOST_NAME, PORT_NUMBER)

	print "Shutting down manager..."
	manager.quit()


### OLD
#		# Check if the manager is running
#		if not command == "init":
#			if manager is None:
#				self.write_headers(HEADERS_TEXT)
#				self.wfile.write("ERROR: manager is None")
#				return
#
#		if command == "init":
#			if manager is not None:
#				print "ERROR: Trying to init, but already active"
#				return
#
#			manager = webui.manager("FL", "0500", "webui",
#			                             os.path.expanduser("~") + "/Temp")#, blank_slate=True)
#			self.write_headers(HEADERS_TEXT)
#			self.wfile.write("OK: init")
