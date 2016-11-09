/*!
 * Deluge.js
 * 
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */

// Setup the state manager
Ext.state.Manager.setProvider(new Ext.state.CookieProvider({
    /**
     * By default, cookies will expire after 7 days. Provide
     * an expiry date 10 years in the future to approximate
     * a cookie that does not expire.
     */
    expires: new Date(new Date().getTime() + (1000 * 60 * 60 * 24 * 365 * 10))
}));

// Add some additional functions to ext and setup some of the
// configurable parameters
Ext.apply(Ext, {
    escapeHTML: function(text) {
        text = String(text).replace('<', '&lt;').replace('>', '&gt;');
        return text.replace('&', '&amp;');
    },

    isObjectEmpty: function(obj) {
        for(var i in obj) { return false; }
        return true;
    },

    areObjectsEqual: function(obj1, obj2) {
        var equal = true;
        if (!obj1 || !obj2) return false;
        for (var i in obj1) {
            if (obj1[i] != obj2[i]) {
                equal = false;
            }
        }
        return equal;
    },
    
    keys: function(obj) {
        var keys = [];
        for (var i in obj) if (obj.hasOwnProperty(i))
        {
            keys.push(i);
        }
        return keys;
    },

    values: function(obj) {
        var values = [];
        for (var i in obj) {
            if (obj.hasOwnProperty(i)) {
                values.push(obj[i]);
            }
        }
        return values;
    },
        
    splat: function(obj) {
        var type = Ext.type(obj);
        return (type) ? ((type != 'array') ? [obj] : obj) : [];
    }
});
Ext.getKeys = Ext.keys;
Ext.BLANK_IMAGE_URL = deluge.config.base + 'images/s.gif';
Ext.USE_NATIVE_JSON = true;

// Create the Deluge namespace
Ext.apply(Deluge, {

    // private
    pluginStore: {},

    // private
    progressTpl:    '<div class="x-progress-wrap x-progress-renderered">' +
                        '<div class="x-progress-inner">' +
                            '<div style="width: {2}px" class="x-progress-bar">' +
                                '<div style="z-index: 99; width: {3}px" class="x-progress-text">' +
                                    '<div style="width: {1}px;white-space:pre;">{0}</div>' +
                                '</div>' +
                            '</div>' +
                            '<div class="x-progress-text x-progress-text-back">' +
                                '<div style="width: {1}px;white-space:pre;">{0}</div>' +
                            '</div>' +
                        '</div>' +
                    '</div>',


    /**
     * A method to create a progress bar that can be used by renderers
     * to display a bar within a grid or tree.
     * @param {Number} progress The bars progress
     * @param {Number} width The width of the bar
     * @param {String} text The text to display on the bar
     * @param {Number} modified Amount to subtract from the width allowing for fixes
     */
    progressBar: function(progress, width, text, modifier) {
        modifier = Ext.value(modifier, 10);
        var progressWidth = ((width / 100.0) * progress).toFixed(0);
        var barWidth = progressWidth - 1;
        var textWidth = ((progressWidth - modifier) > 0 ? progressWidth - modifier : 0);
        return String.format(Deluge.progressTpl, text, width, barWidth, textWidth);
    },

    /**
     * Constructs a new instance of the specified plugin.
     * @param {String} name The plugin name to create
     */
    createPlugin: function(name) {
        return new Deluge.pluginStore[name]();
    },

    /**
     * Check to see if a plugin has been registered.
     * @param {String} name The plugin name to check
     */
    hasPlugin: function(name) {
        return (Deluge.pluginStore[name]) ? true : false;
    },

    /**
     * Register a plugin with the Deluge interface.
     * @param {String} name The plugin name to register
     * @param {Plugin} plugin The plugin to register
     */
    registerPlugin: function(name, plugin) {
        Deluge.pluginStore[name] = plugin;
    }
    
});

// Setup a space for plugins to insert themselves
deluge.plugins = {};

// Hinting for gettext_gen.py
// _('Do Not Download')
// _('Normal Priority')
// _('High Priority')
// _('Highest Priority')
FILE_PRIORITY = {
    9: 'Mixed',
    0: 'Do Not Download',
    1: 'Normal Priority',
    2: 'High Priority',
    5: 'High Priority',
    7: 'Highest Priority',
    'Mixed': 9,
    'Do Not Download': 0,
    'Normal Priority': 1,
    'High Priority': 5,
    'Highest Priority': 7
}

FILE_PRIORITY_CSS = {
    9: 'x-mixed-download',
    0: 'x-no-download',
    1: 'x-normal-download',
    2: 'x-high-download',
    5: 'x-high-download',
    7: 'x-highest-download'
}
