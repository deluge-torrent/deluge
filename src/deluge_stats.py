# 
# Copyright (C) 2006 Alon Zakai ('Kripken') <kripkensteiner@gmail.com>
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
# along with this program.  If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#  In addition, as a special exception, the copyright holders give
#  permission to link the code of portions of this program with the OpenSSL
#  library.
#  You must obey the GNU General Public License in all respects for all of
#  the code used other than OpenSSL. If you modify file(s) with this
#  exception, you may extend this exception to your version of the file(s),
#  but you are not obligated to do so. If you do not wish to do so, delete
#  this exception statement from your version. If you delete this exception
#  statement from all source files in the program, then also delete it here.

import time

# Global variables. Caching of saved data, mostly

old_peer_info           = None
old_peer_info_timestamp = None

# Availability - how many complete copies are among our peers
def calc_availability(peer_info):
	if len(peer_info) == 0:
		return 0

	num_pieces = len(peer_info[0].pieces)

	freqs = [0]*num_pieces

	for peer in peer_info:
		for piece in num_pieces:
			freqs[piece] = freqs[piece] + peer['pieces'][piece]

	minimum = min(freqs)
#		frac = freqs.count(minimum + 1) # Does this mean something?

	return minimum

# Swarm speed - try to guess the speed of the entire swarm
# We return #pieces / second. The calling function should convert pieces to KB, if it wants
# Note that we return the delta from the last call. If the client calls too soon, this may
# be too unreliable. But the client can smooth things out, if desired
def calc_swarm_speed(peer_info):
	if old_peer_info is not None:
		new_pieces  = 0
		peers_known = 0

		# List new peers
		new_peer_IPs = {} # ip->peerinfo dict (from the core)
		for peer in peer_info:
			new_peer_IPs[peer['ip']] = peer

		for new_IP in new_peer_IPs.keys():
			if new_IP in old_peer_IPs.keys():
				# We know this peer from before, see what changed
				peers_known = peers_known + 1
				delta       = sum(new_peer_IPs[new_IP].pieces) - sum(old_peer_IPs[new_IP].pieces)

				if delta >= 0:
					new_pieces  = new_pieces + delta
				else:
					print "Deluge.stat.calc_swarm_speed: Bad Delta: ", delta, old_peer_IPs[new_IP].pieces, new_peer_IPs[new_IP].pieces

	# Calculate final value
	time_delta = time.time() - old_peer_info_timestamp
	ret = float(new_pieces)/( float(peers_known) * time_delta )

	# Save info
	old_peer_info           = peer_info
	old_peer_info_timestamp = time.time()
	old_peer_IPs            = new_peer_IPs

	return ret
