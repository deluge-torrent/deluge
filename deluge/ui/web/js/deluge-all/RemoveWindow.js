/*!
 * Deluge.RemoveWindow.js
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

/**
 * @class Deluge.RemoveWindow
 * @extends Ext.Window
 */
Deluge.RemoveWindow = Ext.extend(Ext.Window, {
    
    title:  _('Remove Torrent'),
    layout: 'fit',
    width:  350,
	height: 100,
    
    buttonAlign: 'right',
    closeAction: 'hide',
    closable:    true,
    iconCls:     'x-deluge-remove-window-icon',
    plain:       true,
    
    bodyStyle: 'padding: 5px; padding-left: 10px;',
    html: 'Are you sure you wish to remove the torrent (s)?',
	
	initComponent: function() {
		Deluge.RemoveWindow.superclass.initComponent.call(this);
		this.addButton(_('Cancel'), this.onCancel, this);
		this.addButton(_('Remove With Data'), this.onRemoveData, this);
		this.addButton(_('Remove Torrent'), this.onRemove, this);
	},
	
	remove: function(removeData) {
		Ext.each(this.torrentIds, function(torrentId) {
			deluge.client.core.remove_torrent(torrentId, removeData, {
				success: function() {
					this.onRemoved(torrentId);
				},
				scope: this,
				torrentId: torrentId
			});
		}, this);
		
	},
	
	show: function(ids) {
		Deluge.RemoveWindow.superclass.show.call(this);
		this.torrentIds = ids;
	},
	
	onCancel: function() {
		this.hide();
		this.torrentIds = null;
	},
	
	onRemove: function() {
		this.remove(false);
	},
	
	onRemoveData: function() {
		this.remove(true);
	},
	
	onRemoved: function(torrentId) {
		deluge.events.fire('torrentRemoved', torrentId);
		this.hide();
		deluge.ui.update();
	}
});

deluge.removeWindow = new Deluge.RemoveWindow();
