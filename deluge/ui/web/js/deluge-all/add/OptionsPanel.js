/*!
 * Deluge.add.OptionsPanel.js
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
Ext.ns('Deluge.add');

Deluge.add.OptionsPanel = Ext.extend(Ext.TabPanel, {

	torrents: {},

	// layout options
	region: 'south',
	margins: '5 5 5 5',
	activeTab: 0,
	height: 220,

	initComponent: function() {
		Deluge.add.OptionsPanel.superclass.initComponent.call(this);
		this.files = this.add(new Ext.ux.tree.TreeGrid({
			layout: 'fit',
			title: _('Files'),
			autoScroll: true,
			border: false,
			animate: false,
			disabled: true,
			rootVisible: false,

			columns: [{
				header: _('Filename'),
				width: 275,
				dataIndex: 'filename'
			},{
				xtype: 'tgrendercolumn',
				header: _('Size'),
				width: 80,
				dataIndex: 'size',
				renderer: fsize
			}]
		}));

		new Ext.tree.TreeSorter(this.files, {
			folderSort: true
		});

		this.optionsManager = new Deluge.MultiOptionsManager();
	
		this.form = this.add({
			xtype: 'form',
			labelWidth: 1,
			title: _('Options'),
			bodyStyle: 'padding: 5px;',
			border: false,
			height: 170,
			disabled: true
		});
	
		var fieldset = this.form.add({
			xtype: 'fieldset',
			title: _('Download Location'),
			border: false,
			autoHeight: true,
			defaultType: 'textfield',
			labelWidth: 1,
			fieldLabel: '',
			style: 'padding-bottom: 5px; margin-bottom: 0px;'
		});
		this.optionsManager.bind('download_location', fieldset.add({
			fieldLabel: '',
			name: 'download_location',
			width: 400,
			labelSeparator: ''
		}));
	
		var panel = this.form.add({
			border: false,
			layout: 'column',
			defaultType: 'fieldset'
		});
		fieldset = panel.add({
			title: _('Allocation'),
			border: false,
			autoHeight: true,
			defaultType: 'radio',
			width: 100
		});

		this.optionsManager.bind('compact_allocation', fieldset.add({
			xtype: 'radiogroup',
			columns: 1,
			vertical: true,
			disabled: true,
			labelSeparator: '',
			items: [{
				name: 'compact_allocation',
				value: false,
				inputValue: false,
				boxLabel: _('Full'),
				fieldLabel: '',
				labelSeparator: ''
			}, {
				name: 'compact_allocation',
				value: true,
				inputValue: true,
				boxLabel: _('Compact'),
				fieldLabel: '',
				labelSeparator: '',
			}]
		}));

		fieldset = panel.add({
			title: _('Bandwidth'),
			border: false,
			autoHeight: true,
			labelWidth: 100,
			width: 200,
			defaultType: 'spinnerfield'
		});
		this.optionsManager.bind('max_download_speed', fieldset.add({
			fieldLabel: _('Max Down Speed'),
			labelStyle: 'margin-left: 10px',
			name: 'max_download_speed',
			width: 60
		}));
		this.optionsManager.bind('max_upload_speed', fieldset.add({
			fieldLabel: _('Max Up Speed'),
			labelStyle: 'margin-left: 10px',
			name: 'max_upload_speed',
			width: 60
		}));
		this.optionsManager.bind('max_connections', fieldset.add({
			fieldLabel: _('Max Connections'),
			labelStyle: 'margin-left: 10px',
			name: 'max_connections',
			width: 60
		}));
		this.optionsManager.bind('max_upload_slots', fieldset.add({
			fieldLabel: _('Max Upload Slots'),
			labelStyle: 'margin-left: 10px',
			name: 'max_upload_slots',
			width: 60
		}));
	
		fieldset = panel.add({
			title: _('General'),
			border: false,
			autoHeight: true,
			defaultType: 'checkbox'
		});
		this.optionsManager.bind('add_paused', fieldset.add({
			name: 'add_paused',
			boxLabel: _('Add In Paused State'),
			fieldLabel: '',
			labelSeparator: '',
		}));
		this.optionsManager.bind('prioritize_first_last_pieces', fieldset.add({
			name: 'prioritize_first_last_pieces',
			boxLabel: _('Prioritize First/Last Pieces'),
			fieldLabel: '',
			labelSeparator: '',
		}));
	
		this.form.on('render', this.onFormRender, this);
	},

	onFormRender: function(form) {
		form.layout = new Ext.layout.FormLayout();
		form.layout.setContainer(form);
		form.doLayout();
	},

	addTorrent: function(torrent) {
		this.torrents[torrent['info_hash']] = torrent;
		var fileIndexes = {};
		this.walkFileTree(torrent['files_tree'], function(filename, type, entry, parent) {
			if (type != 'file') return;
			fileIndexes[entry[0]] = entry[2];
		}, this);

		var priorities = [];
		Ext.each(Ext.keys(fileIndexes), function(index) {
			priorities[index] = fileIndexes[index];
		});
		
		var oldId = this.optionsManager.changeId(torrent['info_hash'], true);
		this.optionsManager.setDefault('file_priorities', priorities);
		this.optionsManager.changeId(oldId, true);
	},

	clear: function() {
		this.clearFiles();
		this.optionsManager.resetAll();
	},

	clearFiles: function() {
		var root = this.files.getRootNode();
		if (!root.hasChildNodes()) return;
		root.cascade(function(node) {
			if (!node.parentNode || !node.getOwnerTree()) return;
			node.remove();
		});
	},

	getDefaults: function() {
		var keys = ['add_paused','compact_allocation','download_location',
		'max_connections_per_torrent','max_download_speed_per_torrent',
		'max_upload_slots_per_torrent','max_upload_speed_per_torrent',
		'prioritize_first_last_pieces'];

		deluge.client.core.get_config_values(keys, {
			success: function(config) {
				var options = {
					'file_priorities': [],
					'add_paused': config.add_paused,
					'compact_allocation': config.compact_allocation,
					'download_location': config.download_location,
					'max_connections': config.max_connections_per_torrent,
					'max_download_speed': config.max_download_speed_per_torrent,
					'max_upload_slots': config.max_upload_slots_per_torrent,
					'max_upload_speed': config.max_upload_speed_per_torrent,
					'prioritize_first_last_pieces': config.prioritize_first_last_pieces
				}
				this.optionsManager.options = options;
				this.optionsManager.resetAll();
			},
			scope: this
		});
	},

	getFilename: function(torrentId) {
		return this.torrents[torrentId]['filename'];
	},

	getOptions: function(torrentId) {
		var oldId = this.optionsManager.changeId(torrentId, true);
		var options = this.optionsManager.get();
		this.optionsManager.changeId(oldId, true);
		Ext.each(options['file_priorities'], function(priority, index) {
			options['file_priorities'][index] = (priority) ? 1 : 0;
		});
		return options;
	},

	setTorrent: function(torrentId) {
		if (!torrentId) return;

		this.torrentId = torrentId;
		this.optionsManager.changeId(torrentId);
	
		this.clearFiles();
		var root = this.files.getRootNode();
		var priorities = this.optionsManager.get('file_priorities');

		this.walkFileTree(this.torrents[torrentId]['files_tree'], function(filename, type, entry, parentNode) {
			if (type == 'dir') {
				alert(Ext.encode(entry));
				var folder = new Ext.tree.TreeNode({
					filename: filename,
					checked: true
				});
				folder.on('checkchange', this.onFolderCheck, this);
				parentNode.appendChild(folder);
				return folder;
			} else {
				var node = new Ext.tree.TreeNode({
					filename: filename,
					fileindex: entry[0],
					text: filename, // this needs to be here for sorting reasons
					size: entry[1],
					leaf: true,
					checked: priorities[entry[0]],
					iconCls: 'x-deluge-file',
					uiProvider: Ext.tree.ColumnNodeUI
				});
				node.on('checkchange', this.onNodeCheck, this);
				parentNode.appendChild(node);
			}
		}, this, root);
		root.firstChild.expand();
	},

	walkFileTree: function(files, callback, scope, parentNode) {
		for (var filename in files) {
			var entry = files[filename];
			var type = (Ext.type(entry) == 'object') ? 'dir' : 'file';

			if (scope) {
				var ret = callback.apply(scope, [filename, type, entry, parentNode]);
			} else {
				var ret = callback(filename, type, entry, parentNode);
			}
		
			if (type == 'dir') this.walkFileTree(entry, callback, scope, ret);
		}
	},

	onFolderCheck: function(node, checked) {
		var priorities = this.optionsManager.get('file_priorities');
		node.cascade(function(child) {
			if (!child.ui.checkbox) {
				child.attributes.checked = checked;
			} else {
				child.ui.checkbox.checked = checked;
			}
			priorities[child.attributes.fileindex] = checked;
		}, this);
		this.optionsManager.setDefault('file_priorities', priorities);
	},

	onNodeCheck: function(node, checked) {
		var priorities = this.optionsManager.get('file_priorities');
		priorities[node.attributes.fileindex] = checked;
		this.optionsManager.update('file_priorities', priorities);
	}
});
