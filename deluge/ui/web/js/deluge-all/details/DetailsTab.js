/*
Script: Deluge.Details.Details.js
	The details tab displayed in the details panel.

Copyright:
	(C) Damien Churchill 2009-2010 <damoxc@gmail.com>
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

Deluge.details.DetailsTab = Ext.extend(Ext.Panel, {
	title: _('Details'),

	fields: {},

	queuedItems: {},

	oldData: {},

	initComponent: function() {
		Deluge.details.DetailsTab.superclass.initComponent.call(this);
		this.addItem('torrent_name', _('Name'));
		this.addItem('hash', _('Hash'));
		this.addItem('path', _('Path'));
		this.addItem('size', _('Total Size'));
		this.addItem('files', _('# of files'));
		this.addItem('comment', _('Comment'));
		this.addItem('status', _('Status'));
		this.addItem('tracker', _('Tracker'));
	},

	onRender: function(ct, position) {
		Deluge.details.DetailsTab.superclass.onRender.call(this, ct, position);
		this.body.setStyle('padding', '10px');
		this.dl = Ext.DomHelper.append(this.body, {tag: 'dl'}, true);

		for (var id in this.queuedItems) {
			this.doAddItem(id, this.queuedItems[id]);
		}
	},

	addItem: function(id, label) {
		if (!this.rendered) {
			this.queuedItems[id] = label;
		} else {
			this.doAddItem(id, label);
		}
	},

	// private
	doAddItem: function(id, label) {
		Ext.DomHelper.append(this.dl, {tag: 'dt', cls: id, html: label + ':'});
		this.fields[id] = Ext.DomHelper.append(this.dl, {tag: 'dd', cls: id, html: ''}, true);
	},

	clear: function() {
		if (!this.fields) return;
		for (var k in this.fields) {
			this.fields[k].dom.innerHTML = '';
		}
		this.oldData = {}
	},

	update: function(torrentId) {
		deluge.client.web.get_torrent_status(torrentId, Deluge.Keys.Details, {
			success: this.onRequestComplete,
			scope: this,
			torrentId: torrentId
		});
	},

	onRequestComplete: function(torrent, request, response, options) {
		var data = {
			torrent_name: torrent.name,
			hash: options.options.torrentId,
			path: torrent.save_path,
			size: fsize(torrent.total_size),
			files: torrent.num_files,
			status: torrent.message,
			tracker: torrent.tracker,
			comment: torrent.comment
		};

		for (var field in this.fields) {
			if (!Ext.isDefined(data[field])) continue; // this is a field we aren't responsible for.
			if (data[field] == this.oldData[field]) continue;
			this.fields[field].dom.innerHTML = Ext.escapeHTML(data[field]);
		}
		this.oldData = data;
	}
});
