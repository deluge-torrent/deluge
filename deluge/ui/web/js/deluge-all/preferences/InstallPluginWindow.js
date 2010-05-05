/*!
 * Deluge.preferences.InstallPluginWindow.js
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
Ext.namespace('Deluge.preferences');

/**
 * @class Deluge.preferences.InstallPluginWindow
 * @extends Ext.Window
 */
Deluge.preferences.InstallPluginWindow = Ext.extend(Ext.Window, {

	title: _('Install Plugin'),
	layout: 'fit',
	height: 115,
	width: 350,
	
	bodyStyle: 'padding: 10px 5px;',
	buttonAlign: 'center',
	closeAction: 'hide',
	iconCls: 'x-deluge-install-plugin',
	modal: true,
	plain: true,

	initComponent: function() {
		Deluge.add.FileWindow.superclass.initComponent.call(this);
		this.addButton(_('Install'), this.onInstall, this);
		
		this.form = this.add({
			xtype: 'form',
			baseCls: 'x-plain',
			labelWidth: 70,
			autoHeight: true,
			fileUpload: true,
			items: [{
				xtype: 'fileuploadfield',
				width: 240,
				emptyText: _('Select an egg'),
				fieldLabel: _('Plugin Egg'),
				name: 'file',
				buttonCfg: {
					text: _('Browse') + '...'
				}
			}]
		});
	},

	onInstall: function(field, e) {
		this.form.getForm().submit({
			url: '/upload',
			waitMsg: _('Uploading your plugin...'),
			success: this.onUploadSuccess,
			scope: this
		}); 
	},

	onUploadPlugin: function(info, obj, response, request) {
		this.fireEvent('pluginadded');
	},

	onUploadSuccess: function(fp, upload) {
		this.hide();
		if (upload.result.success) {
			var filename = this.form.getForm().getFieldValues().file;
			filename = filename.split('\\').slice(-1)[0]
			var path = upload.result.files[0];
			this.form.getForm().setValues({file: ''});
			deluge.client.web.upload_plugin(filename, path, {
				success: this.onUploadPlugin,
				scope: this,
				filename: filename
			});
		}
	}
});
