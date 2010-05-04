/*!
 * Deluge.Statusbar.js
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
Ext.namespace('Deluge');

Deluge.Statusbar = Ext.extend(Ext.ux.StatusBar, {
	constructor: function(config) {
		config = Ext.apply({
			id: 'deluge-statusbar',
			defaultIconCls: 'x-deluge-statusbar x-not-connected',
			defaultText: _('Not Connected')
		}, config);
		Deluge.Statusbar.superclass.constructor.call(this, config);
	},
	
	initComponent: function() {
		Deluge.Statusbar.superclass.initComponent.call(this);
		
		deluge.events.on('connect', this.onConnect, this);
		deluge.events.on('disconnect', this.onDisconnect, this);
	},
	
	createButtons: function() {
		this.buttons = this.add({
			id: 'statusbar-connections',
			text: ' ',
			cls: 'x-btn-text-icon',
			iconCls: 'x-deluge-connections',
			tooltip: _('Connections'),
			menu: new Deluge.StatusbarMenu({
				items: [{
					text: '50',
					value: '50',
					group: 'max_connections_global',
					checked: false
				},{
					text: '100',
					value: '100',
					group: 'max_connections_global',
					checked: false
				},{
					text: '200',
					value: '200',
					group: 'max_connections_global',
					checked: false
				},{
					text: '300',
					value: '300',
					group: 'max_connections_global',
					checked: false
				},{
					text: '500',
					value: '500',
					group: 'max_connections_global',
					checked: false
				},{
					text: _('Unlimited'),
					value: '-1',
					group: 'max_connections_global',
					checked: false
				},'-',{
					text: _('Other'),
					value: 'other',
					group: 'max_connections_global',
					checked: false
				}],
				otherWin: {
					title: _('Set Maximum Connections')
				}
			})
		}, '-', {
			id: 'statusbar-downspeed',
			text: ' ',
			cls: 'x-btn-text-icon',
			iconCls: 'x-deluge-downloading',
			tooltip: _('Download Speed'),
			menu: new Deluge.StatusbarMenu({
				items: [{
					value: '5',
					text: '5 KiB/s',
					group: 'max_download_speed',
					checked: false
				},{
					value: '10',
					text: '10 KiB/s',
					group: 'max_download_speed',
					checked: false
				},{
					value: '30',
					text: '30 KiB/s',
					group: 'max_download_speed',
					checked: false
				},{
					value: '80',
					text: '80 KiB/s',
					group: 'max_download_speed',
					checked: false
				},{
					value: '300',
					text: '300 KiB/s',
					group: 'max_download_speed',
					checked: false
				},{
					value: '-1',
					text: _('Unlimited'),
					group: 'max_download_speed',
					checked: false
				},'-',{
					value: 'other',
					text: _('Other'),
					group: 'max_download_speed',
					checked: false
				}],
				otherWin: {
					title: _('Set Maximum Download Speed'),
					unit: _('Kib/s')
				}
			})
		}, '-', {
			id: 'statusbar-upspeed',
			text: ' ',
			cls: 'x-btn-text-icon',
			iconCls: 'x-deluge-seeding',
			tooltip: _('Upload Speed'),
			menu: new Deluge.StatusbarMenu({
				items: [{
					value: '5',
					text: '5 KiB/s',
					group: 'max_upload_speed',
					checked: false
				},{
					value: '10',
					text: '10 KiB/s',
					group: 'max_upload_speed',
					checked: false
				},{
					value: '30',
					text: '30 KiB/s',
					group: 'max_upload_speed',
					checked: false
				},{
					value: '80',
					text: '80 KiB/s',
					group: 'max_upload_speed',
					checked: false
				},{
					value: '300',
					text: '300 KiB/s',
					group: 'max_upload_speed',
					checked: false
				},{
					value: '-1',
					text: _('Unlimited'),
					group: 'max_upload_speed',
					checked: false
				},'-',{
					value: 'other',
					text: _('Other'),
					group: 'max_upload_speed',
					checked: false
				}],
				otherWin: {
					title: _('Set Maximum Upload Speed'),
					unit: _('Kib/s')
				}
			})
		}, '-', {
			id: 'statusbar-traffic',
			text: ' ',
			cls: 'x-btn-text-icon',
			iconCls: 'x-deluge-traffic',
			tooltip: _('Protocol Traffic Download/Upload'),
			handler: function() {
				deluge.preferences.show();
				deluge.preferences.selectPage('Network');
			}
		}, '-', {
			id: 'statusbar-dht',
			text: ' ',
			cls: 'x-btn-text-icon',
			iconCls: 'x-deluge-dht',
			tooltip: _('DHT Nodes')
		}, '-', {
			id: 'statusbar-freespace',
			text: ' ',
			cls: 'x-btn-text-icon',
			iconCls: 'x-deluge-freespace',
			tooltip: _('Freespace in download location'),
			handler: function() {
				deluge.preferences.show();
				deluge.preferences.selectPage('Downloads');
			}
		});
		this.created = true;
	},
	
	onConnect: function() {
		this.setStatus({
			iconCls: 'x-connected',
			text: ''
		});
		if (!this.created) {
			this.createButtons();
		} else {
			Ext.each(this.buttons, function(item) {
				item.show();
				item.enable();
			});
		}
		this.doLayout();
	},

	onDisconnect: function() {
		this.clearStatus({useDefaults:true});
		Ext.each(this.buttons, function(item) {
			item.hide();
			item.disable();
		});
		this.doLayout();
	},
	
	update: function(stats) {
		if (!stats) return;
		
		function addSpeed(val) {return val + ' KiB/s'}
		
		var updateStat = function(name, config) {
			var item = this.items.get('statusbar-' + name);
			if (config.limit.value > 0) {
				var value = (config.value.formatter) ? config.value.formatter(config.value.value, true) : config.value.value;
				var limit = (config.limit.formatter) ? config.limit.formatter(config.limit.value, true) : config.limit.value;
				var str = String.format(config.format, value, limit);
			} else {
				var str = (config.value.formatter) ? config.value.formatter(config.value.value, true) : config.value.value;
			}
			item.setText(str);

			if (!item.menu) return;
			item.menu.setValue(config.limit.value);
		}.createDelegate(this);
		
		updateStat('connections', {
			value: {value: stats.num_connections},
			limit: {value: stats.max_num_connections},
			format: '{0} ({1})'
		});

		updateStat('downspeed', {
			value: {
				value: stats.download_rate,
				formatter: Deluge.Formatters.speed
			},
			limit: {
				value: stats.max_download,
				formatter: addSpeed
			},
			format: '{0} ({1})'
		});

		updateStat('upspeed', {
			value: {
				value: stats.upload_rate,
				formatter: Deluge.Formatters.speed
			},
			limit: {
				value: stats.max_upload,
				formatter: addSpeed
			},
			format: '{0} ({1})'
		});

		updateStat('traffic', {
			value: {
				value: stats.download_protocol_rate,
				formatter: Deluge.Formatters.speed
			},
			limit: {
				value: stats.upload_protocol_rate,
				formatter: Deluge.Formatters.speed
			},
			format: '{0}/{1}'
		});

		this.items.get('statusbar-dht').setText(stats.dht_nodes);
		this.items.get('statusbar-freespace').setText(fsize(stats.free_space));
	}
});
