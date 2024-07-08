
# Improving the speed of Deluge

We have been working on optimizing Deluge to use less resources and handle more torrents. Most issues with speed gets noticable when the number of torrents grow past a given threshold. Deluge 1.3 will not be getting any more optimizations or improvements, so any new code will go into the develop branch.

Tickets for performance issues that have not yet been fixed or applied to the develop branch are listed in the [performance milestone](http://dev.deluge-torrent.org/query?group=status&milestone=performance).


# Current state of Deluge (v1.3)

Deluge v1.3 handles hundreds of torrents fairly well. The GTKUI uses a lot of CPU to render the torrent list, so to keep CPU usage at a minimum it is a good idea to run in deamon/client mode and only connect with to the daemon when you need.

When the torrent list reaches 1000 torrents, the CPU usage gets more and more noticable, the more torrents the slower it gets.

The following patches have been applied to 1.3:
* [Cache tracker icons in gtkui ([#2248](https://dev.deluge-torrent.org/ticket/2248))](http://dev.deluge-torrent.orghttps://dev.deluge-torrent.org/ticket/2248) [git commit](http://git.deluge-torrent.org/deluge/commit/?h=1.3-stable&id=36a78d8f219f) (gtkui)
* [Small (but significant) speed optimizations to the torrentview ([#2259](https://dev.deluge-torrent.org/ticket/2259))](http://dev.deluge-torrent.orghttps://dev.deluge-torrent.org/ticket/2259)  [git commit](http://git.deluge-torrent.org/deluge/commit/?h=1.3-stable&id=a0ae3ebfce826980d08f6e75ec62a48e39cd5b41) (gtkui) (smaller version of [#2184](https://dev.deluge-torrent.org/ticket/2184) for 1.3 branch)
* [Speed optimizations to the torrentview in GTKUI ([#2184](https://dev.deluge-torrent.org/ticket/2184))](http://dev.deluge-torrent.orghttps://dev.deluge-torrent.org/ticket/2184), [git commit](http://git.deluge-torrent.org/deluge/commit/?h=1.3-stable&id=5dba83853308482827aaecd1be1e79be97e30d15)

# State of git-develop (To be v2)

git-develop has been tested and works well with 2-3000 torrents. Currently the biggest problem is that to make libtorrent v0.16.X handle that many active torrents, the settings *active_dht_limit*, *active_tracker_limit*, *active_lsd_limit* must be set. This is currently not implemented in git-develop, but applying the patch proposed in [#2257](https://dev.deluge-torrent.org/ticket/2257) should solve this. this can also be fixed by using the ltconfig plugin found in the [list of plugins](http://dev.deluge-torrent.org/wiki/plugins).

The following patches have already been applied which improves the speed of Deluge with many torrents greatly:

## GTKUI patches==
* [Speed optimizations to the torrentview in GTKUI ([#2184](https://dev.deluge-torrent.org/ticket/2184))](http://dev.deluge-torrent.orghttps://dev.deluge-torrent.org/ticket/2184), [git commit](http://git.deluge-torrent.org/deluge/commit/?id=b4f5e78a775503a5501e2eba7eee73dfa0e1955a)
* [Cache tracker icons in gtkui ([#2248](https://dev.deluge-torrent.org/ticket/2248))](http://dev.deluge-torrent.orghttps://dev.deluge-torrent.org/ticket/2248) ([git commit](http://git.deluge-torrent.org/deluge/commit/?id=463ac0c07eda1b33b145e1b9be7edbc0981815a99))
* [Speed optimizations to sessionproxy ([#2285](https://dev.deluge-torrent.org/ticket/2285))](http://dev.deluge-torrent.orghttps://dev.deluge-torrent.org/ticket/2285) [git commit](http://git.deluge-torrent.org/deluge/commit/?h=develop&id=5503f9047)
* [Add caching to the data-funcs in ui/gtkui/torrentview_data_funcs.py](http://dev.deluge-torrent.orghttps://dev.deluge-torrent.org/ticket/1885) [git commit](http://dev.deluge-torrent.org/changeset/8ecc0e11a79d92)
* [Speedup removing multiple torrents from core ([#2250](https://dev.deluge-torrent.org/ticket/2250))](http://dev.deluge-torrent.orghttps://dev.deluge-torrent.org/ticket/2250) (gtkui)

## Core patches
* [Speed optimizations to the daemon](http://dev.deluge-torrent.orghttps://dev.deluge-torrent.org/ticket/2255) [git commit](http://git.deluge-torrent.org/deluge/commit/?id=8c106ce8c4c0794ddd63e8e8f98b097221a56a52)
* [Speedup set_prioritize_first_last in torrent.py ([#2246](https://dev.deluge-torrent.org/ticket/2246))](http://dev.deluge-torrent.orghttps://dev.deluge-torrent.org/ticket/2246), [git commit](http://git.deluge-torrent.org/deluge/commit/?id=6313ff19b322a2801c633324bb0d77dc4f59b9a1) (mainly on startup)
* [Move cleanup of prev_status from torrent.py to torrentmanager.py ([#2379](https://dev.deluge-torrent.org/ticket/2379))](http://dev.deluge-torrent.orghttps://dev.deluge-torrent.org/ticket/2379) [git commit](http://dev.deluge-torrent.org/changeset/feaeee0379)
* [Application layer protocol for transfering RPC messages + utf8 decoding error ([#2116](https://dev.deluge-torrent.org/ticket/2116))](http://dev.deluge-torrent.orghttps://dev.deluge-torrent.org/ticket/2116), [git commit](http://git.deluge-torrent.org/deluge/commit/?id=8e7432e71c80a47c96bf48c07535ec1991efe1d9) (rpc communication between daemon and clients)
* [Speed up adding multiple torrents ([#2406](https://dev.deluge-torrent.org/ticket/2406))](http://dev.deluge-torrent.orghttps://dev.deluge-torrent.org/ticket/2406) (core/gtkui)

Proposed patches:
* [Allow setting of active_dht_limit, active_tracker_limit and active_lsd_limit. Fix bugs. ([#2257](https://dev.deluge-torrent.org/ticket/2257))](http://dev.deluge-torrent.orghttps://dev.deluge-torrent.org/ticket/2257) (daemon)

Other issues that need investigation:
* Pausing/resuming multiple torrents is very slow. This is probably because when a torrent changes state, a lot of operations are done (event listeners in GUI presumable), so with hundreds of torrents changing state the result is too much work needing to be done.
* CPU usage on an idle daemon can still be around 5% ([[#1490](https://dev.deluge-torrent.org/ticket/1490)](http://dev.deluge-torrent.orghttps://dev.deluge-torrent.org/ticket/1490)).
* Reducing the number of calls (executions) torrent.update_state during startup (loading torrents)
* Investigate if libtorrent.file_progress is a bottleneck
