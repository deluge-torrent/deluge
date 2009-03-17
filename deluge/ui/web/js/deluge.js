/*
Script: deluge.js
    Contains the events object, formatters and keys for get_torrent(s)_status.

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

var Deluge = {
	author: 'Damien Churchill <damoxc@gmail.com>',
	version: '1.2-dev'
};

Deluge.Events = {
	_events: new Hash(),
	
	fire: function() {
		arguments = $A(arguments);
		var eventName = arguments.shift();
		var eventArgs = arguments;
		if (!this._events[eventName]) return;
		$each(this._events[eventName], function(fn) {
			fn.attempt(eventArgs);
		});
	},
	
	on: function(eventName, fn) {
		var e = $pick(this._events[eventName], new Array());
		e.include(fn);
		this._events[eventName] = e;
	},
	
	removeListener: function(eventName, fn) {
		if (!this._events[eventName]) return;
		this._events[eventName].remove(fn);
	}
};

Deluge.Formatters = {
	size: function(bytes) {
		bytes = bytes / 1024.0;
	
		if (bytes < 1024) { return bytes.toFixed(1)  + ' KiB'; }
		else { bytes = bytes / 1024; }
	
		if (bytes < 1024) { return bytes.toFixed(1)  + ' MiB'; }
		else { bytes = bytes / 1024; }
	
		return bytes.toFixed(1) + ' GiB'
	},
	
	speed: function(bits) {
		return fsize(bits) + '/s'
	},
	
	timeRemaining: function(time) {
		if (time == 0) { return '∞' }
		if (time < 60) { return time + 's'; }
		else { time = time / 60; }
	
		if (time < 60) {
			var minutes = Math.floor(time)
			var seconds = Math.round(60 * (time - minutes))
			if (seconds > 0) {
				return minutes + 'm ' + seconds + 's';
			} else {
				return minutes + 'm'; }
			}
		else { time = time / 60; }
	
		if (time < 24) { 
			var hours = Math.floor(time)
			var minutes = Math.round(60 * (time - hours))
			if (minutes > 0) {
				return hours + 'h ' + minutes + 'm';
			} else {
				return hours + 'h';
			}			
		}
		else { time = time / 24; }
	
		var days = Math.floor(time)
		var hours = Math.round(24 * (time - days))
		if (hours > 0) {
			return days + 'd ' + hours + 'h';
		} else {
			return days + 'd';
		}
	},
	
	plain: function(value) {
		return value;
	}
}

var fsize = Deluge.Formatters.size;
var fspeed = Deluge.Formatters.speed;
var ftime = Deluge.Formatters.timeRemaining;

Deluge.Keys = {
    Grid: [
        'queue', 'name', 'total_size', 'state', 'progress', 'num_seeds',
        'total_seeds', 'num_peers', 'total_peers', 'download_payload_rate',
        'upload_payload_rate', 'eta', 'ratio', 'distributed_copies',
        'is_auto_managed'
    ],
    Status: [
        'total_done', 'total_payload_download', 'total_uploaded',
        'total_payload_upload', 'next_announce', 'tracker_status', 'num_pieces',
        'piece_length', 'is_auto_managed', 'active_time', 'seeding_time',
        'seed_rank'
    ],
    Files: [
        'files', 'file_progress', 'file_priorities'
    ],
    Peers: [
        'peers', 'seeds'
    ],
    Details: [
        'name', 'save_path', 'total_size', 'num_files', 'tracker_status',
        'tracker', 'comment'
    ],
    Options: [
        'max_download_speed', 'max_upload_speed', 'max_connections',
        'max_upload_slots','is_auto_managed', 'stop_at_ratio', 'stop_ratio',
        'remove_at_ratio', 'private', 'prioritize_first_last'
    ]
};
Deluge.Keys.Status.extend(Deluge.Keys.Grid);