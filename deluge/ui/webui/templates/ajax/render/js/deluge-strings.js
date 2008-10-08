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

// Torrent Menu Strings //
Deluge.Strings.add('Pause', '$_('Pause')');
Deluge.Strings.add('Resume', '$_('Resume')');
Deluge.Strings.add('Options', '$_('Options')');
Deluge.Strings.add('D/L Speed Limit', '$_('D/L Speed Limit')');
Deluge.Strings.add('U/L Speed Limit', '$_('U/L Speed Limit')');
Deluge.Strings.add('Unlimited', '$_('Unlimited')');
Deluge.Strings.add('Connection Limit', '$_('Connection Limit')');
Deluge.Strings.add('Upload Slot Limit', '$_('Upload Slot Limit')');
Deluge.Strings.add('Auto Managed', '$_('Auto Managed')');
Deluge.Strings.add('Queue', '$_('Queue')');
Deluge.Strings.add('Top', '$_('Top')');
Deluge.Strings.add('Up', '$_('Up')');
Deluge.Strings.add('Down', '$_('Down')');
Deluge.Strings.add('Bottom', '$_('Bottom')');
Deluge.Strings.add('Update Tracker', '$_('Update Tracker')');
Deluge.Strings.add('Edit Trackers', '$_('Edit Trackers')');
Deluge.Strings.add('Remove Torrent', '$_('Remove Torrent')');
Deluge.Strings.add('From Session', '$_('From Session')');
Deluge.Strings.add('... and delete Torrent file',
    '$_('... and delete Torrent file')');
Deluge.Strings.add('... and delete Downloaded files',
    '$_('... and delete Downloaded files')');
Deluge.Strings.add('... and delete All files',
    '$_('... and delete All files')');
Deluge.Strings.add('Force Recheck', '$_('Force Recheck')');
Deluge.Strings.add('Move Storage', '$_('Move Storage')');

// Add Torrents Window //
Deluge.Strings.add('Add Torrents', '$_('Add Torrents')');
Deluge.Strings.add('Create Torrent', '$_('Create Torrent')');
Deluge.Strings.add('Torrents Window', '$_('Torrents Window')');
Deluge.Strings.add('From Url', '$_('From Url')');
Deluge.Strings.add('Ok', '$_('Ok')');
Deluge.Strings.add('Cancel', '$_('Cancel')');
