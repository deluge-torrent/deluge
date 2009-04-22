/*
Script: Deluge.Details.Options.js
    The options tab displayed in the details panel.

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

Ext.deluge.details.OptionsTab = Ext.extend(Ext.form.FormPanel, {
	title: _('Options'),
	cls: 'x-deluge-options',
	
	onRender: function(ct, position) {
		Ext.deluge.details.OptionsTab.superclass.onRender.call(this, ct, position);
	},
	
	clear: function() {

	},
	
	update: function(torrentId) {
		Deluge.Client.core.get_torrent_status(torrentId, Deluge.Keys.Options, {
			success: this.onRequestComplete,
			scope: this,
			torrentId: torrentId
		});
	},
	
	onRequestComplete: function(torrent, options) {

	}
});
Deluge.Details.add(new Ext.deluge.details.OptionsTab());