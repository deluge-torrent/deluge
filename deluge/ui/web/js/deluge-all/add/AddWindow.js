/*!
 * Deluge.add.AddWindow.js
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

Ext.namespace('Deluge.add');

Deluge.add.AddWindow = Ext.extend(Deluge.add.Window, {

	constructor: function(config) {
		config = Ext.apply({
			title: _('Add Torrents'),
			layout: 'border',
			width: 470,
			height: 450,
			bodyStyle: 'padding: 10px 5px;',
			buttonAlign: 'right',
			closeAction: 'hide',
			closable: true,
			plain: true,
			iconCls: 'x-deluge-add-window-icon'
		}, config);
		Deluge.add.AddWindow.superclass.constructor.call(this, config);
	},

	initComponent: function() {
		Deluge.add.AddWindow.superclass.initComponent.call(this);

		this.addButton(_('Cancel'), this.onCancelClick, this);
		this.addButton(_('Add'), this.onAddClick, this);
	
		function torrentRenderer(value, p, r) {
			if (r.data['info_hash']) {
				return String.format('<div class="x-deluge-add-torrent-name">{0}</div>', value);
			} else {
				return String.format('<div class="x-deluge-add-torrent-name-loading">{0}</div>', value);
			}
		}
	
		this.grid = this.add({
			xtype: 'grid',
			region: 'center',
			store: new Ext.data.SimpleStore({
				fields: [
					{name: 'info_hash', mapping: 1},
					{name: 'text', mapping: 2}
				],
				id: 0
			}),
			columns: [{
				id: 'torrent',
				width: 150,
				sortable: true,
				renderer: torrentRenderer,
				dataIndex: 'text'
			}],	
			stripeRows: true,
			selModel: new Ext.grid.RowSelectionModel({
				singleSelect: true,
				listeners: {
					'rowselect': {
						fn: this.onSelect,
						scope: this
					}
				}
			}),
			hideHeaders: true,
			autoExpandColumn: 'torrent',
			deferredRender: false,
			autoScroll: true,
			margins: '5 5 5 5',
			bbar: new Ext.Toolbar({
				items: [{
					iconCls: 'x-deluge-add-file',
					text: _('File'),
					handler: this.onFile,
					scope: this
				}, {
					text: _('Url'),
					iconCls: 'icon-add-url',
					handler: this.onUrl,
					scope: this
				}, {
					text: _('Infohash'),
					iconCls: 'icon-add-magnet',
					disabled: true
				}, '->', {
					text: _('Remove'),
					iconCls: 'icon-remove',
					handler: this.onRemove,
					scope: this
				}]
			})
		});
	
		this.optionsPanel = this.add(new Deluge.add.OptionsPanel());
		this.on('hide', this.onHide, this);
		this.on('show', this.onShow, this);
	},

	clear: function() {
		this.grid.getStore().removeAll();
		this.optionsPanel.clear();
	},

	onAddClick: function() {
		var torrents = [];
		if (!this.grid) return;
		this.grid.getStore().each(function(r) {
			var id = r.get('info_hash');
			torrents.push({
				path: this.optionsPanel.getFilename(id),
				options: this.optionsPanel.getOptions(id)
			});
		}, this);

		deluge.client.web.add_torrents(torrents, {
			success: function(result) {
			}
		})
		this.clear();
		this.hide();
	},

	onCancelClick: function() {
		this.clear();
		this.hide();
	},

	onFile: function() {
		this.file.show();
	},

	onHide: function() {
		this.optionsPanel.setActiveTab(0);
		this.optionsPanel.files.setDisabled(true);
		this.optionsPanel.form.setDisabled(true);
	},

	onRemove: function() {
		var selection = this.grid.getSelectionModel();
		if (!selection.hasSelection()) return;
		var torrent = selection.getSelected();
		this.grid.getStore().remove(torrent);
		this.optionsPanel.clear();
		
		if (this.torrents && this.torrents[torrent.id]) delete this.torrents[torrent.id];
	},

	onSelect: function(selModel, rowIndex, record) {
		this.optionsPanel.setTorrent(record.get('info_hash'));
		this.optionsPanel.files.setDisabled(false);
		this.optionsPanel.form.setDisabled(false);
	},

	onShow: function() {
		if (!this.url) {
			this.url = new Deluge.add.UrlWindow();
			this.url.on('beforeadd', this.onTorrentBeforeAdd, this);
			this.url.on('add', this.onTorrentAdd, this);
		}

		if (!this.file) {
			this.file = new Deluge.add.FileWindow();
			this.file.on('beforeadd', this.onTorrentBeforeAdd, this);
			this.file.on('add', this.onTorrentAdd, this);
		}
	
		this.optionsPanel.getDefaults();
	},

	onTorrentBeforeAdd: function(torrentId, text) {
		var store = this.grid.getStore();
		store.loadData([[torrentId, null, text]], true);
	},

	onTorrentAdd: function(torrentId, info) {
		var r = this.grid.getStore().getById(torrentId);
		if (!info) {
			Ext.MessageBox.show({
				title: _('Error'),
				msg: _('Not a valid torrent'),
				buttons: Ext.MessageBox.OK,
				modal: false,
				icon: Ext.MessageBox.ERROR,
				iconCls: 'x-deluge-icon-error'
			});
			this.grid.getStore().remove(r);
		} else {
			r.set('info_hash', info['info_hash']);
			r.set('text', info['name']);
			this.grid.getStore().commitChanges();
			this.optionsPanel.addTorrent(info);
		}
	},

	onUrl: function(button, event) {
		this.url.show();
	}
});
