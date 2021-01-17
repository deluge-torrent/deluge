/**
 * Script: stats.js
 *      The javascript client-side code for the Stats plugin.
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */

StatsPlugin = Ext.extend(Deluge.Plugin, {
    constructor: function (config) {
        config = Ext.apply(
            {
                name: 'Stats',
            },
            config
        );
        StatsPlugin.superclass.constructor.call(this, config);
    },

    onDisable: function () {},

    onEnable: function () {},
});
new StatsPlugin();
