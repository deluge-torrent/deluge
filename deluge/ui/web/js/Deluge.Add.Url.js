/*
Script: Deluge.Add.Url.js
    Contains the Add Torrent by url window.

Copyright:
	(C) Damien Churchill 2009 <damoxc@gmail.com>
	This program is free software; you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation; either version 3, or (at your option)
	any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, write to:
		The Free Software Foundation, Inc.,
		51 Franklin Street, Fifth Floor
		Boston, MA  02110-1301, USA.
*/

Ext.deluge.add.UrlWindow = Ext.extend(Ext.deluge.add.Window, {
	constructor: function(config) {
		config = Ext.apply({
			layout: 'fit',
			width: 350,
			height: 115,
			bodyStyle: 'padding: 10px 5px;',
			buttonAlign: 'center',
			closeAction: 'hide',
			modal: true,
			plain: true,
			title: _('Add from Url'),
			iconCls: 'x-deluge-add-url-window-icon',
			buttons: [{
				text: _('Add'),
				handler: this.onAdd,
				scope: this
			}]
		}, config);
		Ext.deluge.add.UrlWindow.superclass.constructor.call(this, config);
	},
	
	initComponent: function() {
		Ext.deluge.add.UrlWindow.superclass.initComponent.call(this);
		this.form = this.add(new Ext.form.FormPanel({
			defaultType: 'textfield',
			baseCls: 'x-plain',
			labelWidth: 55,
			items: [{
				fieldLabel: _('Url'),
				id: 'url',
				name: 'url',
				inputType: 'url',
				anchor: '100%',
				listeners: {
					'specialkey': {
						fn: this.onAdd,
						scope: this
					}
				}
			}]
		}));
	},
	
	onAdd: function(field, e) {
		if (field.id == 'url' && e.getKey() != e.ENTER) return;

		var field = this.form.items.get('url');
		var url = field.getValue();
		
		Deluge.Client.web.download_torrent_from_url(url, {
			success: this.onDownload,
			scope: this
		});
		this.hide();
		this.fireEvent('beforeadd', url);
	},
	
	onDownload: function(filename) {
		this.form.items.get('url').setValue('');
		Deluge.Client.web.get_torrent_info(filename, {
			success: this.onGotInfo,
			scope: this,
			filename: filename
		});
	},
	
	onGotInfo: function(info, obj, response, request) {
		info['filename'] = request.options.filename;
		this.fireEvent('add', info);
	}
});