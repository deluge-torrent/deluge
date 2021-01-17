/**
 * Deluge.StatusbarMenu.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */
Ext.ns('Deluge');

/**
 * Menu that handles setting the statusbar limits correctly.
 * @class Deluge.StatusbarMenu
 * @extends Ext.menu.Menu
 */
Deluge.StatusbarMenu = Ext.extend(Ext.menu.Menu, {
    initComponent: function () {
        Deluge.StatusbarMenu.superclass.initComponent.call(this);
        this.otherWin = new Deluge.OtherLimitWindow(
            this.initialConfig.otherWin || {}
        );

        this.items.each(function (item) {
            if (item.getXType() != 'menucheckitem') return;
            if (item.value == 'other') {
                item.on('click', this.onOtherClicked, this);
            } else {
                item.on('checkchange', this.onLimitChanged, this);
            }
        }, this);
    },

    setValue: function (value) {
        var beenSet = false;
        // set the new value
        this.value = value = value == 0 ? -1 : value;

        var other = null;
        // uncheck all items
        this.items.each(function (item) {
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

    onLimitChanged: function (item, checked) {
        if (!checked || item.value == 'other') return; // We do not care about unchecked or other.
        var config = {};
        config[item.group] = item.value;
        deluge.client.core.set_config(config, {
            success: function () {
                deluge.ui.update();
            },
        });
    },

    onOtherClicked: function (item, e) {
        this.otherWin.group = item.group;
        this.otherWin.setValue(this.value);
        this.otherWin.show();
    },
});
