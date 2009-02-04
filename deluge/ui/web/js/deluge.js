var Deluge = $empty;

Deluge.Formatters = {
	size: function(bytes) {
		if (bytes < 1024) { return bytes.toFixed(1)  + ' B'; }
		else { bytes = bytes / 1024; }
	
		if (bytes < 1024) { return bytes.toFixed(1)  + ' KiB'; }
		else { bytes = bytes / 1024; }
	
		if (bytes < 1024) { return bytes.toFixed(1)  + ' MiB'; }
		else { bytes = bytes / 1024; }
	
		return bytes.toFixed(1) + ' GiB'
	},
	
	speed: function(bits) {
		if (bits < 1024) { return bits.toFixed(1)  + ' b/s'; }
		else { bits = bits / 1024; }
	
		if (bits < 1024) { return bits.toFixed(1)  + ' KiB/s'; }
		else { bits = bits / 1024; }
	
		return bits.toFixed(2) + ' MiB/s'
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

Deluge.Keys = {
    Grid: [
        'queue', 'name', 'total_size', 'state', 'progress', 'num_seeds',
        'total_seeds', 'num_peers', 'total_peers', 'download_payload_rate',
        'upload_payload_rate', 'eta', 'ratio', 'distributed_copies',
        'is_auto_managed'
    ],
    Statistics: [
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
        'tracker'
    ],
    Options: [
        'max_download_speed', 'max_upload_speed', 'max_connections',
        'max_upload_slots','is_auto_managed', 'stop_at_ratio', 'stop_ratio',
        'remove_at_ratio', 'private', 'prioritize_first_last'
    ]
};
Deluge.Keys.Statistics.extend(Deluge.Keys.Grid);