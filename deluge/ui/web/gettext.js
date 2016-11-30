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

// TorrentGrid.js:105
GetText.add('#', '${escape(_("#"))}')

// DetailsTab.js:50
GetText.add('# of files', '${escape(_("# of files"))}')

// Menus.js:206
GetText.add('0', '${escape(_("0"))}')

// Menus.js:211
GetText.add('1', '${escape(_("1"))}')

// Menus.js:100, Menus.js:137
GetText.add('10 KiB/s', '${escape(_("10 KiB/s"))}')

// Menus.js:174
GetText.add('100', '${escape(_("100"))}')

// Menus.js:216
GetText.add('2', '${escape(_("2"))}')

// Menus.js:179
GetText.add('200', '${escape(_("200"))}')

// Menus.js:221
GetText.add('3', '${escape(_("3"))}')

// Menus.js:105, Menus.js:142
GetText.add('30 KiB/s', '${escape(_("30 KiB/s"))}')

// Menus.js:184
GetText.add('300', '${escape(_("300"))}')

// Menus.js:115, Menus.js:152
GetText.add('300 KiB/s', '${escape(_("300 KiB/s"))}')

// Menus.js:226
GetText.add('5', '${escape(_("5"))}')

// Menus.js:95, Menus.js:132
GetText.add('5 KiB/s', '${escape(_("5 KiB/s"))}')

// Menus.js:169
GetText.add('50', '${escape(_("50"))}')

// Menus.js:189
GetText.add('500', '${escape(_("500"))}')

// Menus.js:110, Menus.js:147
GetText.add('80 KiB/s', '${escape(_("80 KiB/s"))}')

// QueuePage.js:69
GetText.add('Active Torrents', '${escape(_("Active Torrents"))}')

// EditTrackersWindow.js:112, ConnectionManager.js:110, AddConnectionWindow.js:56, Toolbar.js:58, AddTrackerWindow.js:66, UrlWindow.js:50, FileWindow.js:53, AddWindow.js:52
GetText.add('Add', '${escape(_("Add"))}')

// AddConnectionWindow.js:40
GetText.add('Add Connection', '${escape(_("Add Connection"))}')

// OptionsTab.js:161
GetText.add('Add In Paused State', '${escape(_("Add In Paused State"))}')

// AddWindow.js:37
GetText.add('Add Torrents', '${escape(_("Add Torrents"))}')

// AddTrackerWindow.js:49
GetText.add('Add Tracker', '${escape(_("Add Tracker"))}')

// FileWindow.js:40
GetText.add('Add from File', '${escape(_("Add from File"))}')

// UrlWindow.js:36
GetText.add('Add from Url', '${escape(_("Add from Url"))}')

// DownloadsPage.js:146
GetText.add('Add torrents in Paused state', '${escape(_("Add torrents in Paused state"))}')

// TorrentGrid.js:176
GetText.add('Added', '${escape(_("Added"))}')

// FilterPanel.js:124
GetText.add('All', '${escape(_("All"))}')

// OptionsTab.js:94, DownloadsPage.js:100
GetText.add('Allocation', '${escape(_("Allocation"))}')

// DaemonPage.js:77
GetText.add('Allow Remote Connections', '${escape(_("Allow Remote Connections"))}')

// InterfacePage.js:78
GetText.add('Allow the use of multiple filters at once', '${escape(_("Allow the use of multiple filters at once"))}')

// StatusTab.js:119
GetText.add('Announce OK', '${escape(_("Announce OK"))}')

// StatusTab.js:120
GetText.add('Announce Sent', '${escape(_("Announce Sent"))}')

// OptionsTab.js:347, PreferencesWindow.js:107
GetText.add('Apply', '${escape(_("Apply"))}')

// Menus.js:238, OptionsTab.js:215
GetText.add('Auto Managed', '${escape(_("Auto Managed"))}')

// DownloadsPage.js:91
GetText.add('Autoadd .torrent files from', '${escape(_("Autoadd .torrent files from"))}')

// TorrentGrid.js:169
GetText.add('Avail', '${escape(_("Avail"))}')

// FileBrowser.js:47
GetText.add('Back', '${escape(_("Back"))}')

// OptionsTab.js:88, OptionsTab.js:124, BandwidthPage.js:42
GetText.add('Bandwidth', '${escape(_("Bandwidth"))}')

// OtherPage.js:66
GetText.add('Be alerted about new releases', '${escape(_("Be alerted about new releases"))}')

// Menus.js:280
GetText.add('Bottom', '${escape(_("Bottom"))}')

// MoveStorage.js:73, FileWindow.js:70, InstallPluginWindow.js:69
GetText.add('Browse', '${escape(_("Browse"))}')

// CachePage.js:41
GetText.add('Cache', '${escape(_("Cache"))}')

// CachePage.js:69
GetText.add('Cache Expiry (seconds)', '${escape(_("Cache Expiry (seconds)"))}')

// CachePage.js:63
GetText.add('Cache Size (16 KiB Blocks)', '${escape(_("Cache Size (16 KiB Blocks)"))}')

// EditTrackersWindow.js:56, OtherLimitWindow.js:72, RemoveWindow.js:55, MoveStorage.js:55, EditTrackerWindow.js:56, AddTrackerWindow.js:65, AddWindow.js:51
GetText.add('Cancel', '${escape(_("Cancel"))}')

// PreferencesWindow.js:85
GetText.add('Categories', '${escape(_("Categories"))}')

// InterfacePage.js:173
GetText.add('Certificate', '${escape(_("Certificate"))}')

// InterfacePage.js:117
GetText.add('Change', '${escape(_("Change"))}')

// ConnectionManager.js:284
GetText.add('Change Default Password', '${escape(_("Change Default Password"))}')

// InterfacePage.js:224
GetText.add('Change Successful', '${escape(_("Change Successful"))}')

// ConnectionManager.js:54, AddConnectionWindow.js:55, PreferencesWindow.js:106
GetText.add('Close', '${escape(_("Close"))}')

// DetailsTab.js:51
GetText.add('Comment', '${escape(_("Comment"))}')

// OptionsTab.js:117
GetText.add('Compact', '${escape(_("Compact"))}')

// InterfacePage.js:105
GetText.add('Confirm Password', '${escape(_("Confirm Password"))}')

// ConnectionManager.js:55, ConnectionManager.js:193
GetText.add('Connect', '${escape(_("Connect"))}')

// ConnectionManager.js:79
GetText.add('Connected', '${escape(_("Connected"))}')

// Menus.js:163
GetText.add('Connection Limit', '${escape(_("Connection Limit"))}')

// ConnectionManager.js:43, Toolbar.js:100
GetText.add('Connection Manager', '${escape(_("Connection Manager"))}')

// UI.js:151
GetText.add('Connection restored', '${escape(_("Connection restored"))}')

// Statusbar.js:57, DaemonPage.js:68
GetText.add('Connections', '${escape(_("Connections"))}')

// UrlWindow.js:68
GetText.add('Cookies', '${escape(_("Cookies"))}')

// DownloadsPage.js:83
GetText.add('Copy of .torrent files to', '${escape(_("Copy of .torrent files to"))}')

// Toolbar.js:52
GetText.add('Create', '${escape(_("Create"))}')

// Menus.js:89
GetText.add('D/L Speed Limit', '${escape(_("D/L Speed Limit"))}')

// NetworkPage.js:225, ProxyPage.js:70
GetText.add('DHT', '${escape(_("DHT"))}')

// Statusbar.js:210
GetText.add('DHT Nodes', '${escape(_("DHT Nodes"))}')

// DaemonPage.js:41
GetText.add('Daemon', '${escape(_("Daemon"))}')

// DaemonPage.js:57
GetText.add('Daemon port', '${escape(_("Daemon port"))}')

// Toolbar.js:45
GetText.add('Deluge', '${escape(_("Deluge"))}')

// DetailsTab.js:36
GetText.add('Details', '${escape(_("Details"))}')

// EncryptionPage.js:65, EncryptionPage.js:82
GetText.add('Disabled', '${escape(_("Disabled"))}')

// ConnectionManager.js:188
GetText.add('Disconnect', '${escape(_("Disconnect"))}')

// Menus.js:327, Deluge.js:163
GetText.add('Do Not Download', '${escape(_("Do Not Download"))}')

// QueuePage.js:107
GetText.add('Do not count slow torrents', '${escape(_("Do not count slow torrents"))}')

// EditTrackersWindow.js:107, Menus.js:274, Toolbar.js:89
GetText.add('Down', '${escape(_("Down"))}')

// TorrentGrid.js:211
GetText.add('Down Limit', '${escape(_("Down Limit"))}')

// TorrentGrid.js:130
GetText.add('Down Speed', '${escape(_("Down Speed"))}')

// FilesTab.js:63
GetText.add('Download', '${escape(_("Download"))}')

// OptionsTab.js:55
GetText.add('Download Location', '${escape(_("Download Location"))}')

// Statusbar.js:104
GetText.add('Download Speed', '${escape(_("Download Speed"))}')

// DownloadsPage.js:69
GetText.add('Download to', '${escape(_("Download to"))}')

// TorrentGrid.js:197
GetText.add('Downloaded', '${escape(_("Downloaded"))}')

// DownloadsPage.js:42
GetText.add('Downloads', '${escape(_("Downloads"))}')

// TorrentGrid.js:142
GetText.add('ETA', '${escape(_("ETA"))}')

// EditTrackersWindow.js:117
GetText.add('Edit', '${escape(_("Edit"))}')

// EditTrackerWindow.js:40
GetText.add('Edit Tracker', '${escape(_("Edit Tracker"))}')

// EditTrackersWindow.js:40, Menus.js:294, OptionsTab.js:332
GetText.add('Edit Trackers', '${escape(_("Edit Trackers"))}')

// EncryptionPage.js:99
GetText.add('Either', '${escape(_("Either"))}')

// EncryptionPage.js:64, EncryptionPage.js:81, PluginsPage.js:81
GetText.add('Enabled', '${escape(_("Enabled"))}')

// EncryptionPage.js:112
GetText.add('Encrypt entire stream', '${escape(_("Encrypt entire stream"))}')

// EncryptionPage.js:41
GetText.add('Encryption', '${escape(_("Encryption"))}')

// ConnectionManager.js:316, ConnectionManager.js:372, AddConnectionWindow.js:103, StatusTab.js:117, UrlWindow.js:116, FileWindow.js:103, AddWindow.js:211
GetText.add('Error', '${escape(_("Error"))}')

// Menus.js:323
GetText.add('Expand All', '${escape(_("Expand All"))}')

// UrlWindow.js:117
GetText.add('Failed to download torrent', '${escape(_("Failed to download torrent"))}')

// FileWindow.js:104
GetText.add('Failed to upload torrent', '${escape(_("Failed to upload torrent"))}')

// FileWindow.js:67, AddWindow.js:98
GetText.add('File', '${escape(_("File"))}')

// FileBrowser.js:36
GetText.add('File Browser', '${escape(_("File Browser"))}')

// OptionsPanel.js:143
GetText.add('File prioritization is unavailable when using Compact allocation. Would you like to switch to Full allocation?', '${escape(_("File prioritization is unavailable when using Compact allocation. Would you like to switch to Full allocation?"))}')

// FilesTab.js:40, FilesTab.js:50
GetText.add('Filename', '${escape(_("Filename"))}')

// FilesTab.js:35, FilesTab.js:41
GetText.add('Files', '${escape(_("Files"))}')

// Sidebar.js:55
GetText.add('Filters', '${escape(_("Filters"))}')

// PluginsPage.js:118
GetText.add('Find More', '${escape(_("Find More"))}')

// DownloadsPage.js:57
GetText.add('Folders', '${escape(_("Folders"))}')

// Menus.js:306
GetText.add('Force Recheck', '${escape(_("Force Recheck"))}')

// EncryptionPage.js:63, EncryptionPage.js:80
GetText.add('Forced', '${escape(_("Forced"))}')

// FileBrowser.js:50
GetText.add('Forward', '${escape(_("Forward"))}')

// Statusbar.js:216
GetText.add('Freespace in download location', '${escape(_("Freespace in download location"))}')

// OptionsTab.js:110
GetText.add('Full', '${escape(_("Full"))}')

// EncryptionPage.js:98
GetText.add('Full Stream', '${escape(_("Full Stream"))}')

// OptionsTab.js:293, OptionsTab.js:154, QueuePage.js:52
GetText.add('General', '${escape(_("General"))}')

// OtherPage.js:97
GetText.add('GeoIP Database', '${escape(_("GeoIP Database"))}')

// BandwidthPage.js:56
GetText.add('Global Bandwidth Usage', '${escape(_("Global Bandwidth Usage"))}')

// ProxyField.js:59
GetText.add('HTTP', '${escape(_("HTTP"))}')

// ProxyField.js:60
GetText.add('HTTP with Auth', '${escape(_("HTTP with Auth"))}')

// EncryptionPage.js:97
GetText.add('Handshake', '${escape(_("Handshake"))}')

// DetailsTab.js:47
GetText.add('Hash', '${escape(_("Hash"))}')

// Toolbar.js:107
GetText.add('Help', '${escape(_("Help"))}')

// Menus.js:337, Deluge.js:165
GetText.add('High Priority', '${escape(_("High Priority"))}')

// Menus.js:342, Deluge.js:166
GetText.add('Highest Priority', '${escape(_("Highest Priority"))}')

// FileBrowser.js:56
GetText.add('Home', '${escape(_("Home"))}')

// ConnectionManager.js:84, AddConnectionWindow.js:66, ProxyField.js:74
GetText.add('Host', '${escape(_("Host"))}')

// BandwidthPage.js:122
GetText.add('Ignore limits on local network', '${escape(_("Ignore limits on local network"))}')

// EncryptionPage.js:57
GetText.add('Inbound', '${escape(_("Inbound"))}')

// NetworkPage.js:51
GetText.add('Incoming Ports', '${escape(_("Incoming Ports"))}')

// PluginsPage.js:135
GetText.add('Info', '${escape(_("Info"))}')

// AddWindow.js:107
GetText.add('Infohash', '${escape(_("Infohash"))}')

// InstallPluginWindow.js:54, PluginsPage.js:113
GetText.add('Install', '${escape(_("Install"))}')

// InstallPluginWindow.js:40
GetText.add('Install Plugin', '${escape(_("Install Plugin"))}')

// InterfacePage.js:41, InterfacePage.js:53
GetText.add('Interface', '${escape(_("Interface"))}')

// InterfacePage.js:199
GetText.add('Invalid Password', '${escape(_("Invalid Password"))}')

// OptionsTab.js:114, OptionsTab.js:141
GetText.add('KiB/s', '${escape(_("KiB/s"))}')

// Statusbar.js:144, Statusbar.js:192
GetText.add('Kib/s', '${escape(_("Kib/s"))}')

// NetworkPage.js:219
GetText.add('LSD', '${escape(_("LSD"))}')

// EncryptionPage.js:91
GetText.add('Level', '${escape(_("Level"))}')

// StatusTab.js:61
GetText.add('Loading', '${escape(_("Loading"))}')

// MoveStorage.js:67, OtherPage.js:104
GetText.add('Location', '${escape(_("Location"))}')

// LoginWindow.js:45, LoginWindow.js:54
GetText.add('Login', '${escape(_("Login"))}')

// LoginWindow.js:130
GetText.add('Login Failed', '${escape(_("Login Failed"))}')

// Toolbar.js:114
GetText.add('Logout', '${escape(_("Logout"))}')

// OptionsTab.js:150, OptionsTab.js:143
GetText.add('Max Connections', '${escape(_("Max Connections"))}')

// OptionsTab.js:133
GetText.add('Max Down Speed', '${escape(_("Max Down Speed"))}')

// OptionsTab.js:97
GetText.add('Max Download Speed', '${escape(_("Max Download Speed"))}')

// OptionsTab.js:138
GetText.add('Max Up Speed', '${escape(_("Max Up Speed"))}')

// OptionsTab.js:173, OptionsTab.js:148
GetText.add('Max Upload Slots', '${escape(_("Max Upload Slots"))}')

// OptionsTab.js:123
GetText.add('Max Upload Speed', '${escape(_("Max Upload Speed"))}')

// BandwidthPage.js:103
GetText.add('Maximum Connection Attempts per Second', '${escape(_("Maximum Connection Attempts per Second"))}')

// BandwidthPage.js:68, BandwidthPage.js:147
GetText.add('Maximum Connections', '${escape(_("Maximum Connections"))}')

// BandwidthPage.js:82, BandwidthPage.js:161
GetText.add('Maximum Download Speed (KiB/s)', '${escape(_("Maximum Download Speed (KiB/s)"))}')

// BandwidthPage.js:96
GetText.add('Maximum Half-Open Connections', '${escape(_("Maximum Half-Open Connections"))}')

// BandwidthPage.js:75, BandwidthPage.js:154
GetText.add('Maximum Upload Slots', '${escape(_("Maximum Upload Slots"))}')

// BandwidthPage.js:89, BandwidthPage.js:168
GetText.add('Maximum Upload Speed (KiB/s)', '${escape(_("Maximum Upload Speed (KiB/s)"))}')

// MoveStorage.js:56
GetText.add('Move', '${escape(_("Move"))}')

// OptionsTab.js:262
GetText.add('Move Completed', '${escape(_("Move Completed"))}')

// OptionsTab.js:72
GetText.add('Move Completed Location', '${escape(_("Move Completed Location"))}')

// Menus.js:312, MoveStorage.js:38
GetText.add('Move Storage', '${escape(_("Move Storage"))}')

// DownloadsPage.js:75
GetText.add('Move completed to', '${escape(_("Move completed to"))}')

// NetworkPage.js:205
GetText.add('NAT-PMP', '${escape(_("NAT-PMP"))}')

// TorrentGrid.js:112, DetailsTab.js:46
GetText.add('Name', '${escape(_("Name"))}')

// NetworkPage.js:42
GetText.add('Network', '${escape(_("Network"))}')

// NetworkPage.js:188
GetText.add('Network Extras', '${escape(_("Network Extras"))}')

// NetworkPage.js:157
GetText.add('Network Interface', '${escape(_("Network Interface"))}')

// InterfacePage.js:101
GetText.add('New Password', '${escape(_("New Password"))}')

// ProxyField.js:55
GetText.add('None', '${escape(_("None"))}')

// Menus.js:332, Deluge.js:164
GetText.add('Normal Priority', '${escape(_("Normal Priority"))}')

// Statusbar.js:39
GetText.add('Not Connected', '${escape(_("Not Connected"))}')

// AddWindow.js:212
GetText.add('Not a valid torrent', '${escape(_("Not a valid torrent"))}')

// Menus.js:248
GetText.add('Off', '${escape(_("Off"))}')

// ConnectionManager.js:76
GetText.add('Offline', '${escape(_("Offline"))}')

// EditTrackersWindow.js:57, OtherLimitWindow.js:73, PreferencesWindow.js:108
GetText.add('Ok', '${escape(_("Ok"))}')

// InterfacePage.js:97
GetText.add('Old Password', '${escape(_("Old Password"))}')

// Menus.js:243
GetText.add('On', '${escape(_("On"))}')

// ConnectionManager.js:73
GetText.add('Online', '${escape(_("Online"))}')

// Menus.js:84, OptionsTab.js:49, OptionsTab.js:40, DownloadsPage.js:129
GetText.add('Options', '${escape(_("Options"))}')

// Statusbar.js:90, Statusbar.js:138, Statusbar.js:186, OtherPage.js:42, DaemonPage.js:84
GetText.add('Other', '${escape(_("Other"))}')

// EncryptionPage.js:74
GetText.add('Outbound', '${escape(_("Outbound"))}')

// NetworkPage.js:104
GetText.add('Outgoing Ports', '${escape(_("Outgoing Ports"))}')

// AddConnectionWindow.js:88, LoginWindow.js:70, ProxyField.js:101, InterfacePage.js:84, InterfacePage.js:214
GetText.add('Password', '${escape(_("Password"))}')

// DetailsTab.js:48
GetText.add('Path', '${escape(_("Path"))}')

// Menus.js:73, Toolbar.js:70
GetText.add('Pause', '${escape(_("Pause"))}')

// ProxyPage.js:52
GetText.add('Peer', '${escape(_("Peer"))}')

// NetworkPage.js:212
GetText.add('Peer Exchange', '${escape(_("Peer Exchange"))}')

// NetworkPage.js:181
GetText.add('Peer TOS Byte', '${escape(_("Peer TOS Byte"))}')

// TorrentGrid.js:155, TorrentGrid.js:225, PeersTab.js:63
GetText.add('Peers', '${escape(_("Peers"))}')

// BandwidthPage.js:135
GetText.add('Per Torrent Bandwidth Usage', '${escape(_("Per Torrent Bandwidth Usage"))}')

// DaemonPage.js:93
GetText.add('Periodically check the website for new releases', '${escape(_("Periodically check the website for new releases"))}')

// PluginsPage.js:92
GetText.add('Plugin', '${escape(_("Plugin"))}')

// InstallPluginWindow.js:66
GetText.add('Plugin Egg', '${escape(_("Plugin Egg"))}')

// PluginsPage.js:41
GetText.add('Plugins', '${escape(_("Plugins"))}')

// AddConnectionWindow.js:72, ProxyField.js:82, DaemonPage.js:52, InterfacePage.js:147
GetText.add('Port', '${escape(_("Port"))}')

// Toolbar.js:94, PreferencesWindow.js:47
GetText.add('Preferences', '${escape(_("Preferences"))}')

// OptionsTab.js:308
GetText.add('Prioritize First/Last', '${escape(_("Prioritize First/Last"))}')

// OptionsTab.js:167
GetText.add('Prioritize First/Last Pieces', '${escape(_("Prioritize First/Last Pieces"))}')

// DownloadsPage.js:140
GetText.add('Prioritize first and last pieces of torrent', '${escape(_("Prioritize first and last pieces of torrent"))}')

// FilesTab.js:60
GetText.add('Priority', '${escape(_("Priority"))}')

// OptionsTab.js:300
GetText.add('Private', '${escape(_("Private"))}')

// InterfacePage.js:166
GetText.add('Private Key', '${escape(_("Private Key"))}')

// TorrentGrid.js:124, FilesTab.js:52
GetText.add('Progress', '${escape(_("Progress"))}')

// Statusbar.js:200
GetText.add('Protocol Traffic Download/Upload', '${escape(_("Protocol Traffic Download/Upload"))}')

// ProxyPage.js:42
GetText.add('Proxy', '${escape(_("Proxy"))}')

// Menus.js:256, OptionsTab.js:196, QueuePage.js:41
GetText.add('Queue', '${escape(_("Queue"))}')

// QueuePage.js:62
GetText.add('Queue new torrents to top', '${escape(_("Queue new torrents to top"))}')

// BandwidthPage.js:129
GetText.add('Rate limit IP overhead', '${escape(_("Rate limit IP overhead"))}')

// TorrentGrid.js:162
GetText.add('Ratio', '${escape(_("Ratio"))}')

// EditTrackersWindow.js:122, ConnectionManager.js:117, Toolbar.js:64, AddWindow.js:112
GetText.add('Remove', '${escape(_("Remove"))}')

// Menus.js:300, RemoveWindow.js:39, RemoveWindow.js:57
GetText.add('Remove Torrent', '${escape(_("Remove Torrent"))}')

// RemoveWindow.js:56
GetText.add('Remove With Data', '${escape(_("Remove With Data"))}')

// OptionsTab.js:253
GetText.add('Remove at ratio', '${escape(_("Remove at ratio"))}')

// QueuePage.js:191
GetText.add('Remove torrent when share ratio is reached', '${escape(_("Remove torrent when share ratio is reached"))}')

// Menus.js:79, Toolbar.js:76
GetText.add('Resume', '${escape(_("Resume"))}')

// EditTrackerWindow.js:57
GetText.add('Save', '${escape(_("Save"))}')

// TorrentGrid.js:190
GetText.add('Save Path', '${escape(_("Save Path"))}')

// QueuePage.js:142
GetText.add('Seed Time (m)', '${escape(_("Seed Time (m)"))}')

// TorrentGrid.js:148, TorrentGrid.js:225
GetText.add('Seeders', '${escape(_("Seeders"))}')

// QueuePage.js:113
GetText.add('Seeding', '${escape(_("Seeding"))}')

// FileWindow.js:66
GetText.add('Select a torrent', '${escape(_("Select a torrent"))}')

// InstallPluginWindow.js:65
GetText.add('Select an egg', '${escape(_("Select an egg"))}')

// InterfacePage.js:129
GetText.add('Server', '${escape(_("Server"))}')

// InterfacePage.js:140
GetText.add('Session Timeout', '${escape(_("Session Timeout"))}')

// Statusbar.js:96
GetText.add('Set Maximum Connections', '${escape(_("Set Maximum Connections"))}')

// Statusbar.js:143
GetText.add('Set Maximum Download Speed', '${escape(_("Set Maximum Download Speed"))}')

// Statusbar.js:191
GetText.add('Set Maximum Upload Speed', '${escape(_("Set Maximum Upload Speed"))}')

// EncryptionPage.js:51, CachePage.js:52
GetText.add('Settings', '${escape(_("Settings"))}')

// QueuePage.js:120
GetText.add('Share Ratio Limit', '${escape(_("Share Ratio Limit"))}')

// QueuePage.js:131
GetText.add('Share Time Ratio', '${escape(_("Share Time Ratio"))}')

// InterfacePage.js:71
GetText.add('Show filters with zero torrents', '${escape(_("Show filters with zero torrents"))}')

// InterfacePage.js:64
GetText.add('Show session speed in titlebar', '${escape(_("Show session speed in titlebar"))}')

// TorrentGrid.js:118, FilesTab.js:44, FilesTab.js:54
GetText.add('Size', '${escape(_("Size"))}')

// ProxyField.js:56
GetText.add('Socksv4', '${escape(_("Socksv4"))}')

// ProxyField.js:57
GetText.add('Socksv5', '${escape(_("Socksv5"))}')

// ProxyField.js:58
GetText.add('Socksv5 with Auth', '${escape(_("Socksv5 with Auth"))}')

// ConnectionManager.js:200
GetText.add('Start Daemon', '${escape(_("Start Daemon"))}')

// Sidebar.js:34
GetText.add('State', '${escape(_("State"))}')

// ConnectionManager.js:68, StatusTab.js:39, DetailsTab.js:52
GetText.add('Status', '${escape(_("Status"))}')

// ConnectionManager.js:125, ConnectionManager.js:206, ConnectionManager.js:336
GetText.add('Stop Daemon', '${escape(_("Stop Daemon"))}')

// OptionsTab.js:225
GetText.add('Stop seed at ratio', '${escape(_("Stop seed at ratio"))}')

// QueuePage.js:168
GetText.add('Stop seeding when share ratio reaches:', '${escape(_("Stop seeding when share ratio reaches:"))}')

// OtherPage.js:72
GetText.add('System Information', '${escape(_("System Information"))}')

// NetworkPage.js:173
GetText.add('TOS', '${escape(_("TOS"))}')

// EditTrackersWindow.js:76
GetText.add('Tier', '${escape(_("Tier"))}')

// Menus.js:262
GetText.add('Top', '${escape(_("Top"))}')

// QueuePage.js:76
GetText.add('Total Active', '${escape(_("Total Active"))}')

// QueuePage.js:85
GetText.add('Total Active Downloading', '${escape(_("Total Active Downloading"))}')

// QueuePage.js:94
GetText.add('Total Active Seeding', '${escape(_("Total Active Seeding"))}')

// DetailsTab.js:49
GetText.add('Total Size', '${escape(_("Total Size"))}')

// EditTrackersWindow.js:80, TorrentGrid.js:183, EditTrackerWindow.js:66, DetailsTab.js:53, ProxyPage.js:64
GetText.add('Tracker', '${escape(_("Tracker"))}')

// Sidebar.js:35
GetText.add('Tracker Host', '${escape(_("Tracker Host"))}')

// AddTrackerWindow.js:75
GetText.add('Trackers', '${escape(_("Trackers"))}')

// ProxyField.js:48
GetText.add('Type', '${escape(_("Type"))}')

// Menus.js:126
GetText.add('U/L Speed Limit', '${escape(_("U/L Speed Limit"))}')

// NetworkPage.js:199
GetText.add('UPnP', '${escape(_("UPnP"))}')

// OptionsPanel.js:142
GetText.add('Unable to set file priority!', '${escape(_("Unable to set file priority!"))}')

// Statusbar.js:85, Statusbar.js:133, Statusbar.js:181, Menus.js:120, Menus.js:157, Menus.js:194, Menus.js:231
GetText.add('Unlimited', '${escape(_("Unlimited"))}')

// EditTrackersWindow.js:102, Menus.js:268, Toolbar.js:83, FileBrowser.js:53
GetText.add('Up', '${escape(_("Up"))}')

// TorrentGrid.js:218
GetText.add('Up Limit', '${escape(_("Up Limit"))}')

// TorrentGrid.js:136
GetText.add('Up Speed', '${escape(_("Up Speed"))}')

// Menus.js:288
GetText.add('Update Tracker', '${escape(_("Update Tracker"))}')

// OtherPage.js:56
GetText.add('Updates', '${escape(_("Updates"))}')

// Menus.js:200
GetText.add('Upload Slot Limit', '${escape(_("Upload Slot Limit"))}')

// Statusbar.js:152
GetText.add('Upload Speed', '${escape(_("Upload Speed"))}')

// TorrentGrid.js:204
GetText.add('Uploaded', '${escape(_("Uploaded"))}')

// InstallPluginWindow.js:78
GetText.add('Uploading your plugin...', '${escape(_("Uploading your plugin..."))}')

// FileWindow.js:82
GetText.add('Uploading your torrent...', '${escape(_("Uploading your torrent..."))}')

// UrlWindow.js:60, AddWindow.js:102
GetText.add('Url', '${escape(_("Url"))}')

// DownloadsPage.js:121
GetText.add('Use Compact', '${escape(_("Use Compact"))}')

// DownloadsPage.js:118
GetText.add('Use Full', '${escape(_("Use Full"))}')

// NetworkPage.js:60, NetworkPage.js:113
GetText.add('Use Random Ports', '${escape(_("Use Random Ports"))}')

// InterfacePage.js:158
GetText.add('Use SSL (paths relative to Deluge config folder)', '${escape(_("Use SSL (paths relative to Deluge config folder)"))}')

// AddConnectionWindow.js:83, ProxyField.js:93
GetText.add('Username', '${escape(_("Username"))}')

// ConnectionManager.js:90
GetText.add('Version', '${escape(_("Version"))}')

// StatusTab.js:118
GetText.add('Warning', '${escape(_("Warning"))}')

// ConnectionManager.js:285
GetText.add('We recommend changing the default password.<br><br>Would you like to change it now?', '${escape(_("We recommend changing the default password.<br><br>Would you like to change it now?"))}')

// ProxyPage.js:58
GetText.add('Web Seed', '${escape(_("Web Seed"))}')

// OtherPage.js:90
GetText.add('Yes, please send anonymous statistics', '${escape(_("Yes, please send anonymous statistics"))}')

// LoginWindow.js:131
GetText.add('You entered an incorrect password', '${escape(_("You entered an incorrect password"))}')

// InterfacePage.js:215
GetText.add('Your old password was incorrect!', '${escape(_("Your old password was incorrect!"))}')

// InterfacePage.js:225
GetText.add('Your password was successfully changed!', '${escape(_("Your password was successfully changed!"))}')

// InterfacePage.js:200
GetText.add('Your passwords don\'t match!', '${escape(_("Your passwords don\'t match!"))}')

