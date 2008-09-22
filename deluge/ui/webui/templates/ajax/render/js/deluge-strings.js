/*
 * Script: deluge-strings.js
 *  A script file that is run through the template renderer in order for
 *  translated strings to be retrieved.
 *
 * Copyright:
 *   Damien Churchill (c) 2008
 */

Deluge.Strings = {
    maps: {},
    add: function(string, translation) {
        this.maps[string] = translation;
    },
    get: function(string) {
        if (this.maps[string]) {
            return this.maps[string];
        } else {
            return string;
        }
    }
}
Deluge.Strings.add('Pause', '$_('Pause')');
Deluge.Strings.add('Resume', '$_('Resume')');
Deluge.Strings.add('Options', '$_('Options')');
Deluge.Strings.add('Torrents Window', '$_('Torrents Window')');
