/*!
 * Deluge.details.StatusTab.js
 * 
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, write to:
 *     The Free Software Foundation, Inc.,
 *     51 Franklin Street, Fifth Floor
 *     Boston, MA  02110-1301, USA.
 *
 * In addition, as a special exception, the copyright holders give
 * permission to link the code of portions of this program with the OpenSSL
 * library.
 * You must obey the GNU General Public License in all respects for all of
 * the code used other than OpenSSL. If you modify file(s) with this
 * exception, you may extend this exception to your version of the file(s),
 * but you are not obligated to do so. If you do not wish to do so, delete
 * this exception statement from your version. If you delete this exception
 * statement from all source files in the program, then also delete it here.
 */
Ext.ns('Deluge.details');

/**
 * @class Deluge.details.StatusTab
 * @extends Ext.Panel
 */
Deluge.details.StatusTab = Ext.extend(Ext.Panel, {
	title: _('Status'),
	autoScroll: true,
	
	onRender: function(ct, position) {
		Deluge.details.StatusTab.superclass.onRender.call(this, ct, position);
		
		this.progressBar = this.add({
			xtype: 'progress',
			cls: 'x-deluge-status-progressbar'
		});
		
		this.status = this.add({
			cls: 'x-deluge-status',
			id: 'deluge-details-status',
			
			border: false,
			width: 1000,
			listeners: {
				'render': {
					fn: function(panel) {
						panel.load({
							url: deluge.config.base + 'render/tab_status.html',
							text: _('Loading') + '...'
						});
						panel.getUpdater().on('update', this.onPanelUpdate, this);
					},
					scope: this
				}
			}
		});
	},
	
	clear: function() {
		this.progressBar.updateProgress(0, ' ');
		for (var k in this.fields) {
			this.fields[k].innerHTML = '';
		}
	},
	
	update: function(torrentId) {
		if (!this.fields) this.getFields();
		deluge.client.web.get_torrent_status(torrentId, Deluge.Keys.Status, {
			success: this.onRequestComplete,
			scope: this
		});
	},
	
	onPanelUpdate: function(el, response) {
		this.fields = {};
		Ext.each(Ext.query('dd', this.status.body.dom), function(field) {
			this.fields[field.className] = field;
		}, this);
	},
	
	onRequestComplete: function(status) {
		seeders = status.total_seeds > -1 ? status.num_seeds + ' (' + status.total_seeds + ')' : status.num_seeds
		peers = status.total_peers > -1 ? status.num_peers + ' (' + status.total_peers + ')' : status.num_peers
		var data = {
			downloaded: fsize(status.total_done, true),
			uploaded: fsize(status.total_uploaded, true),
			share: (status.ratio == -1) ? '&infin;' : status.ratio.toFixed(3),
			announce: ftime(status.next_announce),
			tracker_status: status.tracker_status,
			downspeed: (status.download_payload_rate) ? fspeed(status.download_payload_rate) : '0.0 KiB/s',
			upspeed: (status.upload_payload_rate) ? fspeed(status.upload_payload_rate) : '0.0 KiB/s',
			eta: ftime(status.eta),
			pieces: status.num_pieces + ' (' + fsize(status.piece_length) + ')',
			seeders: seeders,
			peers: peers,
			avail: status.distributed_copies.toFixed(3),
			active_time: ftime(status.active_time),
			seeding_time: ftime(status.seeding_time),
			seed_rank: status.seed_rank,
			time_added: fdate(status.time_added)
		}
		data.auto_managed = _((status.is_auto_managed) ? 'True' : 'False');

		data.downloaded += ' (' + ((status.total_payload_download) ? fsize(status.total_payload_download) : '0.0 KiB') + ')';
		data.uploaded += ' (' + ((status.total_payload_download) ? fsize(status.total_payload_download): '0.0 KiB') + ')';
		
		for (var field in this.fields) {
			this.fields[field].innerHTML = data[field];
		}
		var text = status.state + ' ' + status.progress.toFixed(2) + '%';
		this.progressBar.updateProgress(status.progress / 100.0, text);
	}
});
