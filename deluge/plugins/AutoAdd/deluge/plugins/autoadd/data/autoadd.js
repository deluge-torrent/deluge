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

AutoAddPlugin = Ext.extend(Deluge.Plugin, {
    constructor: function(config) {
        config = Ext.apply({
            name: "AutoAdd"
        }, config);
        AutoAddPlugin.superclass.constructor.call(this, config);
    },

    onDisable: function() {

    },

    onEnable: function() {

    }
});
new AutoAddPlugin();
