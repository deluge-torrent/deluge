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

// Deluge.Torrents.js:117
GetText.add('#', '${_("#").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:164
GetText.add('0', '${_("0").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:166
GetText.add('1', '${_("1").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:112, Deluge.Menus.js:130
GetText.add('10 KiB/s', '${_("10 KiB/s").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:148
GetText.add('100', '${_("100").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:168
GetText.add('2', '${_("2").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:150
GetText.add('200', '${_("200").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:170
GetText.add('3', '${_("3").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:114, Deluge.Menus.js:132
GetText.add('30 KiB/s', '${_("30 KiB/s").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:152
GetText.add('300', '${_("300").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:118, Deluge.Menus.js:136
GetText.add('300 KiB/s', '${_("300 KiB/s").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:172
GetText.add('5', '${_("5").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:110, Deluge.Menus.js:128
GetText.add('5 KiB/s', '${_("5 KiB/s").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:146
GetText.add('50', '${_("50").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:154
GetText.add('500', '${_("500").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:116, Deluge.Menus.js:134
GetText.add('80 KiB/s', '${_("80 KiB/s").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Queue.js:69
GetText.add('Active Torrents', '${_("Active Torrents").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.ConnectionManager.js:64, Deluge.ConnectionManager.js:222, Deluge.Add.Url.js:54, Deluge.Toolbar.js:51, Deluge.Add.js:381, Deluge.EditTrackers.js:58, Deluge.EditTrackers.js:237, Deluge.Add.File.js:54
GetText.add('Add', '${_("Add").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.ConnectionManager.js:52
GetText.add('Add Connection', '${_("Add Connection").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Add.js:183
GetText.add('Add In Paused State', '${_("Add In Paused State").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Add.js:363
GetText.add('Add Torrents', '${_("Add Torrents").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.EditTrackers.js:39
GetText.add('Add Tracker', '${_("Add Tracker").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Add.File.js:46
GetText.add('Add from File', '${_("Add from File").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Add.Url.js:46
GetText.add('Add from Url', '${_("Add from Url").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Downloads.js:121
GetText.add('Add torrents in Paused state', '${_("Add torrents in Paused state").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Torrents.js:184
GetText.add('Added', '${_("Added").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Sidebar.js:198
GetText.add('All', '${_("All").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Add.js:113, Deluge.Preferences.Downloads.js:88
GetText.add('Allocation', '${_("Allocation").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Daemon.js:80
GetText.add('Allow Remote Connections', '${_("Allow Remote Connections").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Details.Options.js:347, Deluge.Preferences.js:91
GetText.add('Apply', '${_("Apply").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:179, Deluge.Details.Options.js:215
GetText.add('Auto Managed', '${_("Auto Managed").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Downloads.js:80
GetText.add('Autoadd .torrent files from', '${_("Autoadd .torrent files from").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Torrents.js:178
GetText.add('Avail', '${_("Avail").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Add.js:143, Deluge.Details.Options.js:88, Deluge.Preferences.Bandwidth.js:39
GetText.add('Bandwidth', '${_("Bandwidth").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Other.js:62
GetText.add('Be alerted about new releases', '${_("Be alerted about new releases").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:207
GetText.add('Bottom', '${_("Bottom").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Add.File.js:69
GetText.add('Browse', '${_("Browse").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Cache.js:39
GetText.add('Cache', '${_("Cache").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Cache.js:71
GetText.add('Cache Expiry (seconds)', '${_("Cache Expiry (seconds)").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Cache.js:59
GetText.add('Cache Size (16 KiB Blocks)', '${_("Cache Size (16 KiB Blocks)").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Add.js:380, Deluge.EditTrackers.js:57, Deluge.EditTrackers.js:116, Deluge.EditTrackers.js:178, Deluge.Remove.js:53
GetText.add('Cancel', '${_("Cancel").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.js:55
GetText.add('Categories', '${_("Categories").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Interface.js:176
GetText.add('Certificate', '${_("Certificate").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Interface.js:115
GetText.add('Change', '${_("Change").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Interface.js:223
GetText.add('Change Successful', '${_("Change Successful").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.ConnectionManager.js:63, Deluge.ConnectionManager.js:171, Deluge.Preferences.js:90
GetText.add('Close', '${_("Close").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Add.js:136, Deluge.Preferences.Downloads.js:99
GetText.add('Compact', '${_("Compact").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Interface.js:103
GetText.add('Confirm Password', '${_("Confirm Password").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.ConnectionManager.js:172, Deluge.ConnectionManager.js:284
GetText.add('Connect', '${_("Connect").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.ConnectionManager.js:277, Deluge.ConnectionManager.js:322
GetText.add('Connected', '${_("Connected").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:142
GetText.add('Connection Limit', '${_("Connection Limit").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.ConnectionManager.js:159, Deluge.Toolbar.js:99
GetText.add('Connection Manager', '${_("Connection Manager").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Daemon.js:72
GetText.add('Connections', '${_("Connections").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Add.Url.js:72
GetText.add('Cookies', '${_("Cookies").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Downloads.js:74
GetText.add('Copy of .torrent files to', '${_("Copy of .torrent files to").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Toolbar.js:44
GetText.add('Create', '${_("Create").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:106
GetText.add('D/L Speed Limit', '${_("D/L Speed Limit").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Network.js:227, Deluge.Preferences.Proxy.js:202
GetText.add('DHT', '${_("DHT").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Daemon.js:39
GetText.add('Daemon', '${_("Daemon").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Daemon.js:58
GetText.add('Daemon port', '${_("Daemon port").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Details.Details.js:36
GetText.add('Details', '${_("Details").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Encryption.js:66, Deluge.Preferences.Encryption.js:82
GetText.add('Disabled', '${_("Disabled").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.ConnectionManager.js:279
GetText.add('Disconnect', '${_("Disconnect").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:406, Deluge.js:107
GetText.add('Do Not Download', '${_("Do Not Download").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Queue.js:116
GetText.add('Do not count slow torrents', '${_("Do not count slow torrents").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Toolbar.js:86, Deluge.Menus.js:201, Deluge.EditTrackers.js:231
GetText.add('Down', '${_("Down").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Torrents.js:154
GetText.add('Down Speed', '${_("Down Speed").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Add.js:93
GetText.add('Download Location', '${_("Download Location").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Downloads.js:63
GetText.add('Download to', '${_("Download to").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Downloads.js:39
GetText.add('Downloads', '${_("Downloads").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Torrents.js:166
GetText.add('ETA', '${_("ETA").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.EditTrackers.js:243
GetText.add('Edit', '${_("Edit").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.EditTrackers.js:98
GetText.add('Edit Tracker', '${_("Edit Tracker").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:221, Deluge.Details.Options.js:329, Deluge.EditTrackers.js:160
GetText.add('Edit Trackers', '${_("Edit Trackers").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Encryption.js:98
GetText.add('Either', '${_("Either").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Plugins.js:83, Deluge.Preferences.Encryption.js:65, Deluge.Preferences.Encryption.js:81
GetText.add('Enabled', '${_("Enabled").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Encryption.js:110
GetText.add('Encrypt entire stream', '${_("Encrypt entire stream").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Encryption.js:39
GetText.add('Encryption', '${_("Encryption").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.ConnectionManager.js:128, Deluge.ConnectionManager.js:391, Deluge.ConnectionManager.js:447, Deluge.Add.js:529
GetText.add('Error', '${_("Error").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:402
GetText.add('Expand All', '${_("Expand All").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Add.js:428, Deluge.Add.File.js:66
GetText.add('File', '${_("File").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Add.js:62, Deluge.Details.Files.js:53
GetText.add('Filename', '${_("Filename").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Add.js:54, Deluge.Details.Files.js:47
GetText.add('Files', '${_("Files").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Sidebar.js:75
GetText.add('Filters', '${_("Filters").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Plugins.js:117
GetText.add('Find More', '${_("Find More").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Downloads.js:53
GetText.add('Folders', '${_("Folders").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:233
GetText.add('Force Recheck', '${_("Force Recheck").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Encryption.js:64, Deluge.Preferences.Encryption.js:80
GetText.add('Forced', '${_("Forced").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Add.js:129, Deluge.Preferences.Downloads.js:100
GetText.add('Full', '${_("Full").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Encryption.js:97
GetText.add('Full Stream', '${_("Full Stream").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Queue.js:53, Deluge.Add.js:176, Deluge.Details.Options.js:281
GetText.add('General', '${_("General").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Other.js:92
GetText.add('GeoIP Database', '${_("GeoIP Database").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Bandwidth.js:53
GetText.add('Global Bandwidth Usage', '${_("Global Bandwidth Usage").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Proxy.js:61
GetText.add('HTTP', '${_("HTTP").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Proxy.js:62
GetText.add('HTTP with Auth', '${_("HTTP with Auth").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Encryption.js:96
GetText.add('Handshake', '${_("Handshake").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Toolbar.js:107
GetText.add('Help', '${_("Help").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:416, Deluge.js:109
GetText.add('High Priority', '${_("High Priority").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:421, Deluge.js:110
GetText.add('Highest Priority', '${_("Highest Priority").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.ConnectionManager.js:77, Deluge.ConnectionManager.js:193, Deluge.Preferences.Proxy.js:73
GetText.add('Host', '${_("Host").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Bandwidth.js:144
GetText.add('Ignore limits on local network', '${_("Ignore limits on local network").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Encryption.js:58
GetText.add('Inbound', '${_("Inbound").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Network.js:53
GetText.add('Incoming Ports', '${_("Incoming Ports").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Plugins.js:128
GetText.add('Info', '${_("Info").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Add.js:441
GetText.add('Infohash', '${_("Infohash").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Plugins.js:112
GetText.add('Install', '${_("Install").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Interface.js:39, Deluge.Preferences.Interface.js:54
GetText.add('Interface', '${_("Interface").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Interface.js:198
GetText.add('Invalid Password', '${_("Invalid Password").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Details.Options.js:114, Deluge.Details.Options.js:141
GetText.add('KiB/s', '${_("KiB/s").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Network.js:221
GetText.add('LSD', '${_("LSD").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Encryption.js:90
GetText.add('Level', '${_("Level").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Details.Status.js:57, Deluge.Details.Details.js:43
GetText.add('Loading', '${_("Loading").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Other.js:99
GetText.add('Location', '${_("Location").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Login.js:52, Deluge.Login.js:63
GetText.add('Login', '${_("Login").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Login.js:139
GetText.add('Login Failed', '${_("Login Failed").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Toolbar.js:115
GetText.add('Logout', '${_("Logout").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Add.js:163, Deluge.Details.Options.js:150
GetText.add('Max Connections', '${_("Max Connections").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Add.js:151
GetText.add('Max Down Speed', '${_("Max Down Speed").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Details.Options.js:97
GetText.add('Max Download Speed', '${_("Max Download Speed").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Add.js:157
GetText.add('Max Up Speed', '${_("Max Up Speed").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Add.js:169, Deluge.Details.Options.js:173
GetText.add('Max Upload Slots', '${_("Max Upload Slots").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Details.Options.js:123
GetText.add('Max Upload Speed', '${_("Max Upload Speed").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Bandwidth.js:121
GetText.add('Maximum Connection Attempts per Second', '${_("Maximum Connection Attempts per Second").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Bandwidth.js:61, Deluge.Preferences.Bandwidth.js:164
GetText.add('Maximum Connections', '${_("Maximum Connections").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Bandwidth.js:85, Deluge.Preferences.Bandwidth.js:188
GetText.add('Maximum Download Speed (KiB/s)', '${_("Maximum Download Speed (KiB/s)").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Bandwidth.js:109
GetText.add('Maximum Half-Open Connections', '${_("Maximum Half-Open Connections").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Bandwidth.js:73, Deluge.Preferences.Bandwidth.js:176
GetText.add('Maximum Upload Slots', '${_("Maximum Upload Slots").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Bandwidth.js:97, Deluge.Preferences.Bandwidth.js:200
GetText.add('Maximum Upload Speed (KiB/s)', '${_("Maximum Upload Speed (KiB/s)").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Details.Options.js:262
GetText.add('Move Completed', '${_("Move Completed").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:239
GetText.add('Move Storage', '${_("Move Storage").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Downloads.js:68
GetText.add('Move completed to', '${_("Move completed to").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Network.js:207
GetText.add('NAT-PMP', '${_("NAT-PMP").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Torrents.js:124
GetText.add('Name', '${_("Name").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Network.js:40
GetText.add('Network', '${_("Network").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Network.js:190
GetText.add('Network Extras', '${_("Network Extras").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Network.js:159
GetText.add('Network Interface', '${_("Network Interface").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Interface.js:99
GetText.add('New Password', '${_("New Password").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Proxy.js:57
GetText.add('None', '${_("None").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:411, Deluge.js:108
GetText.add('Normal Priority', '${_("Normal Priority").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Statusbar.js:7
GetText.add('Not Connected', '${_("Not Connected").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Add.js:530
GetText.add('Not a valid torrent', '${_("Not a valid torrent").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Notification.js:1
GetText.add('Notification', '${_("Notification").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.ConnectionManager.js:280, Deluge.ConnectionManager.js:288
GetText.add('Offline', '${_("Offline").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.EditTrackers.js:179, Deluge.Preferences.js:92
GetText.add('Ok', '${_("Ok").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Interface.js:95
GetText.add('Old Password', '${_("Old Password").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Add.js:84, Deluge.Menus.js:102, Deluge.Details.Options.js:50, Deluge.Preferences.Downloads.js:107
GetText.add('Options', '${_("Options").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:297, Deluge.Menus.js:344, Deluge.Menus.js:391, Deluge.Preferences.Daemon.js:87, Deluge.Preferences.Other.js:39
GetText.add('Other', '${_("Other").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Encryption.js:74
GetText.add('Outbound', '${_("Outbound").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Network.js:107
GetText.add('Outgoing Ports', '${_("Outgoing Ports").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.ConnectionManager.js:109, Deluge.Preferences.Interface.js:82, Deluge.Preferences.Interface.js:213, Deluge.Preferences.Proxy.js:100, Deluge.Login.js:75
GetText.add('Password', '${_("Password").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Toolbar.js:65, Deluge.Menus.js:90
GetText.add('Pause', '${_("Pause").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Proxy.js:184
GetText.add('Peer', '${_("Peer").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Network.js:214
GetText.add('Peer Exchange', '${_("Peer Exchange").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Network.js:183
GetText.add('Peer TOS Byte', '${_("Peer TOS Byte").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Details.Peers.js:64, Deluge.Torrents.js:148
GetText.add('Peers', '${_("Peers").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Bandwidth.js:156
GetText.add('Per Torrent Bandwidth Usage', '${_("Per Torrent Bandwidth Usage").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Daemon.js:96
GetText.add('Periodically check the website for new releases', '${_("Periodically check the website for new releases").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Plugins.js:90
GetText.add('Plugin', '${_("Plugin").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Plugins.js:39
GetText.add('Plugins', '${_("Plugins").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.ConnectionManager.js:85, Deluge.Preferences.Interface.js:148, Deluge.Preferences.Proxy.js:80, Deluge.Preferences.Daemon.js:53
GetText.add('Port', '${_("Port").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Toolbar.js:92, Deluge.Preferences.js:50
GetText.add('Preferences', '${_("Preferences").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Details.Options.js:296
GetText.add('Prioritize First/Last', '${_("Prioritize First/Last").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Add.js:189
GetText.add('Prioritize First/Last Pieces', '${_("Prioritize First/Last Pieces").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Downloads.js:116
GetText.add('Prioritize first and last pieces of torrent', '${_("Prioritize first and last pieces of torrent").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Details.Files.js:67
GetText.add('Priority', '${_("Priority").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Details.Options.js:288
GetText.add('Private', '${_("Private").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Interface.js:169
GetText.add('Private Key', '${_("Private Key").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Details.Files.js:62, Deluge.Torrents.js:136
GetText.add('Progress', '${_("Progress").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Proxy.js:175
GetText.add('Proxy', '${_("Proxy").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Queue.js:39, Deluge.Menus.js:184, Deluge.Details.Options.js:196
GetText.add('Queue', '${_("Queue").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Queue.js:62
GetText.add('Queue new torrents to top', '${_("Queue new torrents to top").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Bandwidth.js:150
GetText.add('Rate limit IP overhead', '${_("Rate limit IP overhead").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Torrents.js:172
GetText.add('Ratio', '${_("Ratio").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.ConnectionManager.js:229, Deluge.Toolbar.js:58, Deluge.Add.js:447, Deluge.EditTrackers.js:249, Deluge.Remove.js:54
GetText.add('Remove', '${_("Remove").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:227, Deluge.Remove.js:38
GetText.add('Remove Torrent', '${_("Remove Torrent").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Details.Options.js:253
GetText.add('Remove at ratio', '${_("Remove at ratio").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Queue.js:208
GetText.add('Remove torrent when share ratio is reached', '${_("Remove torrent when share ratio is reached").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Remove.js:55
GetText.add('Remove with data', '${_("Remove with data").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Toolbar.js:72, Deluge.Menus.js:96
GetText.add('Resume', '${_("Resume").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.EditTrackers.js:117
GetText.add('Save', '${_("Save").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Queue.js:153
GetText.add('Seed Time (m)', '${_("Seed Time (m)").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Torrents.js:142
GetText.add('Seeders', '${_("Seeders").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Queue.js:122
GetText.add('Seeding', '${_("Seeding").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Add.File.js:65
GetText.add('Select a torrent', '${_("Select a torrent").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Interface.js:127
GetText.add('Server', '${_("Server").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Interface.js:138
GetText.add('Session Timeout', '${_("Session Timeout").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Cache.js:53, Deluge.Preferences.Encryption.js:53
GetText.add('Settings', '${_("Settings").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Queue.js:129
GetText.add('Share Ratio Limit', '${_("Share Ratio Limit").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Queue.js:141
GetText.add('Share Time Ratio', '${_("Share Time Ratio").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Interface.js:70
GetText.add('Show filters with zero torrents', '${_("Show filters with zero torrents").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Interface.js:64
GetText.add('Show session speed in titlebar', '${_("Show session speed in titlebar").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Interface.js:76
GetText.add('Show trackers with zero torrents', '${_("Show trackers with zero torrents").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Add.js:66, Deluge.Details.Files.js:57, Deluge.Torrents.js:130
GetText.add('Size', '${_("Size").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Proxy.js:58
GetText.add('Socksv4', '${_("Socksv4").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Proxy.js:59
GetText.add('Socksv5', '${_("Socksv5").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Proxy.js:60
GetText.add('Socksv5 with Auth', '${_("Socksv5 with Auth").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.ConnectionManager.js:291
GetText.add('Start Daemon', '${_("Start Daemon").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Sidebar.js:37
GetText.add('State', '${_("State").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.ConnectionManager.js:186, Deluge.Details.Status.js:35
GetText.add('Status', '${_("Status").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.ConnectionManager.js:237, Deluge.ConnectionManager.js:297, Deluge.ConnectionManager.js:415
GetText.add('Stop Daemon', '${_("Stop Daemon").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Details.Options.js:225
GetText.add('Stop seed at ratio', '${_("Stop seed at ratio").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Queue.js:182
GetText.add('Stop seeding when share ratio reaches:', '${_("Stop seeding when share ratio reaches:").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Other.js:68
GetText.add('System Information', '${_("System Information").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Network.js:175
GetText.add('TOS', '${_("TOS").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.EditTrackers.js:198
GetText.add('Tier', '${_("Tier").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:189
GetText.add('Top', '${_("Top").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Queue.js:76
GetText.add('Total Active', '${_("Total Active").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Queue.js:88
GetText.add('Total Active Downloading', '${_("Total Active Downloading").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Queue.js:100
GetText.add('Total Active Seeding', '${_("Total Active Seeding").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Proxy.js:196, Deluge.Torrents.js:190, Deluge.EditTrackers.js:126, Deluge.EditTrackers.js:205
GetText.add('Tracker', '${_("Tracker").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Sidebar.js:38
GetText.add('Tracker Host', '${_("Tracker Host").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.EditTrackers.js:67
GetText.add('Trackers', '${_("Trackers").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Proxy.js:50
GetText.add('Type', '${_("Type").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:124
GetText.add('U/L Speed Limit', '${_("U/L Speed Limit").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Network.js:201
GetText.add('UPnP', '${_("UPnP").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:120, Deluge.Menus.js:138, Deluge.Menus.js:156, Deluge.Menus.js:174, Deluge.Menus.js:291, Deluge.Menus.js:338, Deluge.Menus.js:385
GetText.add('Unlimited', '${_("Unlimited").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Toolbar.js:79, Deluge.Menus.js:195, Deluge.EditTrackers.js:225
GetText.add('Up', '${_("Up").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Torrents.js:160
GetText.add('Up Speed', '${_("Up Speed").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:215
GetText.add('Update Tracker', '${_("Update Tracker").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Other.js:53
GetText.add('Updates', '${_("Updates").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Menus.js:160
GetText.add('Upload Slot Limit', '${_("Upload Slot Limit").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Add.File.js:80
GetText.add('Uploading your torrent...', '${_("Uploading your torrent...").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Add.Url.js:64, Deluge.Add.js:434
GetText.add('Url', '${_("Url").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Network.js:62, Deluge.Preferences.Network.js:116
GetText.add('Use Random Ports', '${_("Use Random Ports").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Interface.js:161
GetText.add('Use SSL (paths relative to the Deluge config folder)', '${_("Use SSL (paths relative to the Deluge config folder)").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.ConnectionManager.js:101, Deluge.Preferences.Proxy.js:93
GetText.add('Username', '${_("Username").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.ConnectionManager.js:199
GetText.add('Version', '${_("Version").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Proxy.js:190
GetText.add('Web Seed', '${_("Web Seed").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Other.js:85
GetText.add('Yes, please send anonymous statistics', '${_("Yes, please send anonymous statistics").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Login.js:140
GetText.add('You entered an incorrect password', '${_("You entered an incorrect password").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Interface.js:214
GetText.add('Your old password was incorrect!', '${_("Your old password was incorrect!").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Interface.js:224
GetText.add('Your password was successfully changed!', '${_("Your password was successfully changed!").replace("'", "\\'").replace("\n", "\\n")}');

// Deluge.Preferences.Interface.js:199
GetText.add('Your passwords don\'t match!', '${_("Your passwords don\'t match!").replace("'", "\\'").replace("\n", "\\n")}');


