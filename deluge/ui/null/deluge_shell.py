#!/usr/bin/env python

"""
deluge-shell: Deluge shell.
"""

# deluge-shell: Deluge shell.
#
# Copyright (C) 2007, 2008 Sadrul Habib Chowdhury <sadrul@users.sourceforge.net>
#
# This application is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This application is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this application; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02111-1301
# USA

import deluge.ui.client as client
import deluge.common as common
import deluge.error
import readline
import logging

import sys

status_keys = ["state",
		"save_path",
		"tracker",
		"next_announce",
		"name",
		"total_size",
		"progress",
		"num_seeds",
		"total_seeds",
		"num_peers",
		"total_peers",
		"eta",
		"download_payload_rate",
		"upload_payload_rate",
		"ratio",
		"distributed_copies",
		"num_pieces",
		"piece_length",
		"total_done",
		"files",
		"file_priorities",
		"file_progress",
		]

class Command:
	def __init__(self):
		pass

	def execute(self, cmd):
		pass

	def usage(self):
		print ""

	def help(self):
		pass

class CommandAdd(Command):
	"""Command to add a torrent."""
	def execute(self, cmd):
		if len(cmd) < 2:
			self.usage()
			return

		save_path = None
		readpath = False
		if cmd[1] == '-p':
			if len(cmd) < 4:
				self.usage()
				return
			del cmd[1]
			readpath = True
		else:
			def _got_config(configs):
				global save_path
				save_path = configs['download_location']
			client.get_config(_got_config)
			client.force_call()

		command = " ".join(cmd[1:])
		paths = command.split(';')
		if readpath:
			save_path = paths[0].strip()   # Perhaps verify that the path exists?
			client.set_config({'download_location': save_path})
			del paths[0]

		if not save_path:
			print "There's no save-path specified. You must specify a path to save the downloaded files.\n"
			return

		for iter in range(0, len(paths)):
			paths[iter] = paths[iter].strip()
			if len(paths[iter]) == 0:
				del paths[iter]

		try:
			client.add_torrent_file(paths)
		except Exception, msg:
			print "*** Error:", str(msg), "\n"

	def usage(self):
		print "Usage: add [-p <save-location>;] <torrent-file>; [<torrent-file>; ...]"
		print "       (Note that a ';' must follow a path)"
		print ""

	def help(self):
		print "Add a torrent"

class CommandConfig(Command):
	def execute(self, cmd):
		del cmd[0]
		def _on_get_config(config):
			for key in config:
				if cmd and key not in cmd:	continue
				print "%s: %s" % (key, config[key])
			print ""
		client.get_config(_on_get_config)

	def usage(self):
		print "Usage: config [key1 [key2 ...]]"
		print ""

	def help(self):
		print "Show configuration values"

class CommandExit(Command):
	def execute(self, cmd):
		print "Thanks"
		sys.exit(0)

	def help(self):
		print "Exit from the client."

class CommandHelp(Command):
	def execute(self, cmd):
		if len(cmd) < 2:
			print "Available commands:"
			for cmd in sorted(commands.keys()):
				print "\t*", "%s:" % cmd,
				command = commands[cmd]
				command.help()
		else:
			for c in cmd[1:]:
				if c not in commands:
					print "Unknown command:", c
				else:
					print "*", "%s:" % c,
					command = commands[c]
					command.help()
					command.usage()

	def usage(self):
		print "Usage: help [cmd1 [cmd2 ...]]"
		print ""

	def help(self):
		print "Show help"

class CommandInfo(Command):
	def execute(self, cmd):
		torrents = []
		def _got_session_state(tors):
			for tor in tors:
				torrents.append(tor)
		client.get_session_state(_got_session_state)
		client.force_call()
		for tor in torrents:
			if len(cmd) < 2:
				self.show_info(tor, True)
			elif cmd[1] == tor[0:len(cmd[1])]:
				self.show_info(tor, False)

	def usage(self):
		print "Usage: info [<torrent-id> [<torrent-id> ...]]"
		print "       You can give the first few characters of a torrent-id to identify the torrent."
		print ""

	def help(self):
		print "Show information about the torrents"

	def show_info(self, torrent, brief):
		def show_state(state):
			ts = common.TORRENT_STATE
			return ts.keys()[ts.values().index(state)]
		def _got_torrent_status(state):
			print "*** ID:", torrent
			print "*** Name:", state['name']
			print "*** Path:", state['save_path']
			print "*** Completed:", common.fsize(state['total_done']) + "/" + common.fsize(state['total_size'])
			print "*** Status:", show_state(state['state'])
			if state['state'] in [3, 4, 5, 6]:
				print "*** Download Speed:", common.fspeed(state['download_payload_rate'])
				print "*** Upload Speed:", common.fspeed(state['upload_payload_rate'])
				if state['state'] in [3, 4]:
					print "*** ETA:", "%s" % common.ftime(state['eta'])

			if brief == False:
				print "*** Seeders:", "%s (%s)" % (state['num_seeds'], state['total_seeds'])
				print "*** Peers:", "%s (%s)" % (state['num_peers'], state['total_peers'])
				print "*** Share Ratio:", "%.1f" % state['ratio']
				print "*** Availability:", "%.1f" % state['distributed_copies']
				print "*** Files:"
				for i, file in enumerate(state['files']):
					print "\t*", file['path'], "(%s)" % common.fsize(file['size']), "-", "%.1f%% completed" % (state['file_progress'][i] * 100)
			print ""
		client.get_torrent_status(_got_torrent_status, torrent, status_keys)

class CommandPause(Command):
	def execute(self, cmd):
		if len(cmd) < 2:
			self.usage()
			return
		try:
			client.pause_torrent(cmd[1:])
		except Exception, msg:
			print "Error:", str(msg), "\n"

	def usage(self):
		print "Usage: pause <torrent-id> [<torrent-id> ...]"
		print ""

	def help(self):
		print "Pause a torrent"

class CommandResume(Command):
	def execute(self, cmd):
		if len(cmd) < 2:
			self.usage()
			return
		try:
			client.resume_torrent(cmd[1:])
		except Exception, msg:
			print "Error:", str(msg), "\n"

	def usage(self):
		print "Usage: resume <torrent-id> [<torrent-id> ...]"
		print ""

	def help(self):
		print "Resume a torrent"

class CommandRemove(Command):
	def execute(self, cmd):
		if len(cmd) < 2:
			self.usage()
			return
		try:
			client.remove_torrent(cmd[1:])
		except Exception, msg:
			print "*** Error:", str(msg), "\n"

	def usage(self):
		print "Usage: rm <torrent-id> [<torrent-id> ...]"
		print ""

	def help(self):
		print "Remove a torrent"

class CommandHalt(Command):
	def execute(self, cmd):
		client.shutdown()

	def help(self):
		print "Shutdown the deluge server."

class CommandConnect(Command):
	def execute(self, cmd):
		host = 'localhost'
		port = 58846
		if len(cmd) > 1:
			host = cmd[1]
		if len(cmd) > 2:
			port = int(cmd[2])

		if host[:7] != "http://":
			host = "http://" + host

		client.set_core_uri("%s:%d" % (host, port))

	def usage(self):
		print "Usage: connect [<host> [<port>]]"
		print "       'localhost' is the default server. 58846 is the default port."
		print ""

	def help(self):
		print "Connect to a new deluge server."

commands = {
	'add' : CommandAdd(),
	'configs' : CommandConfig(),
	'exit' : CommandExit(),
	'help' : CommandHelp(),
	'info' : CommandInfo(),
	'pause' : CommandPause(),
	'quit' : CommandExit(),
	'resume' : CommandResume(),
	'rm' : CommandRemove(),
	'del' : CommandRemove(),
	'halt' : CommandHalt(),
	'connect' : CommandConnect(),
}

logging.disable(logging.ERROR)
client.set_core_uri("http://localhost:58846")

class NullUI:
	def __init__(self, args):
		print "Welcome to deluge-shell. Type 'help' to see a list of available commands."

		readline.read_init_file()

		while True:
			try:
				inp = raw_input("> ").strip()
			except:
				inp = 'quit'

			if len(inp) == 0:	continue
			inp = inp.split(" ")

			print ""
			cmd = inp[0]
			found = False
			if cmd not in commands:
				print "Invalid command!"
				commands['help'].execute([])
			else:
				command = commands[cmd]
				try:
					command.execute(inp)
					client.force_call()
				except deluge.error.NoCoreError, e:
					print "*** Operation failed. You are not connected to a deluge daemon."
					print "    Perhaps you want to 'connect' first."
					print ""

		print "Thanks."

