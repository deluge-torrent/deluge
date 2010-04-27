/*!
 * label.js
 * 
 * Copyright (c) Damien Churchill 2010 <damoxc@gmail.com>
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
Ext.ns('Deluge.ux');

/**
 * @class Deluge.ux.AddLabelWindow
 * @extends Ext.Window
 */
Deluge.ux.AddLabelWindow = Ext.extend(Ext.Window, {
	
	title: _('Add Label'),
	width: 300,
	height: 100,

	initComponent: function() {
		Deluge.ux.AddLabelWindow.superclass.initComponent.call(this);
		this.addButton(_('Cancel'), this.onCancelClick, this);
		this.addButton(_('Ok'), this.onOkClick, this);

		this.form = this.add({
			xtype: 'form',
			height: 35,
			bodyStyle:'padding:5px 5px 0',
			defaultType: 'textfield',
			labelWidth: 50,
			items: [{
				fieldLabel: _('Name'),
				name: 'name',
				allowBlank: false,
				width: 220,
				listeners: {
					'specialkey': {
						fn: function(field, e) {
							if (e.getKey() == 13) this.onOkClick();
						},
						scope: this
					}
				}
			}]
		});
	},

	onCancelClick: function() {
		this.hide();
	},

	onOkClick: function() {
		var label = this.form.getForm().getValues().name;
		deluge.client.label.add(label, {
			success: function() {
				deluge.ui.update();
				this.fireEvent('labeladded', label);
			},
			scope: this
		});
		this.hide();
	},

	onHide: function(comp) {
		Deluge.ux.AddLabelWindow.superclass.onHide.call(this, comp);
		this.form.getForm().reset();
	},

	onShow: function(comp) {
		Deluge.ux.AddLabelWindow.superclass.onShow.call(this, comp);
		this.form.getForm().findField('name').focus(false, 150);
	}

});

/**
 * @class Deluge.ux.LabelOptionsWindow
 * @extends Ext.Window
 */
Deluge.ux.LabelOptionsWindow = Ext.extend(Ext.Window, {

	title: _('Label Options'),
	width:  325,
	height: 240,
	
	initComponent: function() {
		Deluge.ux.LabelOptionsWindow.superclass.initComponent.call(this);
		this.addButton(_('Cancel'), this.onCancelClick, this);
		this.addButton(_('Ok'), this.onOkClick, this);

		this.form = this.add({
			xtype: 'form'
		});

		this.tabs = this.form.add({
			xtype: 'tabpanel',
			height: 175,
			border: false,
			items: [{
				title: _('Maximum'),
				items: [{
					border: false,
					items: [{
						xtype: 'fieldset',
						border: false,
						labelWidth: 1,
						style: 'margin-bottom: 0px; padding-bottom: 0px;',
						items: [{
							xtype: 'checkbox',
							fieldLabel: '',
							boxLabel: _('Apply per torrent max settings:')
						}]
					}, {
						xtype: 'fieldset',
						border: false,
						defaultType: 'spinnerfield',
						style: 'margin-top: 0px; padding-top: 0px;',
						items: [{
							fieldLabel: _('Download Speed'),
							name: 'down_speed',
							width: 80,
							disabled: true,
							value: -1
						}, {
							fieldLabel: _('Upload Speed'),
							name: 'up_speed',
							width: 80,
							disabled: true,
							value: -1
						}, {
							fieldLabel: _('Upload Slots'),
							name: 'upload_slots',
							width: 80,
							disabled: true,
							value: -1
						}, {
							fieldLabel: _('Connections'),
							name: 'connections',
							width: 80,
							disabled: true,
							value: -1
						}]
					}]
				}]
			}, {
				title: _('Queue'),
				items: [{
					border: false,
					items: [{
						xtype: 'fieldset',
						border: false,
						labelWidth: 1,
						style: 'margin-bottom: 0px; padding-bottom: 0px;',
						items: [{
							xtype: 'checkbox',
							fieldLabel: '',
							boxLabel: _('Apply queue settings:')
						}]
					}, {
						xtype: 'fieldset',
						border: false,
						labelWidth: 1,
						defaultType: 'checkbox',
						style: 'margin-top: 0px; padding-top: 0px;',
						defaults: {
							style: 'margin-left: 20px'
						},
						items: [{
							boxLabel: _('Auto Managed'),
							name: 'auto_managed',
							disabled: true
						}, {
							boxLabel: _('Stop seed at ratio:'),
							name: 'up_speed',
							disabled: true
						}, {
							boxLabel: _('Remove at ratio'),
							name: 'upload_slots',
							disabled: true
						}]
					}]
				}]
			}, {
				title: _('Location'),
				items: [{
					border: false,
					items: [{
						xtype: 'fieldset',
						border: false,
						labelWidth: 1,
						style: 'margin-bottom: 0px; padding-bottom: 0px;',
						items: [{
							xtype: 'checkbox',
							fieldLabel: '',
							boxLabel: _('Apply location settings:')
						}]
					}, {
						xtype: 'fieldset',
						border: false,
						labelWidth: 1,
						defaultType: 'checkbox',
						labelWidth: 1,
						style: 'margin-top: 0px; padding-top: 0px;',
						defaults: {
							style: 'margin-left: 20px'
						},
						items: [{
							boxLabel: _('Move completed to:'),
							name: 'move_completed',
							disabled: true
						}, {
							xtype: 'textfield',
							name: 'move_completed_path',
							width: 250,
							disabled: true
						}]
					}]
				}]
			}, {
				title: _('Trackers'),
				items: [{
					border: false,
					items: [{
						xtype: 'fieldset',
						border: false,
						labelWidth: 1,
						style: 'margin-bottom: 0px; padding-bottom: 0px;',
						items: [{
							xtype: 'checkbox',
							fieldLabel: '',
							boxLabel: _('Automatically apply label:')
						}]
					}, {
						xtype: 'fieldset',
						border: false,
						labelWidth: 1,
						style: 'margin-top: 0px; padding-top: 0px;',
						defaults: {
							style: 'margin-left: 20px'
						},
						defaultType: 'textarea',
						items: [{
							boxLabel: _('Move completed to:'),
							name: 'trackers',
							width: 250,
							height: 100,
							disabled: true
						}]
					}]
				}]
			}]
		});
	},

	show: function(label) {
		Deluge.ux.LabelOptionsWindow.superclass.show.call(this);
		this.label = label;
		this.setTitle(_('Label Options') + ': ' + this.label); 
		this.tabs.setActiveTab(0);
	},

	onCancelClick: function() {
		this.hide();
	},

	onOkClick: function() {
		this.hide();
	}

});


Ext.ns('Deluge.plugins');

/**
 * @class Deluge.plugins.LabelPlugin
 * @extends Deluge.Plugin
 */
Deluge.plugins.LabelPlugin = Ext.extend(Deluge.Plugin, {

	name: 'Label',

	createMenu: function() {
		this.labelMenu = new Ext.menu.Menu({
			items: [{
				text: _('Add Label'),
				iconCls: 'icon-add',
				handler: this.onLabelAddClick,
				scope: this
			}, {
				text: _('Remove Label'),
				disabled: true,
				iconCls: 'icon-remove',
				handler: this.onLabelRemoveClick,
				scope: this
			}, {
				text: _('Label Options'),
				disabled: true,
				handler: this.onLabelOptionsClick,
				scope: this
			}]
		});
	},

	setFilter: function(filter) {
		filter.show_zero = true;
		filter.list.on('contextmenu', this.onLabelContextMenu, this);
		filter.header.on('contextmenu', this.onLabelHeaderContextMenu, this);
		this.filter = filter;
	},

	updateTorrentMenu: function(filter) {
		Ext.each(filter.getStates(), function(state) {
			if (!state) return;
			this.torrentMenu.addMenuItem({
				text: state,
				label: state,
				handler: this.onTorrentMenuClick,
				scope: this
			});
		}, this);
	},
	
	onDisable: function() {
		deluge.sidebar.un('filtercreate', this.onFilterCreate);
		deluge.sidebar.un('afterfiltercreate', this.onAfterFilterCreate);
		delete Deluge.FilterPanel.templates.label;
	    this.deregisterTorrentStatus('label');
		deluge.menus.torrent.remove(this.tmSep);
		deluge.menus.torrent.remove(this.tm);
	},
	
	onEnable: function() {
		if (deluge.sidebar.hasFilter('label')) {
			var filter = deluge.sidebar.getFilter('label');
			this.setFilter(filter);
			this.updateTorrentMenu(filter);
		} else {
			deluge.sidebar.on('filtercreate', this.onFilterCreate, this);
			deluge.sidebar.on('afterfiltercreate', this.onAfterFilterCreate, this);
			Deluge.FilterPanel.templates.label = '<div class="x-deluge-filter x-deluge-{filter:lowercase}"><tpl if="filter">{filter}</tpl><tpl if="!filter">no label</tpl> ({count})</div>';
		}
		this.registerTorrentStatus('label', _('Label'));

		this.torrentMenu = new Ext.menu.Menu({
			items: [{
				text: _('No Label'),
				label: '',
				handler: this.onTorrentMenuClick,
				scope: this
			}]
		});

		this.tmSep = deluge.menus.torrent.add({
			xtype: 'menuseparator'
		});

		this.tm = deluge.menus.torrent.add({
			text: _('Label'),
			menu: this.torrentMenu
		})
	},

	onAfterFilterCreate: function(sidebar, filter) {
		if (filter.filter != 'label') return;
		this.updateTorrentMenu(filter);
	},

	onFilterCreate: function(sidebar, filter) {
		if (filter.filter != 'label') return;
		this.setFilter(filter);
	},

	onLabelAddClick: function() {
		if (!this.addWindow) {
			this.addWindow = new Deluge.ux.AddLabelWindow();
			this.addWindow.on('labeladded', this.onLabelAdded, this);
		}
		this.addWindow.show();
	},

	onLabelAdded: function(label) {
		this.torrentMenu.addMenuItem({
			text: label,
			label: label,
			handler: this.onTorrentMenuClick,
			scope: this
		});
	},

	onLabelContextMenu: function(dv, i, node, e) {
		e.preventDefault();
		if (!this.labelMenu) this.createMenu();
		var r = dv.getRecord(node);
		if (dv.getRecord(node).get('filter')) {
			this.labelMenu.items.get(1).setDisabled(false);
			this.labelMenu.items.get(2).setDisabled(false);
		}

		dv.select(i);
		this.labelMenu.showAt(e.getXY());
	},

	onLabelHeaderContextMenu: function(e, t) {
		e.preventDefault();
		if (!this.labelMenu) this.createMenu();
		this.labelMenu.items.get(1).setDisabled(true);
		this.labelMenu.items.get(2).setDisabled(true);
		this.labelMenu.showAt(e.getXY());
	},

	onLabelOptionsClick: function() {
		if (!this.labelOpts) this.labelOpts = new Deluge.ux.LabelOptionsWindow();
		this.labelOpts.show(this.filter.getState());
	},

	onLabelRemoveClick: function() {
		var state = this.filter.getFilter();
		deluge.client.label.remove(state, {
			success: function() {
				deluge.ui.update();
				this.torrentMenu.items.each(function(item) {
					if (item.text != state) return;
					this.torrentMenu.remove(item);
					var i = item;
				}, this);
			},
			scope: this
		});
	},

	onTorrentMenuClick: function(item, e) {
		var ids = deluge.torrents.getSelectedIds();
		Ext.each(ids, function(id, i) {
			if (ids.length == i +1 ) {
				deluge.client.label.set_torrent(id, item.label, {
					success: function() {
						deluge.ui.update();
					}
				});
			} else {
				deluge.client.label.set_torrent(id, item.label);
			}
		});
	}
});
Deluge.registerPlugin('Label', Deluge.plugins.LabelPlugin);
