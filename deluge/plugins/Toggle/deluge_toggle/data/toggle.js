/**
 * Script: toggle.js
 *   The client-side javascript code for the Toggle plugin.
 *
 * Copyright (C) John Garland 2010 <johnnybg+deluge@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */

TogglePlugin = Ext.extend(Deluge.Plugin, {
    constructor: function (config) {
        config = Ext.apply(
            {
                name: 'Toggle',
            },
            config
        );
        TogglePlugin.superclass.constructor.call(this, config);
    },

    onDisable: function () {},

    onEnable: function () {},
});
new TogglePlugin();
