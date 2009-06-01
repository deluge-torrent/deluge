/*
Script: Deluge.Details.Details.js
    The details tab displayed in the details panel.

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

    In addition, as a special exception, the copyright holders give
    permission to link the code of portions of this program with the OpenSSL
    library.
    You must obey the GNU General Public License in all respects for all of
    the code used other than OpenSSL. If you modify file(s) with this
    exception, you may extend this exception to your version of the file(s),
    but you are not obligated to do so. If you do not wish to do so, delete
    this exception statement from your version. If you delete this exception
    statement from all source files in the program, then also delete it here.

*/

Ext.deluge.details.DetailsTab = Ext.extend(Ext.Panel, {
	title: _('Details'),
	cls: 'x-deluge-status',
	
	onRender: function(ct, position) {
		Ext.deluge.details.DetailsTab.superclass.onRender.call(this, ct, position);
		this.load({
			url: '/render/tab_details.html',
			text: _('Loading') + '...'
		});
		this.getUpdater().on('update', this.onPanelUpdate, this);
	},
	
	clear: function() {
		if (!this.fields) return;
		for (var k in this.fields) {
			this.fields[k].innerHTML = '';
		}
	},
	
	update: function(torrentId) {
		Deluge.Client.core.get_torrent_status(torrentId, Deluge.Keys.Details, {
			success: this.onRequestComplete,
			scope: this,
			torrentId: torrentId
		});
	},
	
	onPanelUpdate: function(el, response) {
		this.fields = {};
		Ext.each(Ext.query('dd', this.body.dom), function(field) {
			this.fields[field.className] = field;
		}, this);
	},
	
	onRequestComplete: function(torrent, options) {
		var data = {
			torrent_name: torrent.name,
			hash: options.torrentId,
			path: torrent.save_path,
			size: fsize(torrent.total_size),
			files: torrent.num_files,
			status: torrent.tracker_status,
			tracker: torrent.tracker,
			comment: torrent.comment
		};
		
		for (var field in this.fields) {
			this.fields[field].innerHTML = data[field];
		}
	}
});
Deluge.Details.add(new Ext.deluge.details.DetailsTab());