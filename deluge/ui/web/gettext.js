/*
 * Script: gettext.js
 *  A script file that is run through the template renderer in order for
 *  translated strings to be used.
 *
 * Copyright:
 *  Damien Churchill (c) 2009
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

function _(string) {
    return GetText.get(string);
}

// deluge-torrents.js:102
GetText.add('#', '${_("#")}');

// deluge-menus.js:155
GetText.add('0', '${_("0")}');

// deluge-menus.js:157
GetText.add('1', '${_("1")}');

// deluge-menus.js:103, deluge-menus.js:121
GetText.add('10 KiB/s', '${_("10 KiB/s")}');

// deluge-menus.js:139
GetText.add('100', '${_("100")}');

// deluge-menus.js:159
GetText.add('2', '${_("2")}');

// deluge-menus.js:141
GetText.add('200', '${_("200")}');

// deluge-menus.js:161
GetText.add('3', '${_("3")}');

// deluge-menus.js:105, deluge-menus.js:123
GetText.add('30 KiB/s', '${_("30 KiB/s")}');

// deluge-menus.js:143
GetText.add('300', '${_("300")}');

// deluge-menus.js:109, deluge-menus.js:127
GetText.add('300 KiB/s', '${_("300 KiB/s")}');

// deluge-menus.js:163
GetText.add('5', '${_("5")}');

// deluge-menus.js:101, deluge-menus.js:119
GetText.add('5 KiB/s', '${_("5 KiB/s")}');

// deluge-menus.js:137
GetText.add('50', '${_("50")}');

// deluge-menus.js:145
GetText.add('500', '${_("500")}');

// deluge-menus.js:107, deluge-menus.js:125
GetText.add('80 KiB/s', '${_("80 KiB/s")}');

// deluge-bars.js:41, deluge-add.js:467, deluge-add.js:527, deluge-add.js:552, deluge-connections.js:219, deluge-connections.js:291
GetText.add('Add', '${_("Add")}');

// deluge-connections.js:248
GetText.add('Add Connection', '${_("Add Connection")}');

// deluge-add.js:387
GetText.add('Add In Paused State', '${_("Add In Paused State")}');

// deluge-add.js:542
GetText.add('Add Torrents', '${_("Add Torrents")}');

// deluge-add.js:463
GetText.add('Add from File', '${_("Add from File")}');

// deluge-add.js:523
GetText.add('Add from Url', '${_("Add from Url")}');

// deluge-preferences.js:173
GetText.add('Add torrents in Paused state', '${_("Add torrents in Paused state")}');

// deluge-torrents.js:169
GetText.add('Added', '${_("Added")}');

// deluge-add.js:305, deluge-preferences.js:146
GetText.add('Allocation', '${_("Allocation")}');

// deluge-preferences.js:355
GetText.add('Allow Remote Connections', '${_("Allow Remote Connections")}');

// deluge-details.js:692, deluge-preferences.js:42
GetText.add('Apply', '${_("Apply")}');

// deluge-add.js:396
GetText.add('Apply to All', '${_("Apply to All")}');

// deluge-details.js:638, deluge-menus.js:170
GetText.add('Auto Managed', '${_("Auto Managed")}');

// deluge-torrents.js:163
GetText.add('Avail', '${_("Avail")}');

// deluge-details.js:552, deluge-add.js:330, deluge-preferences.js:183
GetText.add('Bandwidth', '${_("Bandwidth")}');

// deluge-menus.js:198
GetText.add('Bottom', '${_("Bottom")}');

// deluge-add.js:291, deluge-add.js:449
GetText.add('Browse', '${_("Browse")}');

// deluge-add.js:546
GetText.add('Cancel', '${_("Cancel")}');

// deluge-preferences.js:50
GetText.add('Categories', '${_("Categories")}');

// deluge-connections.js:286, deluge-connections.js:312, deluge-preferences.js:38
GetText.add('Close', '${_("Close")}');

// deluge-add.js:322, deluge-preferences.js:153
GetText.add('Compact', '${_("Compact")}');

// deluge-connections.js:149, deluge-connections.js:315
GetText.add('Connect', '${_("Connect")}');

// deluge-connections.js:95, deluge-connections.js:146
GetText.add('Connected', '${_("Connected")}');

// deluge-menus.js:133
GetText.add('Connection Limit', '${_("Connection Limit")}');

// deluge-bars.js:89, deluge-connections.js:308
GetText.add('Connection Manager', '${_("Connection Manager")}');

// deluge-preferences.js:348
GetText.add('Connections', '${_("Connections")}');

// deluge-preferences.js:140
GetText.add('Copy of .torrent files to', '${_("Copy of .torrent files to")}');

// deluge-bars.js:34
GetText.add('Create', '${_("Create")}');

// deluge-menus.js:97
GetText.add('D/L Speed Limit', '${_("D/L Speed Limit")}');

// deluge-preferences.js:331
GetText.add('Daemon', '${_("Daemon")}');

// deluge-preferences.js:342
GetText.add('Daemon port', '${_("Daemon port")}');

// deluge-details.js:461
GetText.add('Details', '${_("Details")}');

// deluge-connections.js:147
GetText.add('Disconnect', '${_("Disconnect")}');

// deluge-menus.js:386
GetText.add('Do Not Download', '${_("Do Not Download")}');

// deluge-bars.js:76, deluge-menus.js:192
GetText.add('Down', '${_("Down")}');

// deluge-torrents.js:139
GetText.add('Down Speed', '${_("Down Speed")}');

// deluge-add.js:272
GetText.add('Download Location', '${_("Download Location")}');

// deluge-preferences.js:132
GetText.add('Download to', '${_("Download to")}');

// deluge-preferences.js:119
GetText.add('Downloads', '${_("Downloads")}');

// deluge-torrents.js:151
GetText.add('ETA', '${_("ETA")}');

// deluge-details.js:683, deluge-menus.js:212
GetText.add('Edit Trackers', '${_("Edit Trackers")}');

// deluge-add.js:142, deluge-connections.js:61, deluge-connections.js:129, deluge-connections.js:164
GetText.add('Error', '${_("Error")}');

// deluge-menus.js:382
GetText.add('Expand All', '${_("Expand All")}');

// deluge-add.js:224, deluge-add.js:446
GetText.add('File', '${_("File")}');

// deluge-details.js:477, deluge-add.js:181
GetText.add('Filename', '${_("Filename")}');

// deluge-details.js:471, deluge-add.js:259
GetText.add('Files', '${_("Files")}');

// deluge-bars.js:509
GetText.add('Filters', '${_("Filters")}');

// deluge-preferences.js:126
GetText.add('Folders', '${_("Folders")}');

// deluge-menus.js:224
GetText.add('Force Recheck', '${_("Force Recheck")}');

// deluge-add.js:316, deluge-preferences.js:157
GetText.add('Full', '${_("Full")}');

// deluge-details.js:662, deluge-add.js:379
GetText.add('General', '${_("General")}');

// deluge-preferences.js:191
GetText.add('Global Bandwidth Usage', '${_("Global Bandwidth Usage")}');

// deluge-bars.js:98
GetText.add('Help', '${_("Help")}');

// deluge-preferences.js:305
GetText.add('Hide filters with zero torrents', '${_("Hide filters with zero torrents")}');

// deluge-menus.js:396
GetText.add('High Priority', '${_("High Priority")}');

// deluge-menus.js:401
GetText.add('Highest Priority', '${_("Highest Priority")}');

// deluge-connections.js:256
GetText.add('Host', '${_("Host")}');

// deluge-preferences.js:238
GetText.add('Ignore limits on local network', '${_("Ignore limits on local network")}');

// deluge-add.js:237
GetText.add('Infohash', '${_("Infohash")}');

// deluge-preferences.js:278
GetText.add('Interface', '${_("Interface")}');

// deluge-details.js:85, deluge-details.js:148
GetText.add('Loading', '${_("Loading")}');

// deluge-login.js:37, deluge-login.js:51
GetText.add('Login', '${_("Login")}');

// deluge-login.js:93
GetText.add('Login Failed', '${_("Login Failed")}');

// deluge-bars.js:106
GetText.add('Logout', '${_("Logout")}');

// deluge-details.js:596, deluge-add.js:357
GetText.add('Max Connections', '${_("Max Connections")}');

// deluge-add.js:337
GetText.add('Max Down Speed', '${_("Max Down Speed")}');

// deluge-details.js:560
GetText.add('Max Download Speed', '${_("Max Download Speed")}');

// deluge-add.js:347
GetText.add('Max Up Speed', '${_("Max Up Speed")}');

// deluge-details.js:611, deluge-add.js:367
GetText.add('Max Upload Slots', '${_("Max Upload Slots")}');

// deluge-details.js:578
GetText.add('Max Upload Speed', '${_("Max Upload Speed")}');

// deluge-preferences.js:223
GetText.add('Maximum Connection Attempts per Second', '${_("Maximum Connection Attempts per Second")}');

// deluge-preferences.js:198, deluge-preferences.js:257
GetText.add('Maximum Connections', '${_("Maximum Connections")}');

// deluge-preferences.js:208, deluge-preferences.js:267
GetText.add('Maximum Download Speed (KiB/s)', '${_("Maximum Download Speed (KiB/s)")}');

// deluge-preferences.js:218
GetText.add('Maximum Half-Open Connections', '${_("Maximum Half-Open Connections")}');

// deluge-preferences.js:203, deluge-preferences.js:262
GetText.add('Maximum Upload Slots', '${_("Maximum Upload Slots")}');

// deluge-preferences.js:213, deluge-preferences.js:272
GetText.add('Maximum Upload Speed (KiB/s)', '${_("Maximum Upload Speed (KiB/s)")}');

// deluge-details.js:653
GetText.add('Move Completed', '${_("Move Completed")}');

// deluge-menus.js:230
GetText.add('Move Storage', '${_("Move Storage")}');

// deluge-preferences.js:136
GetText.add('Move completed to', '${_("Move completed to")}');

// deluge-torrents.js:109
GetText.add('Name', '${_("Name")}');

// deluge-preferences.js:177
GetText.add('Network', '${_("Network")}');

// deluge-menus.js:391
GetText.add('Normal Priority', '${_("Normal Priority")}');

// deluge-bars.js:350
GetText.add('Not Connected', '${_("Not Connected")}');

// deluge-add.js:143
GetText.add('Not a valid torrent', '${_("Not a valid torrent")}');

// deluge-preferences.js:386
GetText.add('Notification', '${_("Notification")}');

// deluge-preferences.js:44
GetText.add('Ok', '${_("Ok")}');

// deluge-details.js:535, deluge-add.js:263, deluge-menus.js:93, deluge-preferences.js:162
GetText.add('Options', '${_("Options")}');

// deluge-menus.js:277, deluge-menus.js:324, deluge-menus.js:371, deluge-preferences.js:325, deluge-preferences.js:361
GetText.add('Other', '${_("Other")}');

// deluge-connections.js:278, deluge-login.js:63, deluge-preferences.js:311
GetText.add('Password', '${_("Password")}');

// deluge-bars.js:55, deluge-menus.js:81
GetText.add('Pause', '${_("Pause")}');

// deluge-details.js:512, deluge-torrents.js:133
GetText.add('Peers', '${_("Peers")}');

// deluge-preferences.js:251
GetText.add('Per Torrent Bandwidth Usage', '${_("Per Torrent Bandwidth Usage")}');

// deluge-preferences.js:369
GetText.add('Periodically check the website for new releases', '${_("Periodically check the website for new releases")}');

// deluge-preferences.js:392
GetText.add('Plugins', '${_("Plugins")}');

// deluge-connections.js:262, deluge-preferences.js:338
GetText.add('Port', '${_("Port")}');

// deluge-bars.js:82, deluge-preferences.js:36
GetText.add('Preferences', '${_("Preferences")}');

// deluge-details.js:674
GetText.add('Prioritize First/Last', '${_("Prioritize First/Last")}');

// deluge-add.js:392
GetText.add('Prioritize First/Last Piece', '${_("Prioritize First/Last Piece")}');

// deluge-preferences.js:169
GetText.add('Prioritize first and last pieces of torrent', '${_("Prioritize first and last pieces of torrent")}');

// deluge-details.js:491
GetText.add('Priority', '${_("Priority")}');

// deluge-details.js:669
GetText.add('Private', '${_("Private")}');

// deluge-details.js:486, deluge-torrents.js:121
GetText.add('Progress', '${_("Progress")}');

// deluge-preferences.js:380
GetText.add('Proxy', '${_("Proxy")}');

// deluge-details.js:631, deluge-menus.js:175, deluge-preferences.js:374
GetText.add('Queue', '${_("Queue")}');

// deluge-preferences.js:245
GetText.add('Rate limit IP overhead', '${_("Rate limit IP overhead")}');

// deluge-torrents.js:157
GetText.add('Ratio', '${_("Ratio")}');

// deluge-bars.js:48, deluge-add.js:243, deluge-connections.js:225
GetText.add('Remove', '${_("Remove")}');

// deluge-menus.js:218
GetText.add('Remove Torrent', '${_("Remove Torrent")}');

// deluge-details.js:648
GetText.add('Remove at ratio', '${_("Remove at ratio")}');

// deluge-bars.js:62, deluge-menus.js:87
GetText.add('Resume', '${_("Resume")}');

// deluge-add.js:400
GetText.add('Revert to Defaults', '${_("Revert to Defaults")}');

// deluge-torrents.js:127
GetText.add('Seeders', '${_("Seeders")}');

// deluge-add.js:445
GetText.add('Select a torrent', '${_("Select a torrent")}');

// deluge-preferences.js:292
GetText.add('Show session speed in titlebar', '${_("Show session speed in titlebar")}');

// deluge-preferences.js:298
GetText.add('Sidebar', '${_("Sidebar")}');

// deluge-details.js:481, deluge-add.js:185, deluge-torrents.js:115
GetText.add('Size', '${_("Size")}');

// deluge-bars.js:356
GetText.add('State', '${_("State")}');

// deluge-details.js:452
GetText.add('Status', '${_("Status")}');

// deluge-connections.js:231
GetText.add('Stop Daemon', '${_("Stop Daemon")}');

// deluge-details.js:643
GetText.add('Stop seed at ratio', '${_("Stop seed at ratio")}');

// deluge-menus.js:180
GetText.add('Top', '${_("Top")}');

// deluge-torrents.js:175
GetText.add('Tracker', '${_("Tracker")}');

// deluge-bars.js:357
GetText.add('Tracker Host', '${_("Tracker Host")}');

// deluge-menus.js:115
GetText.add('U/L Speed Limit', '${_("U/L Speed Limit")}');

// deluge-menus.js:111, deluge-menus.js:129, deluge-menus.js:147, deluge-menus.js:165, deluge-menus.js:271, deluge-menus.js:318, deluge-menus.js:365
GetText.add('Unlimited', '${_("Unlimited")}');

// deluge-bars.js:69, deluge-menus.js:186
GetText.add('Up', '${_("Up")}');

// deluge-torrents.js:145
GetText.add('Up Speed', '${_("Up Speed")}');

// deluge-menus.js:206
GetText.add('Update Tracker', '${_("Update Tracker")}');

// deluge-menus.js:151
GetText.add('Upload Slot Limit', '${_("Upload Slot Limit")}');

// deluge-add.js:420
GetText.add('Uploading your torrent...', '${_("Uploading your torrent...")}');

// deluge-add.js:230, deluge-add.js:500
GetText.add('Url', '${_("Url")}');

// deluge-connections.js:272
GetText.add('Username', '${_("Username")}');

// deluge-preferences.js:285
GetText.add('Window', '${_("Window")}');

// deluge-login.js:94
GetText.add('You entered an incorrect password', '${_("You entered an incorrect password")}');


