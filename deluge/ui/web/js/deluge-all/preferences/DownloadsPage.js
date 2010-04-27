/*!
 * Deluge.preferences.DownloadsPage.js
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
 * @class Deluge.preferences.Downloads
 * @extends Ext.form.FormPanel
 */
Deluge.preferences.Downloads = Ext.extend(Ext.FormPanel, {
	constructor: function(config) {
		config = Ext.apply({
			border: false,
			title: _('Downloads'),
			layout: 'form',
			autoHeight: true,
			width: 320
		}, config);
		Deluge.preferences.Downloads.superclass.constructor.call(this, config);
	},

	initComponent: function() {
		Deluge.preferences.Downloads.superclass.initComponent.call(this);

		var optMan = deluge.preferences.getOptionsManager();
		var fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Folders'),
			labelWidth: 150,
			defaultType: 'togglefield',
			autoHeight: true,
			labelAlign: 'top',
			width: 300,
			style: 'margin-bottom: 5px; padding-bottom: 5px;'
		});

		optMan.bind('download_location', fieldset.add({
			xtype: 'textfield',
			name: 'download_location',
			fieldLabel: _('Download to'),
			width: 280
		}));

		var field = fieldset.add({
			name: 'move_completed_path',
			fieldLabel: _('Move completed to'),
			width: 280
		});
		optMan.bind('move_completed', field.toggle);
		optMan.bind('move_completed_path', field.input);

		field = fieldset.add({
			name: 'torrentfiles_location',
			fieldLabel: _('Copy of .torrent files to'),
			width: 280
		});
		optMan.bind('copy_torrent_file', field.toggle);
		optMan.bind('torrentfiles_location', field.input);

		field = fieldset.add({
			name: 'autoadd_location',
			fieldLabel: _('Autoadd .torrent files from'),
			width: 280
		});
		optMan.bind('autoadd_enable', field.toggle);
		optMan.bind('autoadd_location', field.input);
	
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Allocation'),
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'radiogroup',
			style: 'margin-bottom: 5px; margin-top: 0; padding-bottom: 5px; padding-top: 0;',
			width: 240
		});
		optMan.bind('compact_allocation', fieldset.add({
			name: 'compact_allocation',
			width: 200,
			labelSeparator: '',
			//disabled: true,
			defaults: {
				width: 80,
				height: 22,
				name: 'compact_allocation'
			},
			items: [{
				boxLabel: _('Use Full'),
				inputValue: false
			}, {
				boxLabel: _('Use Compact'),
				inputValue: true
			}]
		}));
	
		fieldset = this.add({
			xtype: 'fieldset',
			border: false,
			title: _('Options'),
			autoHeight: true,
			labelWidth: 1,
			defaultType: 'checkbox',
			style: 'margin-bottom: 0; padding-bottom: 0;',
			width: 280
		});
		optMan.bind('prioritize_first_last_pieces', fieldset.add({
			name: 'prioritize_first_last_pieces',
			labelSeparator: '',
			height: 22,
			boxLabel: _('Prioritize first and last pieces of torrent')
		}));
		optMan.bind('add_paused', fieldset.add({
			name: 'add_paused',
			labelSeparator: '',
			height: 22,
			boxLabel: _('Add torrents in Paused state')
		}));
	}
});
