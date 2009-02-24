/*
Script: deluge-add.js
    Contains the Add Torrent window.

Copyright:
	(C) Damien Churchill 2009 <damoxc@gmail.com>
	This program is free software; you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation; either version 3, or (at your option)
	any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, write to:
		The Free Software Foundation, Inc.,
		51 Franklin Street, Fifth Floor
		Boston, MA  02110-1301, USA.
*/

Deluge.Add = {
	onRender: function(window) {
		
	}
}

Deluge.Add.Window = new Ext.Window({
	layout: 'fit',
    width: 300,
    height: 150,
    buttonAlign: 'right',
    closeAction: 'hide',
    closable: true,
    plain: true,
    title: _('Add Torrent'),
    iconCls: 'x-deluge-add-window-icon',
    items: [],
    buttons: [{
        text: _('Cancel')
    }, {
		text: _('Add')
	}],
    listeners: {'render': {fn: Deluge.Add.onRender, scope: Deluge.Add}}
});