/*!
 * Deluge.StatusbarMenu.js
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
Ext.ns('Deluge');

/**
 * Menu that handles setting the statusbar limits correctly.
 * @class Deluge.StatusbarMenu
 * @extends Ext.menu.Menu
 */
Deluge.StatusbarMenu = Ext.extend(Ext.menu.Menu, {
	
	initComponent: function() {
		Deluge.StatusbarMenu.superclass.initComponent.call(this);
		this.otherWin = new Deluge.OtherLimitWindow(this.initialConfig.otherWin || {});

		this.items.each(function(item) {
			if (item.getXType() != 'menucheckitem') return;
			if (item.value == 'other') {
				item.on('click', this.onOtherClicked, this);
			} else {
				item.on('checkchange', this.onLimitChanged, this);
			}
		}, this);
	},
    
    setValue: function(value) {
        var beenSet = false;
        // set the new value
        this.value = value = (value == 0) ? -1 : value;

        var other = null;
        // uncheck all items
        this.items.each(function(item) {
            if (item.setChecked) {
                item.suspendEvents();
                if (item.value == value) {
                    item.setChecked(true);
                    beenSet = true;
                } else {
                    item.setChecked(false);
                }   
                item.resumeEvents();
            }   

            if (item.value == 'other') other = item;
        }); 

        if (beenSet) return;

        other.suspendEvents();
        other.setChecked(true);
        other.resumeEvents();
    },

	onLimitChanged: function(item, checked) {
		if (!checked || item.value == 'other') return; // we don't care about unchecks or other
		var config = {}
		config[item.group] = item.value
		deluge.client.core.set_config(config, {
			success: function() {
				deluge.ui.update();
			}
		});
	},

	onOtherClicked: function(item, e) {
		this.otherWin.group = item.group;
		this.otherWin.setValue(this.value);
		this.otherWin.show();
	}
});
