/*
 * Script: gettext.js
 *  A script file that is run through the template renderer in order for
 *  translated strings to be retrieved.
 *
 * Copyright:
 *   Damien Churchill (c) 2008
 */

GetText = {
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
GetText.add('Pause', '$_('Pause')');
GetText.add('Resume', '$_('Resume')');
GetText.add('Options', '$_('Options')');
GetText.add('D/L Speed Limit', '$_('D/L Speed Limit')');
GetText.add('U/L Speed Limit', '$_('U/L Speed Limit')');
GetText.add('Unlimited', '$_('Unlimited')');
GetText.add('Connection Limit', '$_('Connection Limit')');
GetText.add('Upload Slot Limit', '$_('Upload Slot Limit')');
GetText.add('Auto Managed', '$_('Auto Managed')');
GetText.add('Queue', '$_('Queue')');
GetText.add('Top', '$_('Top')');
GetText.add('Up', '$_('Up')');
GetText.add('Down', '$_('Down')');
GetText.add('Bottom', '$_('Bottom')');
GetText.add('Update Tracker', '$_('Update Tracker')');
GetText.add('Edit Trackers', '$_('Edit Trackers')');
GetText.add('Remove Torrent', '$_('Remove Torrent')');
GetText.add('From Session', '$_('From Session')');
GetText.add('... and delete Torrent file',
    '$_('... and delete Torrent file')');
GetText.add('... and delete Downloaded files',
    '$_('... and delete Downloaded files')');
GetText.add('... and delete All files',
    '$_('... and delete All files')');
GetText.add('Force Recheck', '$_('Force Recheck')');
GetText.add('Move Storage', '$_('Move Storage')');

// Add Torrents Window //
GetText.add('Add Torrents', '$_('Add Torrents')');
GetText.add('Create Torrent', '$_('Create Torrent')');
GetText.add('Torrents Window', '$_('Torrents Window')');
GetText.add('From Url', '$_('From Url')');
GetText.add('Ok', '$_('Ok')');
GetText.add('Cancel', '$_('Cancel')');


// Details //
GetText.add('Statistics', '$_('Statistics')');
GetText.add('Details', '$_('Details')');
GetText.add('Files', '$_('Files')');
GetText.add('Peers', '$_('Peers')');
GetText.add('Options', '$_('Options')');

function _(string) {
	return GetText.get(string);
}
