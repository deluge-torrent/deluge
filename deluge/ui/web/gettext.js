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

// Deluge.Torrents.js:113
GetText.add('#', '${_("#").replace("'", "\'")}');

// Deluge.Menus.js:169
GetText.add('0', '${_("0").replace("'", "\'")}');

// Deluge.Menus.js:171
GetText.add('1', '${_("1").replace("'", "\'")}');

// Deluge.Menus.js:117, Deluge.Menus.js:135
GetText.add('10 KiB/s', '${_("10 KiB/s").replace("'", "\'")}');

// Deluge.Menus.js:153
GetText.add('100', '${_("100").replace("'", "\'")}');

// Deluge.Menus.js:173
GetText.add('2', '${_("2").replace("'", "\'")}');

// Deluge.Menus.js:155
GetText.add('200', '${_("200").replace("'", "\'")}');

// Deluge.Menus.js:175
GetText.add('3', '${_("3").replace("'", "\'")}');

// Deluge.Menus.js:119, Deluge.Menus.js:137
GetText.add('30 KiB/s', '${_("30 KiB/s").replace("'", "\'")}');

// Deluge.Menus.js:157
GetText.add('300', '${_("300").replace("'", "\'")}');

// Deluge.Menus.js:123, Deluge.Menus.js:141
GetText.add('300 KiB/s', '${_("300 KiB/s").replace("'", "\'")}');

// Deluge.Menus.js:177
GetText.add('5', '${_("5").replace("'", "\'")}');

// Deluge.Menus.js:115, Deluge.Menus.js:133
GetText.add('5 KiB/s', '${_("5 KiB/s").replace("'", "\'")}');

// Deluge.Menus.js:151
GetText.add('50', '${_("50").replace("'", "\'")}');

// Deluge.Menus.js:159
GetText.add('500', '${_("500").replace("'", "\'")}');

// Deluge.Menus.js:121, Deluge.Menus.js:139
GetText.add('80 KiB/s', '${_("80 KiB/s").replace("'", "\'")}');

// Deluge.Toolbar.js:51, Deluge.Add.js:186, Deluge.Add.Url.js:49, Deluge.ConnectionManager.js:112, Deluge.ConnectionManager.js:370, Deluge.Add.File.js:49, Deluge.EditTrackers.js:58, Deluge.EditTrackers.js:237
GetText.add('Add', '${_("Add").replace("'", "\'")}');

// Deluge.ConnectionManager.js:327
GetText.add('Add Connection', '${_("Add Connection").replace("'", "\'")}');

// Deluge.Add.js:168
GetText.add('Add Torrents', '${_("Add Torrents").replace("'", "\'")}');

// Deluge.EditTrackers.js:39
GetText.add('Add Tracker', '${_("Add Tracker").replace("'", "\'")}');

// Deluge.Add.File.js:46
GetText.add('Add from File', '${_("Add from File").replace("'", "\'")}');

// Deluge.Add.Url.js:46
GetText.add('Add from Url', '${_("Add from Url").replace("'", "\'")}');

// Deluge.Preferences.Downloads.js:56
GetText.add('Add torrents in Paused state', '${_("Add torrents in Paused state").replace("'", "\'")}');

// Deluge.Torrents.js:180
GetText.add('Added', '${_("Added").replace("'", "\'")}');

// Deluge.Preferences.Downloads.js:29
GetText.add('Allocation', '${_("Allocation").replace("'", "\'")}');

// Deluge.Preferences.Daemon.js:26
GetText.add('Allow Remote Connections', '${_("Allow Remote Connections").replace("'", "\'")}');

// Deluge.Details.Options.js:343, Deluge.Preferences.js:55
GetText.add('Apply', '${_("Apply").replace("'", "\'")}');

// Deluge.Details.Options.js:215, Deluge.Menus.js:184
GetText.add('Auto Managed', '${_("Auto Managed").replace("'", "\'")}');

// Deluge.Torrents.js:174
GetText.add('Avail', '${_("Avail").replace("'", "\'")}');

// Deluge.Preferences.Bandwidth.js:3, Deluge.Details.Options.js:89
GetText.add('Bandwidth', '${_("Bandwidth").replace("'", "\'")}');

// Deluge.Menus.js:212
GetText.add('Bottom', '${_("Bottom").replace("'", "\'")}');

// Deluge.Add.File.js:71
GetText.add('Browse', '${_("Browse").replace("'", "\'")}');

// Deluge.Add.js:185, Deluge.EditTrackers.js:57, Deluge.EditTrackers.js:116, Deluge.EditTrackers.js:178
GetText.add('Cancel', '${_("Cancel").replace("'", "\'")}');

// Deluge.Preferences.js:64
GetText.add('Categories', '${_("Categories").replace("'", "\'")}');

// Deluge.Preferences.js:51, Deluge.ConnectionManager.js:62, Deluge.ConnectionManager.js:365
GetText.add('Close', '${_("Close").replace("'", "\'")}');

// Deluge.Preferences.Downloads.js:36
GetText.add('Compact', '${_("Compact").replace("'", "\'")}');

// Deluge.ConnectionManager.js:63, Deluge.ConnectionManager.js:272
GetText.add('Connect', '${_("Connect").replace("'", "\'")}');

// Deluge.ConnectionManager.js:197, Deluge.ConnectionManager.js:269
GetText.add('Connected', '${_("Connected").replace("'", "\'")}');

// Deluge.Menus.js:147
GetText.add('Connection Limit', '${_("Connection Limit").replace("'", "\'")}');

// Deluge.Toolbar.js:99, Deluge.ConnectionManager.js:50
GetText.add('Connection Manager', '${_("Connection Manager").replace("'", "\'")}');

// Deluge.Preferences.Daemon.js:19
GetText.add('Connections', '${_("Connections").replace("'", "\'")}');

// Deluge.Preferences.Downloads.js:23
GetText.add('Copy of .torrent files to', '${_("Copy of .torrent files to").replace("'", "\'")}');

// Deluge.Toolbar.js:44
GetText.add('Create', '${_("Create").replace("'", "\'")}');

// Deluge.Menus.js:111
GetText.add('D/L Speed Limit', '${_("D/L Speed Limit").replace("'", "\'")}');

// Deluge.Preferences.Daemon.js:3
GetText.add('Daemon', '${_("Daemon").replace("'", "\'")}');

// Deluge.Preferences.Daemon.js:13
GetText.add('Daemon port', '${_("Daemon port").replace("'", "\'")}');

// Deluge.Details.Details.js:36
GetText.add('Details', '${_("Details").replace("'", "\'")}');

// Deluge.ConnectionManager.js:270
GetText.add('Disconnect', '${_("Disconnect").replace("'", "\'")}');

// Deluge.js:89, Deluge.Menus.js:400
GetText.add('Do Not Download', '${_("Do Not Download").replace("'", "\'")}');

// Deluge.Toolbar.js:86, Deluge.Menus.js:206, Deluge.EditTrackers.js:231
GetText.add('Down', '${_("Down").replace("'", "\'")}');

// Deluge.Torrents.js:150
GetText.add('Down Speed', '${_("Down Speed").replace("'", "\'")}');

// Deluge.Add.js:88
GetText.add('Download Location', '${_("Download Location").replace("'", "\'")}');

// Deluge.Preferences.Downloads.js:15
GetText.add('Download to', '${_("Download to").replace("'", "\'")}');

// Deluge.Preferences.Downloads.js:3
GetText.add('Downloads', '${_("Downloads").replace("'", "\'")}');

// Deluge.Torrents.js:162
GetText.add('ETA', '${_("ETA").replace("'", "\'")}');

// Deluge.EditTrackers.js:243
GetText.add('Edit', '${_("Edit").replace("'", "\'")}');

// Deluge.EditTrackers.js:98
GetText.add('Edit Tracker', '${_("Edit Tracker").replace("'", "\'")}');

// Deluge.Details.Options.js:325, Deluge.Menus.js:226, Deluge.EditTrackers.js:160
GetText.add('Edit Trackers', '${_("Edit Trackers").replace("'", "\'")}');

// Deluge.Add.js:361, Deluge.ConnectionManager.js:164, Deluge.ConnectionManager.js:252, Deluge.ConnectionManager.js:287
GetText.add('Error', '${_("Error").replace("'", "\'")}');

// Deluge.Menus.js:396
GetText.add('Expand All', '${_("Expand All").replace("'", "\'")}');

// Deluge.Add.js:233, Deluge.Add.File.js:68
GetText.add('File', '${_("File").replace("'", "\'")}');

// Deluge.Details.Files.js:53, Deluge.Add.js:60
GetText.add('Filename', '${_("Filename").replace("'", "\'")}');

// Deluge.Details.Files.js:47, Deluge.Add.js:52
GetText.add('Files', '${_("Files").replace("'", "\'")}');

// Deluge.Sidebar.js:75
GetText.add('Filters', '${_("Filters").replace("'", "\'")}');

// Deluge.Preferences.Downloads.js:9
GetText.add('Folders', '${_("Folders").replace("'", "\'")}');

// Deluge.Menus.js:238
GetText.add('Force Recheck', '${_("Force Recheck").replace("'", "\'")}');

// Deluge.Preferences.Downloads.js:40
GetText.add('Full', '${_("Full").replace("'", "\'")}');

// Deluge.Details.Options.js:278
GetText.add('General', '${_("General").replace("'", "\'")}');

// Deluge.Preferences.Bandwidth.js:10
GetText.add('Global Bandwidth Usage', '${_("Global Bandwidth Usage").replace("'", "\'")}');

// Deluge.Toolbar.js:108
GetText.add('Help', '${_("Help").replace("'", "\'")}');

// Deluge.Preferences.Interface.js:29
GetText.add('Hide filters with zero torrents', '${_("Hide filters with zero torrents").replace("'", "\'")}');

// Deluge.js:91, Deluge.Menus.js:410
GetText.add('High Priority', '${_("High Priority").replace("'", "\'")}');

// Deluge.js:92, Deluge.Menus.js:415
GetText.add('Highest Priority', '${_("Highest Priority").replace("'", "\'")}');

// Deluge.ConnectionManager.js:84, Deluge.ConnectionManager.js:335
GetText.add('Host', '${_("Host").replace("'", "\'")}');

// Deluge.Preferences.Bandwidth.js:57
GetText.add('Ignore limits on local network', '${_("Ignore limits on local network").replace("'", "\'")}');

// Deluge.Add.js:246
GetText.add('Infohash', '${_("Infohash").replace("'", "\'")}');

// Deluge.Preferences.Interface.js:3
GetText.add('Interface', '${_("Interface").replace("'", "\'")}');

// Deluge.Details.Options.js:115, Deluge.Details.Options.js:142
GetText.add('KiB/s', '${_("KiB/s").replace("'", "\'")}');

// Deluge.Details.Status.js:57, Deluge.Details.Details.js:43
GetText.add('Loading', '${_("Loading").replace("'", "\'")}');

// Deluge.Login.js:52, Deluge.Login.js:65
GetText.add('Login', '${_("Login").replace("'", "\'")}');

// Deluge.Login.js:107
GetText.add('Login Failed', '${_("Login Failed").replace("'", "\'")}');

// Deluge.Toolbar.js:116
GetText.add('Logout', '${_("Logout").replace("'", "\'")}');

// Deluge.Details.Options.js:151
GetText.add('Max Connections', '${_("Max Connections").replace("'", "\'")}');

// Deluge.Details.Options.js:98
GetText.add('Max Download Speed', '${_("Max Download Speed").replace("'", "\'")}');

// Deluge.Details.Options.js:174
GetText.add('Max Upload Slots', '${_("Max Upload Slots").replace("'", "\'")}');

// Deluge.Details.Options.js:124
GetText.add('Max Upload Speed', '${_("Max Upload Speed").replace("'", "\'")}');

// Deluge.Preferences.Bandwidth.js:42
GetText.add('Maximum Connection Attempts per Second', '${_("Maximum Connection Attempts per Second").replace("'", "\'")}');

// Deluge.Preferences.Bandwidth.js:17, Deluge.Preferences.Bandwidth.js:76
GetText.add('Maximum Connections', '${_("Maximum Connections").replace("'", "\'")}');

// Deluge.Preferences.Bandwidth.js:27, Deluge.Preferences.Bandwidth.js:86
GetText.add('Maximum Download Speed (KiB/s)', '${_("Maximum Download Speed (KiB/s)").replace("'", "\'")}');

// Deluge.Preferences.Bandwidth.js:37
GetText.add('Maximum Half-Open Connections', '${_("Maximum Half-Open Connections").replace("'", "\'")}');

// Deluge.Preferences.Bandwidth.js:22, Deluge.Preferences.Bandwidth.js:81
GetText.add('Maximum Upload Slots', '${_("Maximum Upload Slots").replace("'", "\'")}');

// Deluge.Preferences.Bandwidth.js:32, Deluge.Preferences.Bandwidth.js:91
GetText.add('Maximum Upload Speed (KiB/s)', '${_("Maximum Upload Speed (KiB/s)").replace("'", "\'")}');

// Deluge.Details.Options.js:259
GetText.add('Move Completed', '${_("Move Completed").replace("'", "\'")}');

// Deluge.Menus.js:244
GetText.add('Move Storage', '${_("Move Storage").replace("'", "\'")}');

// Deluge.Preferences.Downloads.js:19
GetText.add('Move completed to', '${_("Move completed to").replace("'", "\'")}');

// Deluge.Torrents.js:120
GetText.add('Name', '${_("Name").replace("'", "\'")}');

// Deluge.Preferences.Network.js:1
GetText.add('Network', '${_("Network").replace("'", "\'")}');

// Deluge.js:90, Deluge.Menus.js:405
GetText.add('Normal Priority', '${_("Normal Priority").replace("'", "\'")}');

// Deluge.Statusbar.js:7
GetText.add('Not Connected', '${_("Not Connected").replace("'", "\'")}');

// Deluge.Add.js:362
GetText.add('Not a valid torrent', '${_("Not a valid torrent").replace("'", "\'")}');

// Deluge.Preferences.Notification.js:1
GetText.add('Notification', '${_("Notification").replace("'", "\'")}');

// Deluge.Preferences.js:57, Deluge.EditTrackers.js:179
GetText.add('Ok', '${_("Ok").replace("'", "\'")}');

// Deluge.Details.Options.js:50, Deluge.Add.js:81, Deluge.Menus.js:107, Deluge.Preferences.Downloads.js:45
GetText.add('Options', '${_("Options").replace("'", "\'")}');

// Deluge.Menus.js:291, Deluge.Menus.js:338, Deluge.Menus.js:385, Deluge.Preferences.Other.js:1, Deluge.Preferences.Daemon.js:32
GetText.add('Other', '${_("Other").replace("'", "\'")}');

// Deluge.Preferences.Interface.js:35, Deluge.Login.js:77, Deluge.ConnectionManager.js:357
GetText.add('Password', '${_("Password").replace("'", "\'")}');

// Deluge.Toolbar.js:65, Deluge.Menus.js:95
GetText.add('Pause', '${_("Pause").replace("'", "\'")}');

// Deluge.Torrents.js:144, Deluge.Details.Peers.js:64
GetText.add('Peers', '${_("Peers").replace("'", "\'")}');

// Deluge.Preferences.Bandwidth.js:70
GetText.add('Per Torrent Bandwidth Usage', '${_("Per Torrent Bandwidth Usage").replace("'", "\'")}');

// Deluge.Preferences.Daemon.js:40
GetText.add('Periodically check the website for new releases', '${_("Periodically check the website for new releases").replace("'", "\'")}');

// Deluge.Preferences.Plugins.js:1
GetText.add('Plugins', '${_("Plugins").replace("'", "\'")}');

// Deluge.Preferences.Daemon.js:9, Deluge.ConnectionManager.js:341
GetText.add('Port', '${_("Port").replace("'", "\'")}');

// Deluge.Toolbar.js:92, Deluge.Preferences.js:48
GetText.add('Preferences', '${_("Preferences").replace("'", "\'")}');

// Deluge.Details.Options.js:292
GetText.add('Prioritize First/Last', '${_("Prioritize First/Last").replace("'", "\'")}');

// Deluge.Preferences.Downloads.js:52
GetText.add('Prioritize first and last pieces of torrent', '${_("Prioritize first and last pieces of torrent").replace("'", "\'")}');

// Deluge.Details.Files.js:67
GetText.add('Priority', '${_("Priority").replace("'", "\'")}');

// Deluge.Details.Options.js:285
GetText.add('Private', '${_("Private").replace("'", "\'")}');

// Deluge.Details.Files.js:62, Deluge.Torrents.js:132
GetText.add('Progress', '${_("Progress").replace("'", "\'")}');

// Deluge.Preferences.Proxy.js:2
GetText.add('Proxy', '${_("Proxy").replace("'", "\'")}');

// Deluge.Details.Options.js:197, Deluge.Menus.js:189, Deluge.Preferences.Queue.js:2
GetText.add('Queue', '${_("Queue").replace("'", "\'")}');

// Deluge.Preferences.Bandwidth.js:64
GetText.add('Rate limit IP overhead', '${_("Rate limit IP overhead").replace("'", "\'")}');

// Deluge.Torrents.js:168
GetText.add('Ratio', '${_("Ratio").replace("'", "\'")}');

// Deluge.Toolbar.js:58, Deluge.Add.js:252, Deluge.ConnectionManager.js:119, Deluge.EditTrackers.js:249
GetText.add('Remove', '${_("Remove").replace("'", "\'")}');

// Deluge.Menus.js:232
GetText.add('Remove Torrent', '${_("Remove Torrent").replace("'", "\'")}');

// Deluge.Details.Options.js:250
GetText.add('Remove at ratio', '${_("Remove at ratio").replace("'", "\'")}');

// Deluge.Toolbar.js:72, Deluge.Menus.js:101
GetText.add('Resume', '${_("Resume").replace("'", "\'")}');

// Deluge.EditTrackers.js:117
GetText.add('Save', '${_("Save").replace("'", "\'")}');

// Deluge.Torrents.js:138
GetText.add('Seeders', '${_("Seeders").replace("'", "\'")}');

// Deluge.Add.File.js:67
GetText.add('Select a torrent', '${_("Select a torrent").replace("'", "\'")}');

// Deluge.Preferences.Interface.js:16
GetText.add('Show session speed in titlebar', '${_("Show session speed in titlebar").replace("'", "\'")}');

// Deluge.Preferences.Interface.js:22
GetText.add('Sidebar', '${_("Sidebar").replace("'", "\'")}');

// Deluge.Details.Files.js:57, Deluge.Torrents.js:126, Deluge.Add.js:64
GetText.add('Size', '${_("Size").replace("'", "\'")}');

// Deluge.Sidebar.js:37
GetText.add('State', '${_("State").replace("'", "\'")}');

// Deluge.Details.Status.js:35, Deluge.ConnectionManager.js:77
GetText.add('Status', '${_("Status").replace("'", "\'")}');

// Deluge.ConnectionManager.js:126
GetText.add('Stop Daemon', '${_("Stop Daemon").replace("'", "\'")}');

// Deluge.Details.Options.js:225
GetText.add('Stop seed at ratio', '${_("Stop seed at ratio").replace("'", "\'")}');

// Deluge.EditTrackers.js:198
GetText.add('Tier', '${_("Tier").replace("'", "\'")}');

// Deluge.Menus.js:194
GetText.add('Top', '${_("Top").replace("'", "\'")}');

// Deluge.Torrents.js:186, Deluge.EditTrackers.js:126, Deluge.EditTrackers.js:205
GetText.add('Tracker', '${_("Tracker").replace("'", "\'")}');

// Deluge.Sidebar.js:38
GetText.add('Tracker Host', '${_("Tracker Host").replace("'", "\'")}');

// Deluge.EditTrackers.js:67
GetText.add('Trackers', '${_("Trackers").replace("'", "\'")}');

// Deluge.Menus.js:129
GetText.add('U/L Speed Limit', '${_("U/L Speed Limit").replace("'", "\'")}');

// Deluge.Menus.js:125, Deluge.Menus.js:143, Deluge.Menus.js:161, Deluge.Menus.js:179, Deluge.Menus.js:285, Deluge.Menus.js:332, Deluge.Menus.js:379
GetText.add('Unlimited', '${_("Unlimited").replace("'", "\'")}');

// Deluge.Toolbar.js:79, Deluge.Menus.js:200, Deluge.EditTrackers.js:225
GetText.add('Up', '${_("Up").replace("'", "\'")}');

// Deluge.Torrents.js:156
GetText.add('Up Speed', '${_("Up Speed").replace("'", "\'")}');

// Deluge.Menus.js:220
GetText.add('Update Tracker', '${_("Update Tracker").replace("'", "\'")}');

// Deluge.Menus.js:165
GetText.add('Upload Slot Limit', '${_("Upload Slot Limit").replace("'", "\'")}');

// Deluge.Add.File.js:82
GetText.add('Uploading your torrent...', '${_("Uploading your torrent...").replace("'", "\'")}');

// Deluge.Add.js:239, Deluge.Add.Url.js:64
GetText.add('Url', '${_("Url").replace("'", "\'")}');

// Deluge.ConnectionManager.js:351
GetText.add('Username', '${_("Username").replace("'", "\'")}');

// Deluge.ConnectionManager.js:90
GetText.add('Version', '${_("Version").replace("'", "\'")}');

// Deluge.Preferences.Interface.js:9
GetText.add('Window', '${_("Window").replace("'", "\'")}');

// Deluge.Login.js:108
GetText.add('You entered an incorrect password', '${_("You entered an incorrect password").replace("'", "\'")}');


