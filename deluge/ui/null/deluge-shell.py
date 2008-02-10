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
import readline

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

def add_torrent(cmd):
	"""Add a torrent."""
	def show_usage():
		print "Usage: add [-p <save-location>;] <torrent-file>; [<torrent-file>; ...]"
		print "       (Note that a ';' must follow a path)"
		print ""

	if len(cmd) < 2:
		show_usage()
		return

	save_path = None
	readpath = False
	if cmd[1] == '-p':
		if len(cmd) < 4:
			show_usage()
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
		client.force_call()
	except Exception, msg:
		print "*** Error:", str(msg), "\n"


def show_configs(cmd):
	del cmd[0]
	def _on_get_config(config):
		for key in config:
			if cmd and key not in cmd:	continue
			print "%s: %s" % (key, config[key])
		print ""
	client.get_config(_on_get_config)
	client.force_call()

def show_state(state):
	ts = common.TORRENT_STATE
	return ts.keys()[ts.values().index(state)]

def show_info(torrent, brief):
	"""Show information about a torrent."""
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
		pr = state['file_priorities']
		print pr
		if len(pr) == 0:
			pr = [1] * len(state['files'])
		pr[0] = 2
		print "b", pr
		client.set_torrent_file_priorities(torrent, pr)
	client.get_torrent_status(_got_torrent_status, torrent, status_keys)

def info_torrents(cmd):
	"""Show information about the torrents."""
	torrents = []
	def _got_session_state(tors):
		for tor in tors:
			torrents.append(tor)
	client.get_session_state(_got_session_state)
	client.force_call()
	for tor in torrents:
		if len(cmd) < 2:
			show_info(tor, True)
		elif cmd[1] == tor[0:len(cmd[1])]:
			show_info(tor, False)
	client.force_call()

def exit(cmd):
	"""Terminate."""
	print "Thanks."
	sys.exit(0)

def show_help(cmd):
	"""Show help."""
	print "Available commands:"
	for cmd, action, help in commands:
		print "\t" + cmd + ": " + help

def pause_torrent(cmd):
	"""Pause a torrent"""
	if len(cmd) < 2:
		print "Usage: pause <torrent-id> [<torrent-id> ...]"
		return
	try:
		client.pause_torrent(cmd[1:])
	except Exception, msg:
		print "Error:", str(msg), "\n"

def resume_torrent(cmd):
	"""Resume a torrent."""
	if len(cmd) < 2:
		print "Usage: resume <torrent-id> [<torrent-id> ...]"
		return
	try:
		client.resume_torrent(cmd[1:])
	except Exception, msg:
		print "Error:", str(msg), "\n"

def remove_torrent(cmd):
	"""Remove a torrent."""
	if len(cmd) < 2:
		print "Usage: rm <torrent-id> [<torrent-id> ...]"
		print "       Use 'list' to see the list of torrents."
		print ""
		return
	try:
		client.remove_torrent(cmd[1:])
	except Exception, msg:
		print "*** Error:", str(msg), "\n"

commands = (('add', add_torrent, 'Add a torrent'),
	('configs', show_configs, 'Show configurations'),
	('exit', exit, 'Terminate'),
	('help', show_help, 'Show help about a command, or generic help'),
	('info', info_torrents, 'Show information about the torrents'),
	('pause', pause_torrent, 'Pause a torrent.'),
	('quit', exit, 'Terminate'),
	('resume', resume_torrent, 'Resume a torrent.'),
	('rm', remove_torrent, 'Remove a torrent'),
)

client.set_core_uri("http://localhost:58846")

print "Welcome to deluge-shell. Type 'help' to see a list of available commands."

readline.read_init_file()
while True:
	inp = raw_input("> ")
	if len(inp) == 0:	break
	inp = inp.strip().split(" ")

	print ""
	cmd = inp[0]
	found = False
	for command, action, help in commands:
		if command != cmd:
			continue
		action(inp)
		found = True
		break
	if not found:
		print "Invalid command!"
		show_help([])

print "Thanks."
