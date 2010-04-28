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
		this.files = this.add(new Deluge.add.FilesTab());
		this.form = this.add(new Deluge.add.OptionsTab());

		this.files.on('fileschecked', this.onFilesChecked, this);
	},

	addTorrent: function(torrent) {
		this.torrents[torrent['info_hash']] = torrent;
		var fileIndexes = {};
		this.walkFileTree(torrent['files_tree'], function(filename, type, entry, parent) {
			if (type != 'file') return;
			fileIndexes[entry.index] = entry.download;
		}, this);

		var priorities = [];
		Ext.each(Ext.keys(fileIndexes), function(index) {
			priorities[index] = fileIndexes[index];
		});
		
		var oldId = this.form.optionsManager.changeId(torrent['info_hash'], true);
		this.form.optionsManager.setDefault('file_priorities', priorities);
		this.form.optionsManager.changeId(oldId, true);
	},

	clear: function() {
		this.files.clearFiles();
		this.form.optionsManager.resetAll();
	},

	getFilename: function(torrentId) {
		return this.torrents[torrentId]['filename'];
	},

	getOptions: function(torrentId) {
		var oldId = this.form.optionsManager.changeId(torrentId, true);
		var options = this.form.optionsManager.get();
		this.form.optionsManager.changeId(oldId, true);
		Ext.each(options['file_priorities'], function(priority, index) {
			options['file_priorities'][index] = (priority) ? 1 : 0;
		});
		return options;
	},

	setTorrent: function(torrentId) {
		if (!torrentId) return;

		this.torrentId = torrentId;
		this.form.optionsManager.changeId(torrentId);
	
		this.files.clearFiles();
		var root = this.files.getRootNode();
		var priorities = this.form.optionsManager.get('file_priorities');

		this.walkFileTree(this.torrents[torrentId]['files_tree'], function(filename, type, entry, parentNode) {
			var node = new Ext.tree.TreeNode({
				download:  (entry.index) ? priorities[entry.index] : true,
				filename:  filename,
				fileindex: entry.index,
				leaf:      type != 'dir',
				size:      entry.length
			});
			parentNode.appendChild(node);
			if (type == 'dir') return node;
		}, this, root);
		root.firstChild.expand();
	},

	walkFileTree: function(files, callback, scope, parentNode) {
		for (var filename in files.contents) {
			var entry = files.contents[filename];
			var type = entry.type;

			if (scope) {
				var ret = callback.apply(scope, [filename, type, entry, parentNode]);
			} else {
				var ret = callback(filename, type, entry, parentNode);
			}
		
			if (type == 'dir') this.walkFileTree(entry, callback, scope, ret);
		}
	},

	onFilesChecked: function(nodes, newValue, oldValue) {
		if (this.form.optionsManager.get('compact_allocation')) {
			Ext.Msg.show({
				title: _('Unable to set file priority!'),
				msg:   _('File prioritization is unavailable when using Compact allocation. Would you like to switch to Full allocation?'),
				buttons: Ext.Msg.YESNO,
				fn: function(result) {
					if (result == 'yes') {
						this.form.optionsManager.update('compact_allocation', false);
						Ext.each(nodes, function(node) {
							if (node.attributes.fileindex < 0) return;
							var priorities = this.form.optionsManager.get('file_priorities');
							priorities[node.attributes.fileindex] = newValue;
							this.form.optionsManager.update('file_priorities', priorities);
						}, this);
					} else {
						this.files.setDownload(nodes[0], oldValue, true);
					}	
				},
				scope: this,
				icon: Ext.MessageBox.QUESTION
			});
		} else {
			Ext.each(nodes, function(node) {
				if (node.attributes.fileindex < 0) return;
				var priorities = this.form.optionsManager.get('file_priorities');
				priorities[node.attributes.fileindex] = newValue;
				this.form.optionsManager.update('file_priorities', priorities);
			}, this);
		}
	}
});
