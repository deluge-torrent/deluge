/*!
 * Deluge.add.File.js
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

/**
 * @class Deluge.add.FileWindow
 * @extends Deluge.add.Window
 */
Deluge.add.FileWindow = Ext.extend(Deluge.add.Window, {

	title: _('Add from File'),
	layout: 'fit',
	width: 350,
	height: 115,
	modal: true,
	plain: true,
	buttonAlign: 'center',
	closeAction: 'hide',
	bodyStyle: 'padding: 10px 5px;',
	iconCls: 'x-deluge-add-file',

	initComponent: function() {
		Deluge.add.FileWindow.superclass.initComponent.call(this);
		this.addButton(_('Add'), this.onAddClick, this);

		this.form = this.add({
			xtype: 'form',
			baseCls: 'x-plain',
			labelWidth: 35,
			autoHeight: true,
			fileUpload: true,
			items: [{
				xtype: 'fileuploadfield',
				id: 'torrentFile',
				width: 280,
				height: 24,
				emptyText: _('Select a torrent'),
				fieldLabel: _('File'),
				name: 'file',
				buttonCfg: {
					text: _('Browse') + '...'
				}
			}]
		});
	},

	// private
	onAddClick: function(field, e) {
		if (this.form.getForm().isValid()) {
			this.torrentId = this.createTorrentId();
			this.form.getForm().submit({
				url: deluge.config.base + 'upload',
				waitMsg: _('Uploading your torrent...'),
				failure: this.onUploadFailure,
				success: this.onUploadSuccess,
				scope: this
			});
			var name = this.form.getForm().findField('torrentFile').value;
			name = name.split('\\').slice(-1)[0];
			this.fireEvent('beforeadd', this.torrentId, name);
		}
	},

	// private
	onGotInfo: function(info, obj, response, request) {
		info['filename'] = request.options.filename;
		this.fireEvent('add', this.torrentId, info);
	},

	// private
	onUploadFailure: function(form, action) {
		this.hide();
	},

	// private
	onUploadSuccess: function(fp, upload) {
		this.hide();
		if (upload.result.success) {
			var filename = upload.result.files[0];
			this.form.getForm().findField('torrentFile').setValue('');
			deluge.client.web.get_torrent_info(filename, {
				success: this.onGotInfo,
				scope: this,
				filename: filename
			});
		}
	}
});
