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

var _ = GetText.get.bind(GetText);

// deluge-menus.js:154
GetText.add('0', '${_("0")}');

// deluge-menus.js:156
GetText.add('1', '${_("1")}');

// deluge-menus.js:102, deluge-menus.js:120
GetText.add('10 KiB/s', '${_("10 KiB/s")}');

// deluge-menus.js:138
GetText.add('100', '${_("100")}');

// deluge-menus.js:158
GetText.add('2', '${_("2")}');

// deluge-menus.js:140
GetText.add('200', '${_("200")}');

// deluge-menus.js:160
GetText.add('3', '${_("3")}');

// deluge-menus.js:104, deluge-menus.js:122
GetText.add('30 KiB/s', '${_("30 KiB/s")}');

// deluge-menus.js:142
GetText.add('300', '${_("300")}');

// deluge-menus.js:108, deluge-menus.js:126
GetText.add('300 KiB/s', '${_("300 KiB/s")}');

// deluge-menus.js:162
GetText.add('5', '${_("5")}');

// deluge-menus.js:100, deluge-menus.js:118
GetText.add('5 KiB/s', '${_("5 KiB/s")}');

// deluge-menus.js:136
GetText.add('50', '${_("50")}');

// deluge-menus.js:144
GetText.add('500', '${_("500")}');

// deluge-menus.js:106, deluge-menus.js:124
GetText.add('80 KiB/s', '${_("80 KiB/s")}');

// deluge-bars.js:117, deluge-add.js:466, deluge-add.js:526, deluge-add.js:551, deluge-connections.js:218, deluge-connections.js:290
GetText.add('Add', '${_("Add")}');

// deluge-connections.js:247
GetText.add('Add Connection', '${_("Add Connection")}');

// deluge-add.js:386
GetText.add('Add In Paused State', '${_("Add In Paused State")}');

// deluge-add.js:541
GetText.add('Add Torrents', '${_("Add Torrents")}');

// deluge-add.js:462
GetText.add('Add from File', '${_("Add from File")}');

// deluge-add.js:522
GetText.add('Add from Url', '${_("Add from Url")}');

// deluge-add.js:304
GetText.add('Allocation', '${_("Allocation")}');

// deluge-details.js:690, deluge-preferences.js:35
GetText.add('Apply', '${_("Apply")}');

// deluge-add.js:395
GetText.add('Apply to All', '${_("Apply to All")}');

// deluge-details.js:636, deluge-menus.js:169
GetText.add('Auto Managed', '${_("Auto Managed")}');

// deluge-details.js:550, deluge-add.js:329
GetText.add('Bandwidth', '${_("Bandwidth")}');

// deluge-menus.js:197
GetText.add('Bottom', '${_("Bottom")}');

// deluge-add.js:290, deluge-add.js:448
GetText.add('Browse', '${_("Browse")}');

// deluge-add.js:545
GetText.add('Cancel', '${_("Cancel")}');

// deluge-connections.js:285, deluge-connections.js:311, deluge-preferences.js:33
GetText.add('Close', '${_("Close")}');

// deluge-add.js:321
GetText.add('Compact', '${_("Compact")}');

// deluge-connections.js:148, deluge-connections.js:314
GetText.add('Connect', '${_("Connect")}');

// deluge-connections.js:94, deluge-connections.js:145
GetText.add('Connected', '${_("Connected")}');

// deluge-menus.js:132
GetText.add('Connection Limit', '${_("Connection Limit")}');

// deluge-bars.js:165, deluge-connections.js:307
GetText.add('Connection Manager', '${_("Connection Manager")}');

// deluge-bars.js:110
GetText.add('Create', '${_("Create")}');

// deluge-menus.js:96
GetText.add('D/L Speed Limit', '${_("D/L Speed Limit")}');

// deluge-details.js:459
GetText.add('Details', '${_("Details")}');

// deluge-connections.js:146
GetText.add('Disconnect', '${_("Disconnect")}');

// deluge-menus.js:385
GetText.add('Do Not Download', '${_("Do Not Download")}');

// deluge-bars.js:152, deluge-menus.js:191
GetText.add('Down', '${_("Down")}');

// deluge-add.js:271
GetText.add('Download Location', '${_("Download Location")}');

// deluge-details.js:681, deluge-menus.js:211
GetText.add('Edit Trackers', '${_("Edit Trackers")}');

// deluge-add.js:141, deluge-connections.js:60, deluge-connections.js:128, deluge-connections.js:163
GetText.add('Error', '${_("Error")}');

// deluge-menus.js:381
GetText.add('Expand All', '${_("Expand All")}');

// deluge-add.js:223, deluge-add.js:445
GetText.add('File', '${_("File")}');

// deluge-details.js:475, deluge-add.js:180
GetText.add('Filename', '${_("Filename")}');

// deluge-details.js:469, deluge-add.js:258
GetText.add('Files', '${_("Files")}');

// deluge-bars.js:488
GetText.add('Filters', '${_("Filters")}');

// deluge-menus.js:223
GetText.add('Force Recheck', '${_("Force Recheck")}');

// deluge-add.js:315
GetText.add('Full', '${_("Full")}');

// deluge-details.js:660, deluge-add.js:378
GetText.add('General', '${_("General")}');

// deluge-bars.js:174
GetText.add('Help', '${_("Help")}');

// deluge-menus.js:395
GetText.add('High Priority', '${_("High Priority")}');

// deluge-menus.js:400
GetText.add('Highest Priority', '${_("Highest Priority")}');

// deluge-connections.js:255
GetText.add('Host', '${_("Host")}');

// deluge-add.js:236
GetText.add('Infohash', '${_("Infohash")}');

// deluge-details.js:84, deluge-details.js:146
GetText.add('Loading', '${_("Loading")}');

// deluge-login.js:90, deluge-login.js:94
GetText.add('Login', '${_("Login")}');

// deluge-login.js:35
GetText.add('Login Failed', '${_("Login Failed")}');

// deluge-bars.js:182
GetText.add('Logout', '${_("Logout")}');

// deluge-details.js:594, deluge-add.js:356
GetText.add('Max Connections', '${_("Max Connections")}');

// deluge-add.js:336
GetText.add('Max Down Speed', '${_("Max Down Speed")}');

// deluge-details.js:558
GetText.add('Max Download Speed', '${_("Max Download Speed")}');

// deluge-add.js:346
GetText.add('Max Up Speed', '${_("Max Up Speed")}');

// deluge-details.js:609, deluge-add.js:366
GetText.add('Max Upload Slots', '${_("Max Upload Slots")}');

// deluge-details.js:576
GetText.add('Max Upload Speed', '${_("Max Upload Speed")}');

// deluge-details.js:651
GetText.add('Move Completed', '${_("Move Completed")}');

// deluge-menus.js:229
GetText.add('Move Storage', '${_("Move Storage")}');

// deluge-menus.js:390
GetText.add('Normal Priority', '${_("Normal Priority")}');

// deluge-bars.js:332
GetText.add('Not Connected', '${_("Not Connected")}');

// deluge-add.js:142
GetText.add('Not a valid torrent', '${_("Not a valid torrent")}');

// deluge-preferences.js:37
GetText.add('Ok', '${_("Ok")}');

// deluge-details.js:533, deluge-add.js:262, deluge-menus.js:92
GetText.add('Options', '${_("Options")}');

// deluge-menus.js:276, deluge-menus.js:323, deluge-menus.js:370
GetText.add('Other', '${_("Other")}');

// deluge-connections.js:277, deluge-login.js:66
GetText.add('Password', '${_("Password")}');

// deluge-bars.js:131, deluge-menus.js:80
GetText.add('Pause', '${_("Pause")}');

// deluge-details.js:510
GetText.add('Peers', '${_("Peers")}');

// deluge-connections.js:261
GetText.add('Port', '${_("Port")}');

// deluge-bars.js:158, deluge-preferences.js:31
GetText.add('Preferences', '${_("Preferences")}');

// deluge-details.js:672
GetText.add('Prioritize First/Last', '${_("Prioritize First/Last")}');

// deluge-add.js:391
GetText.add('Prioritize First/Last Piece', '${_("Prioritize First/Last Piece")}');

// deluge-details.js:489
GetText.add('Priority', '${_("Priority")}');

// deluge-details.js:667
GetText.add('Private', '${_("Private")}');

// deluge-details.js:484
GetText.add('Progress', '${_("Progress")}');

// deluge-details.js:629, deluge-menus.js:174
GetText.add('Queue', '${_("Queue")}');

// deluge-bars.js:124, deluge-add.js:242, deluge-connections.js:224
GetText.add('Remove', '${_("Remove")}');

// deluge-menus.js:217
GetText.add('Remove Torrent', '${_("Remove Torrent")}');

// deluge-details.js:646
GetText.add('Remove at ratio', '${_("Remove at ratio")}');

// deluge-bars.js:138, deluge-menus.js:86
GetText.add('Resume', '${_("Resume")}');

// deluge-add.js:399
GetText.add('Revert to Defaults', '${_("Revert to Defaults")}');

// deluge-add.js:444
GetText.add('Select a torrent', '${_("Select a torrent")}');

// deluge-details.js:479, deluge-add.js:184
GetText.add('Size', '${_("Size")}');

// deluge-details.js:450
GetText.add('Status', '${_("Status")}');

// deluge-connections.js:230
GetText.add('Stop Daemon', '${_("Stop Daemon")}');

// deluge-details.js:641
GetText.add('Stop seed at ratio', '${_("Stop seed at ratio")}');

// deluge-menus.js:179
GetText.add('Top', '${_("Top")}');

// deluge-menus.js:114
GetText.add('U/L Speed Limit', '${_("U/L Speed Limit")}');

// deluge-menus.js:110, deluge-menus.js:128, deluge-menus.js:146, deluge-menus.js:164, deluge-menus.js:270, deluge-menus.js:317, deluge-menus.js:364
GetText.add('Unlimited', '${_("Unlimited")}');

// deluge-bars.js:145, deluge-menus.js:185
GetText.add('Up', '${_("Up")}');

// deluge-menus.js:205
GetText.add('Update Tracker', '${_("Update Tracker")}');

// deluge-menus.js:150
GetText.add('Upload Slot Limit', '${_("Upload Slot Limit")}');

// deluge-add.js:419
GetText.add('Uploading your torrent...', '${_("Uploading your torrent...")}');

// deluge-add.js:229, deluge-add.js:499
GetText.add('Url', '${_("Url")}');

// deluge-connections.js:271
GetText.add('Username', '${_("Username")}');

// deluge-login.js:36
GetText.add('You entered an incorrect password', '${_("You entered an incorrect password")}');


