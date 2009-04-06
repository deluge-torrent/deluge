/*
 * Script: gettext.js
 *  A script file that is run through the template renderer in order for
 *  translated strings to be retrieved.
 *
 *
 * Copyright (C) Damien Churchill 2008 <damoxc@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, write to:
 *     The Free Software Foundation, Inc.,
 *     51 Franklin Street, Fifth Floor
 *     Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

 *
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
