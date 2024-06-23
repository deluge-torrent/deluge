## Bandwidth Tweaking

The settings below are suggestions.  They are intended to give users more guidance than the settings recommended in the FAQ, but are by no means definitive.

The most important thing to remember is: **The speed of your downloads is determined by the speed of your uploads.**  That's built into the bittorrent protocol, and works through what is known as "choking."

From the [BitTorrent protocol](http://www.bittorrent.org/beps/bep_0003.html):

>Choking is done for several reasons. TCP congestion control behaves very poorly when sending over many connections at once. Also, choking lets each peer use a tit-for-tat-ish algorithm to ensure that they get a consistent download rate.

>There are several criteria a good choking algorithm should meet. It should cap the number of simultaneous uploads for good TCP performance. It should avoid choking and unchoking quickly, known as 'fibrillation'. It should reciprocate to peers who let it download. Finally, it should try out unused connections once in a while to find out if they might be better than the currently used ones, known as optimistic unchoking.

>The currently deployed choking algorithm avoids fibrillation by only changing who's choked once every ten seconds. It does reciprocation and number of uploads capping by unchoking the four peers which it has the best download rates from and are interested. Peers which have a better upload rate but aren't interested get unchoked and if they become interested the worst uploader gets choked. If a downloader has a complete file, it uses its upload rate rather than its download rate to decide who to unchoke.

>For optimistic unchoking, at any one time there is a single peer which is unchoked regardless of it's upload rate (if interested, it counts as one of the four allowed downloaders.) Which peer is optimistically unchoked rotates every 30 seconds. To give them a decent chance of getting a complete piece to upload, new connections are three times as likely to start as the current optimistic unchoke as anywhere else in the rotation.

If you don't set up your uploading setting properly, you will be forever choked on your downloads.

### Determine Internet Connection Speed

Go to [SpeedTest.net](http://speedtest.net/) to test your connection.  It's best to do this with all other applications, including Deluge, closed.  You also should run the test a few times, hours or days apart, to make sure your initial results were accurate.

SpeedTest.net by default will give you results in Mbps (Mb/s). To see the results in KB/s (which is what deluge's preferences uses):
1. Click on "Settings", located in the top left corner of the page
2. Select "kilobytes" under "Speed Measurement"
3. Click "Save"

### Preferences: Bandwidth

#### Global Settings

|                     |         |                                                                                                    |
|---------------------|---------|----------------------------------------------------------------------------------------------------|
| Maximum Connections | **250** | (You may never see this many connections depending on your per-torrent and active-torrent limits.) |
| Maximum Upload Slots | **4** | (Let libtorrent manage this for you.  It will open more upload slots as necessary to utilize available upstream bandwidth.) |
| Maximum Download Speed | **80 - 95%** of tested download speed | (Be careful of setting this too high--it can strangle your browsing, media streaming, etc. and other people who use your connection.)
| Maximum Upload Speed | **80%** of tested upload speed | (Upload speed is the limiter for most p2p applications.) |
| Maximum Half-Open Connections: | **10 - 50** | (Unless you've got a Windows install with limited half-open connections.  Then this should be 80% of that limit.) |

Everyone got all excited when it was noticed that Microsoft had initially limited half-open connections in XP and Vista to small numbers.  As a plethora of hacks came out to remove this limit, somehow "half-open connections" became the scape-goat for slow download speeds.  Suddenly it became *de riguer* to advise Windows users to hack the TCP/IP driver and set their half-open connections to something huge, like 200.

Most users have no need for a setting that high, and Microsoft has removed the original limit in later releases/patches, and made it user-adjustable.  (Do not patch your tcpip.sys or whatever--just update to the current official release.)  The reality is that half-open connections should--rapidly--resolve to fully-opened connections or be timed-out, so you really don't need that many of them hanging around, anyway.

|                                        |        |                                                                                                                                                                                                                                    |
|----------------------------------------|--------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Maximum Connection Attempts per Second | **20** | (When you set your per-torrent connections and such to a reasonable number, you will establish reliable connections with plenty of peers.  You shouldn't need to be banging around for thousands of new connections every minute.) |


#### Per Torrent Settings

|                         |            |                |                 |             |
|-------------------------|------------|----------------|-----------------|-------------|
| *For upload speeds of:* | < 50 KiB/s | 50 - 150 KiB/s | 150 - 250 KiB/s | > 250 KiB/s |
| Maximum Connections  | 30 | 50 | 80 | 120 |
| Maximum Upload Slots | 4  | 5  | 7  | 8   |

While a basic premise of bit-torrenting is a big-ol' "swarm" of peers, you, as a single client, can spread yourself too thin.  You're more helpful to the swarm by feeding a limited number of peers with a steady, thick stream of data, than you are by spraying out droplets of data to a huge number of peers.

So, you should limit your upload slots based on your upload speeds to make sure that each connected peer is getting a reasonable amount of bandwidth.

You should limit your number of connections because it take resources to keep track of each connection, and why track connections that are giving you a trickle if any data?  One peer feeding you 5 KiB/s is worth 50 peers flickering at 0.1 KiB/s.  Similarly, you don't want/need to be keeping track of a large number of peers waiting around hoping one of your upload slots comes free.

|                        |    |                                                                |
|------------------------|----|----------------------------------------------------------------|
| Maximum Download Speed | -1 | (Let the per-torrent speed be limited by the global settings.) |
| Maximum Upload Speed | -1 | (Let the per-torrent speed be limited by the global settings.) |

You can, by setting the per-torrent maximums to less than the global maximums, prevent a single torrent from using up all the allocated bandwidth and forcing all of the other (auto-managed) torrents to pause.  But there is no advantage to increasing your number of active torrents.  Indeed, by letting the torrent with the best speeds dominate, it will finish as quickly as possible and then stop competing for resources with the other torrents in the queue.


### Preferences: Queue

#### Active Torrents

|                         |            |                |                 |             |
|-------------------------|------------|----------------|-----------------|-------------|
| *For upload speeds of:* | < 50 KiB/s | 50 - 150 KiB/s | 150 - 250 KiB/s | > 250 KiB/s |
| Total active             | 3 | 5 | 10 | 15 |
| Total active downloading | 3 | 4 | 8  | 10 |
| Total active seeding:    | 3 | 5 | 10 | 15 |

By setting "active downloading" less than the "total active" you can make sure that you are seeding completed torrents at all times.

Deluge always prioritizes downloads over uploads, so seeding can be set the same as total but all of your downloading slots will still get used.

 *Note*: All downloading torrents are automatically also seeding.

### Example Results

|                                  |     |     |     |     |
|----------------------------------|-----|-----|-----|-----|
| Assumed upload speed (KiB/s)     | 25  | 50  | 150 | 250 |
| Total active torrents            | 3   | 5   | 10  | 15  |
| Maximum upload slots per torrent | 4   | 5   | 7   | 8   |
| Maximum total upload slots       | 12  | 25  | 70  | 120 |
| Worst-case KiB/s per upload slot | 2.1 | 2.0 | 2.1 | 2.1 |
| Worst-case KiB/s per torrent     | 8.3 | 10  | 15  | 17  |