
# Plugin Ideas

## Plugin Requests on Trac

Below is a list of [query:status=accepted|new|assigned|reopened&type=plugin-request Plugin Request] tickets

## Notification Plugin

*Currently working on this:* Solexious

The Notification component currently in Deluge should be moved into a plugin.

## Importer Plugin

*Currently working on this:* Nobody

This plugin would be used for importing states from other torrent clients to ease migration.  It would be best to start with the more popular clients, such as uTorrent, Vuze and Transmission.  uTorrent's state file is just a bencoded dict, which should be pretty easy to read and convert to Deluge.  There will be some care needed to ensure the paths match up, especially if converting from another OS.

## Download in Order

*Currently working on this:* Nobody

This plugin would download individual files within a torrent in a specified order, likely alphabetical.  It would essentially set the first one with normal priority and the rest with 'do not download' and so forth as the files download.

## Auto Move Storage

*Currently working on this:* Nobody

*Currently implemented in:* Label plugin, but through an additional level of abstraction ("Labels"). Auto-move by label, and assign trackers to label.

This plugin would automatically change the target path of newly added torrents based on its tracker, with a configuration UI where you can specify simple tracker -> directory mappings.

## Pruning

*Currently working on this:* TheGenious

This plugin routinely removes torrents that have reached a certain age and when a hard drive threshold has been reached (so only remove torrents when the hard drive capacity is less than 10%).

## Users

*Currently working on this:* TheGenious

This plugin will automatically "label" torrents with the environmental variable REMOTE_USER value that is passed in by a reverse proxy or gateway for HTTP Authentication. The purpose of this is to allow multiple users to see what torrents are their own.

## Auto-replace bad peers

*Currently working on this:* Nobody

During downloading, automatically replace peers with an average download rate under a custom limit (default for instance 5kb/s) the last 20 seconds if there are other peers available.