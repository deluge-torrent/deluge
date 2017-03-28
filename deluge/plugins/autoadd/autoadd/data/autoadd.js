/*
Script: autoadd.js
    The client-side javascript code for the AutoAdd plugin.

Copyright:
    (C) GazpachoKing 2009 <damoxc@gmail.com>
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

    In addition, as a special exception, the copyright holders give
    permission to link the code of portions of this program with the OpenSSL
    library.
    You must obey the GNU General Public License in all respects for all of
    the code used other than OpenSSL. If you modify file(s) with this
    exception, you may extend this exception to your version of the file(s),
    but you are not obligated to do so. If you do not wish to do so, delete
    this exception statement from your version. If you delete this exception
    statement from all source files in the program, then also delete it here.
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
