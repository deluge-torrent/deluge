## -*- coding: utf-8 -*-
/*
 * Script: gettext.js
 *  A script file that is run through the template renderer in order for
 *  translated strings to be used.
 *
 * Copyright:
 *  (c) 2009 Damien Churchill <damoxc@gmail.com>
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
GetText.add('#', '${escape(_("#"))}')

// Deluge.Menus.js:167
GetText.add('0', '${escape(_("0"))}')

// Deluge.Menus.js:169
GetText.add('1', '${escape(_("1"))}')

// Deluge.Menus.js:115, Deluge.Menus.js:133
GetText.add('10 KiB/s', '${escape(_("10 KiB/s"))}')

// Deluge.Menus.js:151
GetText.add('100', '${escape(_("100"))}')

// Deluge.Menus.js:171
GetText.add('2', '${escape(_("2"))}')

// Deluge.Menus.js:153
GetText.add('200', '${escape(_("200"))}')

// Deluge.Menus.js:173
GetText.add('3', '${escape(_("3"))}')

// Deluge.Menus.js:117, Deluge.Menus.js:135
GetText.add('30 KiB/s', '${escape(_("30 KiB/s"))}')

// Deluge.Menus.js:155
GetText.add('300', '${escape(_("300"))}')

// Deluge.Menus.js:121, Deluge.Menus.js:139
GetText.add('300 KiB/s', '${escape(_("300 KiB/s"))}')

// Deluge.Menus.js:175
GetText.add('5', '${escape(_("5"))}')

// Deluge.Menus.js:113, Deluge.Menus.js:131
GetText.add('5 KiB/s', '${escape(_("5 KiB/s"))}')

// Deluge.Menus.js:149
GetText.add('50', '${escape(_("50"))}')

// Deluge.Menus.js:157
GetText.add('500', '${escape(_("500"))}')

// Deluge.Menus.js:119, Deluge.Menus.js:137
GetText.add('80 KiB/s', '${escape(_("80 KiB/s"))}')

// Deluge.Preferences.Queue.js:70
GetText.add('Active Torrents', '${escape(_("Active Torrents"))}')

// Deluge.ConnectionManager.js:64, Deluge.ConnectionManager.js:222, Deluge.Add.Url.js:55, Deluge.Toolbar.js:51, Deluge.Add.js:384, Deluge.EditTrackers.js:58, Deluge.EditTrackers.js:237, Deluge.Add.File.js:55
GetText.add('Add', '${escape(_("Add"))}')

// Deluge.ConnectionManager.js:52
GetText.add('Add Connection', '${escape(_("Add Connection"))}')

// Deluge.Add.js:184
GetText.add('Add In Paused State', '${escape(_("Add In Paused State"))}')

// Deluge.Add.js:366
GetText.add('Add Torrents', '${escape(_("Add Torrents"))}')

// Deluge.EditTrackers.js:39
GetText.add('Add Tracker', '${escape(_("Add Tracker"))}')

// Deluge.Add.File.js:47
GetText.add('Add from File', '${escape(_("Add from File"))}')

// Deluge.Add.Url.js:47
GetText.add('Add from Url', '${escape(_("Add from Url"))}')

// Deluge.Preferences.Downloads.js:142
GetText.add('Add torrents in Paused state', '${escape(_("Add torrents in Paused state"))}')

// Deluge.Torrents.js:184
GetText.add('Added', '${escape(_("Added"))}')

// Deluge.Sidebar.js:198
GetText.add('All', '${escape(_("All"))}')

// Deluge.Add.js:114, Deluge.Preferences.Downloads.js:97
GetText.add('Allocation', '${escape(_("Allocation"))}')

// Deluge.Preferences.Daemon.js:81
GetText.add('Allow Remote Connections', '${escape(_("Allow Remote Connections"))}')

// Deluge.Details.Options.js:347, Deluge.Preferences.js:91
GetText.add('Apply', '${escape(_("Apply"))}')

// Deluge.Menus.js:182, Deluge.Details.Options.js:215
GetText.add('Auto Managed', '${escape(_("Auto Managed"))}')

// Deluge.Preferences.Downloads.js:88
GetText.add('Autoadd .torrent files from', '${escape(_("Autoadd .torrent files from"))}')

// Deluge.Torrents.js:178
GetText.add('Avail', '${escape(_("Avail"))}')

// Deluge.Add.js:144, Deluge.Details.Options.js:88, Deluge.Preferences.Bandwidth.js:39
GetText.add('Bandwidth', '${escape(_("Bandwidth"))}')

// Deluge.Preferences.Other.js:63
GetText.add('Be alerted about new releases', '${escape(_("Be alerted about new releases"))}')

// Deluge.Menus.js:210
GetText.add('Bottom', '${escape(_("Bottom"))}')

// Deluge.Preferences.Plugins.js:74, Deluge.Add.File.js:70
GetText.add('Browse', '${escape(_("Browse"))}')

// Deluge.Preferences.Cache.js:39
GetText.add('Cache', '${escape(_("Cache"))}')

// Deluge.Preferences.Cache.js:71
GetText.add('Cache Expiry (seconds)', '${escape(_("Cache Expiry (seconds)"))}')

// Deluge.Preferences.Cache.js:59
GetText.add('Cache Size (16 KiB Blocks)', '${escape(_("Cache Size (16 KiB Blocks)"))}')

// Deluge.Add.js:383, Deluge.MoveStorage.js:56, Deluge.EditTrackers.js:57, Deluge.EditTrackers.js:116, Deluge.EditTrackers.js:178, Deluge.Remove.js:53
GetText.add('Cancel', '${escape(_("Cancel"))}')

// Deluge.Preferences.js:55
GetText.add('Categories', '${escape(_("Categories"))}')

// Deluge.Preferences.Interface.js:180
GetText.add('Certificate', '${escape(_("Certificate"))}')

// Deluge.Preferences.Interface.js:118
GetText.add('Change', '${escape(_("Change"))}')

// Deluge.Preferences.Interface.js:227
GetText.add('Change Successful', '${escape(_("Change Successful"))}')

// Deluge.ConnectionManager.js:63, Deluge.ConnectionManager.js:171, Deluge.Preferences.js:90
GetText.add('Close', '${escape(_("Close"))}')

// Deluge.Add.js:137
GetText.add('Compact', '${escape(_("Compact"))}')

// Deluge.Preferences.Interface.js:106
GetText.add('Confirm Password', '${escape(_("Confirm Password"))}')

// Deluge.ConnectionManager.js:172, Deluge.ConnectionManager.js:284
GetText.add('Connect', '${escape(_("Connect"))}')

// Deluge.ConnectionManager.js:277, Deluge.ConnectionManager.js:322
GetText.add('Connected', '${escape(_("Connected"))}')

// Deluge.Menus.js:145
GetText.add('Connection Limit', '${escape(_("Connection Limit"))}')

// Deluge.ConnectionManager.js:159, Deluge.Toolbar.js:99
GetText.add('Connection Manager', '${escape(_("Connection Manager"))}')

// Deluge.Statusbar.js:25, Deluge.Preferences.Daemon.js:72
GetText.add('Connections', '${escape(_("Connections"))}')

// Deluge.Add.Url.js:73
GetText.add('Cookies', '${escape(_("Cookies"))}')

// Deluge.Preferences.Downloads.js:80
GetText.add('Copy of .torrent files to', '${escape(_("Copy of .torrent files to"))}')

// Deluge.Toolbar.js:44
GetText.add('Create', '${escape(_("Create"))}')

// Deluge.Menus.js:109
GetText.add('D/L Speed Limit', '${escape(_("D/L Speed Limit"))}')

// Deluge.Preferences.Network.js:229, Deluge.Preferences.Proxy.js:202
GetText.add('DHT', '${escape(_("DHT"))}')

// Deluge.Statusbar.js:52
GetText.add('DHT Nodes', '${escape(_("DHT Nodes"))}')

// Deluge.Preferences.Daemon.js:39
GetText.add('Daemon', '${escape(_("Daemon"))}')

// Deluge.Preferences.Daemon.js:58
GetText.add('Daemon port', '${escape(_("Daemon port"))}')

// Deluge.Details.Details.js:36
GetText.add('Details', '${escape(_("Details"))}')

// Deluge.Preferences.Encryption.js:66, Deluge.Preferences.Encryption.js:82
GetText.add('Disabled', '${escape(_("Disabled"))}')

// Deluge.ConnectionManager.js:279
GetText.add('Disconnect', '${escape(_("Disconnect"))}')

// Deluge.Menus.js:410, Deluge.js:107
GetText.add('Do Not Download', '${escape(_("Do Not Download"))}')

// Deluge.Preferences.Queue.js:117
GetText.add('Do not count slow torrents', '${escape(_("Do not count slow torrents"))}')

// Deluge.Toolbar.js:86, Deluge.Menus.js:204, Deluge.EditTrackers.js:231
GetText.add('Down', '${escape(_("Down"))}')

// Deluge.Torrents.js:154
GetText.add('Down Speed', '${escape(_("Down Speed"))}')

// Deluge.Add.js:94
GetText.add('Download Location', '${escape(_("Download Location"))}')

// Deluge.Statusbar.js:32
GetText.add('Download Speed', '${escape(_("Download Speed"))}')

// Deluge.Preferences.Downloads.js:66
GetText.add('Download to', '${escape(_("Download to"))}')

// Deluge.Preferences.Downloads.js:39
GetText.add('Downloads', '${escape(_("Downloads"))}')

// Deluge.Torrents.js:166
GetText.add('ETA', '${escape(_("ETA"))}')

// Deluge.EditTrackers.js:243
GetText.add('Edit', '${escape(_("Edit"))}')

// Deluge.EditTrackers.js:98
GetText.add('Edit Tracker', '${escape(_("Edit Tracker"))}')

// Deluge.Menus.js:224, Deluge.Details.Options.js:329, Deluge.EditTrackers.js:160
GetText.add('Edit Trackers', '${escape(_("Edit Trackers"))}')

// Deluge.Preferences.Encryption.js:98
GetText.add('Either', '${escape(_("Either"))}')

// Deluge.Preferences.Plugins.js:157, Deluge.Preferences.Encryption.js:65, Deluge.Preferences.Encryption.js:81
GetText.add('Enabled', '${escape(_("Enabled"))}')

// Deluge.Preferences.Encryption.js:110
GetText.add('Encrypt entire stream', '${escape(_("Encrypt entire stream"))}')

// Deluge.Preferences.Encryption.js:39
GetText.add('Encryption', '${escape(_("Encryption"))}')

// Deluge.ConnectionManager.js:128, Deluge.ConnectionManager.js:391, Deluge.ConnectionManager.js:447, Deluge.Add.js:541
GetText.add('Error', '${escape(_("Error"))}')

// Deluge.Menus.js:406
GetText.add('Expand All', '${escape(_("Expand All"))}')

// Deluge.Add.js:431, Deluge.Add.File.js:67
GetText.add('File', '${escape(_("File"))}')

// Deluge.Add.js:63, Deluge.Details.Files.js:53
GetText.add('Filename', '${escape(_("Filename"))}')

// Deluge.Add.js:54, Deluge.Details.Files.js:47
GetText.add('Files', '${escape(_("Files"))}')

// Deluge.Sidebar.js:75
GetText.add('Filters', '${escape(_("Filters"))}')

// Deluge.Preferences.Plugins.js:191
GetText.add('Find More', '${escape(_("Find More"))}')

// Deluge.Preferences.Downloads.js:54
GetText.add('Folders', '${escape(_("Folders"))}')

// Deluge.Menus.js:236
GetText.add('Force Recheck', '${escape(_("Force Recheck"))}')

// Deluge.Preferences.Encryption.js:64, Deluge.Preferences.Encryption.js:80
GetText.add('Forced', '${escape(_("Forced"))}')

// Deluge.Statusbar.js:58
GetText.add('Freespace in download location', '${escape(_("Freespace in download location"))}')

// Deluge.Add.js:130
GetText.add('Full', '${escape(_("Full"))}')

// Deluge.Preferences.Encryption.js:97
GetText.add('Full Stream', '${escape(_("Full Stream"))}')

// Deluge.Preferences.Queue.js:53, Deluge.Add.js:177, Deluge.Details.Options.js:281
GetText.add('General', '${escape(_("General"))}')

// Deluge.Preferences.Other.js:94
GetText.add('GeoIP Database', '${escape(_("GeoIP Database"))}')

// Deluge.Preferences.Bandwidth.js:53
GetText.add('Global Bandwidth Usage', '${escape(_("Global Bandwidth Usage"))}')

// Deluge.Preferences.Proxy.js:61
GetText.add('HTTP', '${escape(_("HTTP"))}')

// Deluge.Preferences.Proxy.js:62
GetText.add('HTTP with Auth', '${escape(_("HTTP with Auth"))}')

// Deluge.Preferences.Encryption.js:96
GetText.add('Handshake', '${escape(_("Handshake"))}')

// Deluge.Toolbar.js:107
GetText.add('Help', '${escape(_("Help"))}')

// Deluge.Menus.js:420, Deluge.js:109
GetText.add('High Priority', '${escape(_("High Priority"))}')

// Deluge.Menus.js:425, Deluge.js:110
GetText.add('Highest Priority', '${escape(_("Highest Priority"))}')

// Deluge.ConnectionManager.js:77, Deluge.ConnectionManager.js:193, Deluge.Preferences.Proxy.js:73
GetText.add('Host', '${escape(_("Host"))}')

// Deluge.Preferences.Bandwidth.js:145
GetText.add('Ignore limits on local network', '${escape(_("Ignore limits on local network"))}')

// Deluge.Preferences.Encryption.js:58
GetText.add('Inbound', '${escape(_("Inbound"))}')

// Deluge.Preferences.Network.js:53
GetText.add('Incoming Ports', '${escape(_("Incoming Ports"))}')

// Deluge.Preferences.Plugins.js:203
GetText.add('Info', '${escape(_("Info"))}')

// Deluge.Add.js:444
GetText.add('Infohash', '${escape(_("Infohash"))}')

// Deluge.Preferences.Plugins.js:59, Deluge.Preferences.Plugins.js:186
GetText.add('Install', '${escape(_("Install"))}')

// Deluge.Preferences.Plugins.js:55
GetText.add('Install Plugin', '${escape(_("Install Plugin"))}')

// Deluge.Preferences.Interface.js:39, Deluge.Preferences.Interface.js:54
GetText.add('Interface', '${escape(_("Interface"))}')

// Deluge.Preferences.Interface.js:202
GetText.add('Invalid Password', '${escape(_("Invalid Password"))}')

// Deluge.Details.Options.js:114, Deluge.Details.Options.js:141
GetText.add('KiB/s', '${escape(_("KiB/s"))}')

// Deluge.Preferences.Network.js:223
GetText.add('LSD', '${escape(_("LSD"))}')

// Deluge.Preferences.Encryption.js:90
GetText.add('Level', '${escape(_("Level"))}')

// Deluge.Details.Status.js:57, Deluge.Details.Details.js:43
GetText.add('Loading', '${escape(_("Loading"))}')

// Deluge.MoveStorage.js:68, Deluge.Preferences.Other.js:101
GetText.add('Location', '${escape(_("Location"))}')

// Deluge.Login.js:52, Deluge.Login.js:63
GetText.add('Login', '${escape(_("Login"))}')

// Deluge.Login.js:139
GetText.add('Login Failed', '${escape(_("Login Failed"))}')

// Deluge.Toolbar.js:115
GetText.add('Logout', '${escape(_("Logout"))}')

// Deluge.Add.js:164, Deluge.Details.Options.js:150
GetText.add('Max Connections', '${escape(_("Max Connections"))}')

// Deluge.Add.js:152
GetText.add('Max Down Speed', '${escape(_("Max Down Speed"))}')

// Deluge.Details.Options.js:97
GetText.add('Max Download Speed', '${escape(_("Max Download Speed"))}')

// Deluge.Add.js:158
GetText.add('Max Up Speed', '${escape(_("Max Up Speed"))}')

// Deluge.Add.js:170, Deluge.Details.Options.js:173
GetText.add('Max Upload Slots', '${escape(_("Max Upload Slots"))}')

// Deluge.Details.Options.js:123
GetText.add('Max Upload Speed', '${escape(_("Max Upload Speed"))}')

// Deluge.Preferences.Bandwidth.js:121
GetText.add('Maximum Connection Attempts per Second', '${escape(_("Maximum Connection Attempts per Second"))}')

// Deluge.Preferences.Bandwidth.js:61, Deluge.Preferences.Bandwidth.js:166
GetText.add('Maximum Connections', '${escape(_("Maximum Connections"))}')

// Deluge.Preferences.Bandwidth.js:85, Deluge.Preferences.Bandwidth.js:190
GetText.add('Maximum Download Speed (KiB/s)', '${escape(_("Maximum Download Speed (KiB/s)"))}')

// Deluge.Preferences.Bandwidth.js:109
GetText.add('Maximum Half-Open Connections', '${escape(_("Maximum Half-Open Connections"))}')

// Deluge.Preferences.Bandwidth.js:73, Deluge.Preferences.Bandwidth.js:178
GetText.add('Maximum Upload Slots', '${escape(_("Maximum Upload Slots"))}')

// Deluge.Preferences.Bandwidth.js:97, Deluge.Preferences.Bandwidth.js:202
GetText.add('Maximum Upload Speed (KiB/s)', '${escape(_("Maximum Upload Speed (KiB/s)"))}')

// Deluge.MoveStorage.js:57
GetText.add('Move', '${escape(_("Move"))}')

// Deluge.Details.Options.js:262
GetText.add('Move Completed', '${escape(_("Move Completed"))}')

// Deluge.Menus.js:242, Deluge.MoveStorage.js:39
GetText.add('Move Storage', '${escape(_("Move Storage"))}')

// Deluge.Preferences.Downloads.js:72
GetText.add('Move completed to', '${escape(_("Move completed to"))}')

// Deluge.Preferences.Network.js:209
GetText.add('NAT-PMP', '${escape(_("NAT-PMP"))}')

// Deluge.Torrents.js:124
GetText.add('Name', '${escape(_("Name"))}')

// Deluge.Preferences.Network.js:40
GetText.add('Network', '${escape(_("Network"))}')

// Deluge.Preferences.Network.js:192
GetText.add('Network Extras', '${escape(_("Network Extras"))}')

// Deluge.Preferences.Network.js:161
GetText.add('Network Interface', '${escape(_("Network Interface"))}')

// Deluge.Preferences.Interface.js:102
GetText.add('New Password', '${escape(_("New Password"))}')

// Deluge.Preferences.Proxy.js:57
GetText.add('None', '${escape(_("None"))}')

// Deluge.Menus.js:415, Deluge.js:108
GetText.add('Normal Priority', '${escape(_("Normal Priority"))}')

// Deluge.Statusbar.js:7
GetText.add('Not Connected', '${escape(_("Not Connected"))}')

// Deluge.Add.js:542
GetText.add('Not a valid torrent', '${escape(_("Not a valid torrent"))}')

// Deluge.Preferences.Notification.js:1
GetText.add('Notification', '${escape(_("Notification"))}')

// Deluge.ConnectionManager.js:280, Deluge.ConnectionManager.js:288
GetText.add('Offline', '${escape(_("Offline"))}')

// Deluge.EditTrackers.js:179, Deluge.Preferences.js:92
GetText.add('Ok', '${escape(_("Ok"))}')

// Deluge.Preferences.Interface.js:98
GetText.add('Old Password', '${escape(_("Old Password"))}')

// Deluge.Add.js:85, Deluge.Menus.js:105, Deluge.Details.Options.js:50, Deluge.Preferences.Downloads.js:125
GetText.add('Options', '${escape(_("Options"))}')

// Deluge.Menus.js:301, Deluge.Menus.js:348, Deluge.Menus.js:395, Deluge.Preferences.Daemon.js:88, Deluge.Preferences.Other.js:39
GetText.add('Other', '${escape(_("Other"))}')

// Deluge.Preferences.Encryption.js:74
GetText.add('Outbound', '${escape(_("Outbound"))}')

// Deluge.Preferences.Network.js:108
GetText.add('Outgoing Ports', '${escape(_("Outgoing Ports"))}')

// Deluge.ConnectionManager.js:109, Deluge.Preferences.Interface.js:85, Deluge.Preferences.Interface.js:217, Deluge.Preferences.Proxy.js:100, Deluge.Login.js:75
GetText.add('Password', '${escape(_("Password"))}')

// Deluge.Toolbar.js:65, Deluge.Menus.js:93
GetText.add('Pause', '${escape(_("Pause"))}')

// Deluge.Preferences.Proxy.js:184
GetText.add('Peer', '${escape(_("Peer"))}')

// Deluge.Preferences.Network.js:216
GetText.add('Peer Exchange', '${escape(_("Peer Exchange"))}')

// Deluge.Preferences.Network.js:185
GetText.add('Peer TOS Byte', '${escape(_("Peer TOS Byte"))}')

// Deluge.Details.Peers.js:64, Deluge.Torrents.js:148
GetText.add('Peers', '${escape(_("Peers"))}')

// Deluge.Preferences.Bandwidth.js:158
GetText.add('Per Torrent Bandwidth Usage', '${escape(_("Per Torrent Bandwidth Usage"))}')

// Deluge.Preferences.Daemon.js:97
GetText.add('Periodically check the website for new releases', '${escape(_("Periodically check the website for new releases"))}')

// Deluge.Preferences.Plugins.js:164
GetText.add('Plugin', '${escape(_("Plugin"))}')

// Deluge.Preferences.Plugins.js:71
GetText.add('Plugin Egg', '${escape(_("Plugin Egg"))}')

// Deluge.Preferences.Plugins.js:113
GetText.add('Plugins', '${escape(_("Plugins"))}')

// Deluge.ConnectionManager.js:85, Deluge.Preferences.Interface.js:151, Deluge.Preferences.Proxy.js:80, Deluge.Preferences.Daemon.js:53
GetText.add('Port', '${escape(_("Port"))}')

// Deluge.Toolbar.js:92, Deluge.Preferences.js:50
GetText.add('Preferences', '${escape(_("Preferences"))}')

// Deluge.Details.Options.js:296
GetText.add('Prioritize First/Last', '${escape(_("Prioritize First/Last"))}')

// Deluge.Add.js:190
GetText.add('Prioritize First/Last Pieces', '${escape(_("Prioritize First/Last Pieces"))}')

// Deluge.Preferences.Downloads.js:136
GetText.add('Prioritize first and last pieces of torrent', '${escape(_("Prioritize first and last pieces of torrent"))}')

// Deluge.Details.Files.js:67
GetText.add('Priority', '${escape(_("Priority"))}')

// Deluge.Details.Options.js:288
GetText.add('Private', '${escape(_("Private"))}')

// Deluge.Preferences.Interface.js:173
GetText.add('Private Key', '${escape(_("Private Key"))}')

// Deluge.Details.Files.js:62, Deluge.Torrents.js:136
GetText.add('Progress', '${escape(_("Progress"))}')

// Deluge.Statusbar.js:46
GetText.add('Protocol Traffic Download/Upload', '${escape(_("Protocol Traffic Download/Upload"))}')

// Deluge.Preferences.Proxy.js:175
GetText.add('Proxy', '${escape(_("Proxy"))}')

// Deluge.Preferences.Queue.js:39, Deluge.Menus.js:187, Deluge.Details.Options.js:196
GetText.add('Queue', '${escape(_("Queue"))}')

// Deluge.Preferences.Queue.js:63
GetText.add('Queue new torrents to top', '${escape(_("Queue new torrents to top"))}')

// Deluge.Preferences.Bandwidth.js:152
GetText.add('Rate limit IP overhead', '${escape(_("Rate limit IP overhead"))}')

// Deluge.Torrents.js:172
GetText.add('Ratio', '${escape(_("Ratio"))}')

// Deluge.ConnectionManager.js:229, Deluge.Toolbar.js:58, Deluge.Add.js:450, Deluge.EditTrackers.js:249
GetText.add('Remove', '${escape(_("Remove"))}')

// Deluge.Menus.js:230, Deluge.Remove.js:38, Deluge.Remove.js:55
GetText.add('Remove Torrent', '${escape(_("Remove Torrent"))}')

// Deluge.Remove.js:54
GetText.add('Remove With Data', '${escape(_("Remove With Data"))}')

// Deluge.Details.Options.js:253
GetText.add('Remove at ratio', '${escape(_("Remove at ratio"))}')

// Deluge.Preferences.Queue.js:209
GetText.add('Remove torrent when share ratio is reached', '${escape(_("Remove torrent when share ratio is reached"))}')

// Deluge.Toolbar.js:72, Deluge.Menus.js:99
GetText.add('Resume', '${escape(_("Resume"))}')

// Deluge.EditTrackers.js:117
GetText.add('Save', '${escape(_("Save"))}')

// Deluge.Preferences.Queue.js:154
GetText.add('Seed Time (m)', '${escape(_("Seed Time (m)"))}')

// Deluge.Torrents.js:142
GetText.add('Seeders', '${escape(_("Seeders"))}')

// Deluge.Preferences.Queue.js:123
GetText.add('Seeding', '${escape(_("Seeding"))}')

// Deluge.Add.File.js:66
GetText.add('Select a torrent', '${escape(_("Select a torrent"))}')

// Deluge.Preferences.Plugins.js:70
GetText.add('Select an egg', '${escape(_("Select an egg"))}')

// Deluge.Preferences.Interface.js:130
GetText.add('Server', '${escape(_("Server"))}')

// Deluge.Preferences.Interface.js:141
GetText.add('Session Timeout', '${escape(_("Session Timeout"))}')

// Deluge.Preferences.Cache.js:53, Deluge.Preferences.Encryption.js:53
GetText.add('Settings', '${escape(_("Settings"))}')

// Deluge.Preferences.Queue.js:130
GetText.add('Share Ratio Limit', '${escape(_("Share Ratio Limit"))}')

// Deluge.Preferences.Queue.js:142
GetText.add('Share Time Ratio', '${escape(_("Share Time Ratio"))}')

// Deluge.Preferences.Interface.js:72
GetText.add('Show filters with zero torrents', '${escape(_("Show filters with zero torrents"))}')

// Deluge.Preferences.Interface.js:65
GetText.add('Show session speed in titlebar', '${escape(_("Show session speed in titlebar"))}')

// Deluge.Preferences.Interface.js:79
GetText.add('Show trackers with zero torrents', '${escape(_("Show trackers with zero torrents"))}')

// Deluge.Add.js:67, Deluge.Details.Files.js:57, Deluge.Torrents.js:130
GetText.add('Size', '${escape(_("Size"))}')

// Deluge.Preferences.Proxy.js:58
GetText.add('Socksv4', '${escape(_("Socksv4"))}')

// Deluge.Preferences.Proxy.js:59
GetText.add('Socksv5', '${escape(_("Socksv5"))}')

// Deluge.Preferences.Proxy.js:60
GetText.add('Socksv5 with Auth', '${escape(_("Socksv5 with Auth"))}')

// Deluge.ConnectionManager.js:291
GetText.add('Start Daemon', '${escape(_("Start Daemon"))}')

// Deluge.Sidebar.js:37
GetText.add('State', '${escape(_("State"))}')

// Deluge.ConnectionManager.js:186, Deluge.Details.Status.js:35
GetText.add('Status', '${escape(_("Status"))}')

// Deluge.ConnectionManager.js:237, Deluge.ConnectionManager.js:297, Deluge.ConnectionManager.js:415
GetText.add('Stop Daemon', '${escape(_("Stop Daemon"))}')

// Deluge.Details.Options.js:225
GetText.add('Stop seed at ratio', '${escape(_("Stop seed at ratio"))}')

// Deluge.Preferences.Queue.js:183
GetText.add('Stop seeding when share ratio reaches:', '${escape(_("Stop seeding when share ratio reaches:"))}')

// Deluge.Preferences.Other.js:69
GetText.add('System Information', '${escape(_("System Information"))}')

// Deluge.Preferences.Network.js:177
GetText.add('TOS', '${escape(_("TOS"))}')

// Deluge.EditTrackers.js:198
GetText.add('Tier', '${escape(_("Tier"))}')

// Deluge.Menus.js:192
GetText.add('Top', '${escape(_("Top"))}')

// Deluge.Preferences.Queue.js:77
GetText.add('Total Active', '${escape(_("Total Active"))}')

// Deluge.Preferences.Queue.js:89
GetText.add('Total Active Downloading', '${escape(_("Total Active Downloading"))}')

// Deluge.Preferences.Queue.js:101
GetText.add('Total Active Seeding', '${escape(_("Total Active Seeding"))}')

// Deluge.Preferences.Proxy.js:196, Deluge.Torrents.js:190, Deluge.EditTrackers.js:126, Deluge.EditTrackers.js:205
GetText.add('Tracker', '${escape(_("Tracker"))}')

// Deluge.Sidebar.js:38
GetText.add('Tracker Host', '${escape(_("Tracker Host"))}')

// Deluge.EditTrackers.js:67
GetText.add('Trackers', '${escape(_("Trackers"))}')

// Deluge.Preferences.Proxy.js:50
GetText.add('Type', '${escape(_("Type"))}')

// Deluge.Menus.js:127
GetText.add('U/L Speed Limit', '${escape(_("U/L Speed Limit"))}')

// Deluge.Preferences.Network.js:203
GetText.add('UPnP', '${escape(_("UPnP"))}')

// Deluge.Menus.js:123, Deluge.Menus.js:141, Deluge.Menus.js:159, Deluge.Menus.js:177, Deluge.Menus.js:295, Deluge.Menus.js:342, Deluge.Menus.js:389
GetText.add('Unlimited', '${escape(_("Unlimited"))}')

// Deluge.Toolbar.js:79, Deluge.Menus.js:198, Deluge.EditTrackers.js:225
GetText.add('Up', '${escape(_("Up"))}')

// Deluge.Torrents.js:160
GetText.add('Up Speed', '${escape(_("Up Speed"))}')

// Deluge.Menus.js:218
GetText.add('Update Tracker', '${escape(_("Update Tracker"))}')

// Deluge.Preferences.Other.js:53
GetText.add('Updates', '${escape(_("Updates"))}')

// Deluge.Menus.js:163
GetText.add('Upload Slot Limit', '${escape(_("Upload Slot Limit"))}')

// Deluge.Statusbar.js:39
GetText.add('Upload Speed', '${escape(_("Upload Speed"))}')

// Deluge.Preferences.Plugins.js:83
GetText.add('Uploading your plugin...', '${escape(_("Uploading your plugin..."))}')

// Deluge.Add.File.js:81
GetText.add('Uploading your torrent...', '${escape(_("Uploading your torrent..."))}')

// Deluge.Add.Url.js:65, Deluge.Add.js:437
GetText.add('Url', '${escape(_("Url"))}')

// Deluge.Preferences.Downloads.js:117
GetText.add('Use Compact', '${escape(_("Use Compact"))}')

// Deluge.Preferences.Downloads.js:114
GetText.add('Use Full', '${escape(_("Use Full"))}')

// Deluge.Preferences.Network.js:62, Deluge.Preferences.Network.js:117
GetText.add('Use Random Ports', '${escape(_("Use Random Ports"))}')

// Deluge.Preferences.Interface.js:165
GetText.add('Use SSL (paths relative to Deluge config folder)', '${escape(_("Use SSL (paths relative to Deluge config folder)"))}')

// Deluge.ConnectionManager.js:101, Deluge.Preferences.Proxy.js:93
GetText.add('Username', '${escape(_("Username"))}')

// Deluge.ConnectionManager.js:199
GetText.add('Version', '${escape(_("Version"))}')

// Deluge.Preferences.Proxy.js:190
GetText.add('Web Seed', '${escape(_("Web Seed"))}')

// Deluge.Preferences.Other.js:87
GetText.add('Yes, please send anonymous statistics', '${escape(_("Yes, please send anonymous statistics"))}')

// Deluge.Login.js:140
GetText.add('You entered an incorrect password', '${escape(_("You entered an incorrect password"))}')

// Deluge.Preferences.Interface.js:218
GetText.add('Your old password was incorrect!', '${escape(_("Your old password was incorrect!"))}')

// Deluge.Preferences.Interface.js:228
GetText.add('Your password was successfully changed!', '${escape(_("Your password was successfully changed!"))}')

// Deluge.Preferences.Interface.js:203
GetText.add('Your passwords don\'t match!', '${escape(_("Your passwords don\'t match!"))}')


