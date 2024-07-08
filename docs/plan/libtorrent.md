This is page is to collate the work that is required to bring the next Deluge version up to date with libtorrent

# Deluge 1.4.0 milestone and libtorrent 0.16

## Tickets requests for new/missing libtorrent features
### Handle/Status
* [ticket:1903 [#1903](https://dev.deluge-torrent.org/ticket/1903) super_seeding (handle/status)]
* [ticket:607 [#607](https://dev.deluge-torrent.org/ticket/607) completed_time (handle)]
* [ticket:1294 [#1294](https://dev.deluge-torrent.org/ticket/1294) seed_mode (add_torrent) flag_seed_mode (status)]
* [ticket:1165 [#1165](https://dev.deluge-torrent.org/ticket/1165) add_url_seed, remove_url_seed (handle)]
* [ticket:1206 [#1206](https://dev.deluge-torrent.org/ticket/1206) set_upload_mode (handle) upload_mode (status) flag_upload_mode (add_torrent)]
* [ticket:2347 [#2347](https://dev.deluge-torrent.org/ticket/2347) orig_files (status)]

### Session
* ~~Use `flush_disk_cache` flag with `save_resume_data` when stopping session~~
* [ticket:2122 [#2122](https://dev.deluge-torrent.org/ticket/2122) listen_on_flags: listen_reuse_address and listen_no_system_port]
* [ticket:2133 [#2133](https://dev.deluge-torrent.org/ticket/2133) listen_on: Change incoming port randomization]
* [ticket:2219 [#2219](https://dev.deluge-torrent.org/ticket/2219) set_i2p_proxy() i2p_proxy()]
* ~~[ticket:1337 [#1337](https://dev.deluge-torrent.org/ticket/1337) make_magnet_uri()]~~

### Session_settings

These should be covered by the WiP by gazpachoking to query lt for all available settings.

* [ticket:2115 [#2115](https://dev.deluge-torrent.org/ticket/2115) uTP/TCP Enable/Disable]
* [ticket:1466 [#1466](https://dev.deluge-torrent.org/ticket/1466) send_buffer_watermark, send_buffer_watermark_factor]
* [ticket:1903 [#1903](https://dev.deluge-torrent.org/ticket/1903) strict_super_seeding]
* [ticket:1384 [#1384](https://dev.deluge-torrent.org/ticket/1384) announce_ip]
* [ticket:2257 [#2257](https://dev.deluge-torrent.org/ticket/2257) active_dht_limit, active_tracker_limit and active_lsd_limit]
* [ticket:2059 [#2059](https://dev.deluge-torrent.org/ticket/2059) tracker_backoff]
* [ticket:1677 [#1677](https://dev.deluge-torrent.org/ticket/1677) apply_ip_filter_to_trackers (for blocklist)]
* [ticket:1395 [#1395](https://dev.deluge-torrent.org/ticket/1395) announce_to_all_tiers]
* [ticket:2472 [#2472](https://dev.deluge-torrent.org/ticket/2472) anonymous mode]

### Alerts
* [ticket:1466 [#1466](https://dev.deluge-torrent.org/ticket/1466) performance alert: send_buffer_watermark_too_low]
* [ticket:637 [#637](https://dev.deluge-torrent.org/ticket/637) storage_moved_alert]
* [ticket:2006 [#2006](https://dev.deluge-torrent.org/ticket/2006) storage_moved_failed_alert]
* [ticket:2490 [#2490](https://dev.deluge-torrent.org/ticket/2490) Support for external_ip_alert]

# Features for future Deluge releases
* Support SSL Torrents (also see [#2195](https://dev.deluge-torrent.org/ticket/2195))
* [ticket:2196 [#2196](https://dev.deluge-torrent.org/ticket/2196) piece_deadline (handle)]
* ~~Torrent priority with set_priority (handle) priority (status)~~
* [ticket:367 [#367](https://dev.deluge-torrent.org/ticket/367) Do not store per-torrent settings that are saved in the resume data]
* ~~Replace add_torrent with the more efficient non-blocking async_add_torrent.~~

Notable libtorrent 1.0 [Changelog](http://sourceforge.net/p/libtorrent/code/HEAD/tree/branches/RC_1_0/ChangeLog) entries:

* Support magnet links wrapped in .torrent files (need more details)
* Support storing save_path in resume data
* Include name, save_path and torrent_file in torrent_status, for improved performance
* allow moving files to absolute paths, out of the download directory
* ~~add moving_storage field to torrent_status~~
* allow force_announce to only affect a single tracker (need more details)

## Deprecated Functions

To test use libtorrent build with TORRENT_NO_DEPRECATE config.