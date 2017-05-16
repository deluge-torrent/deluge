/*!
 * Script: autoadd.js
 *      The client-side javascript code for the AutoAdd plugin.
 *
 * Copyright (C) 2009 GazpachoKing <chase.sterling@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */

Ext.ns('Deluge.ux.preferences');

/**
 * @class Deluge.ux.preferences.AutoAddPage
 * @extends Ext.Panel
 */
Deluge.ux.preferences.AutoAddPage = Ext.extend(Ext.Panel, {

    title: _('AutoAdd'),
    layout: 'fit',
    border: false,

    initComponent: function() {
        Deluge.ux.preferences.AutoAddPage.superclass.initComponent.call(this);
        fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            title: _('AutoAdd Preferences'),
            autoHeight: true,
            labelWidth: 1,
            defaultType: 'panel'
        });
        fieldset.add({
            border: false,
            bodyCfg: {
                html: _('<p>The AutoAdd plugin is enabled however there is no WebUI ' +
                        'preferences page implemented yet for this plugin.</p><br>' +
                        '<p>In the meantime please use GtkUI preference page to configure this plugin.<p>')
            }
        });
    }
});

Deluge.plugins.AutoAddPlugin = Ext.extend(Deluge.Plugin, {
    name: 'AutoAdd',

    onDisable: function() {
        deluge.preferences.removePage(this.prefsPage);
    },

    onEnable: function() {
        this.prefsPage = deluge.preferences.addPage(new Deluge.ux.preferences.AutoAddPage());
    }
});

Deluge.registerPlugin('AutoAdd', Deluge.plugins.AutoAddPlugin);
