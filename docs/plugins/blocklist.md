# Blocklist Plugin

Currently this plugin can handle PeerGuardian (text only), SafePeer and Emule lists.

*Note: 7zip format files are not supported.* 

Generally PeerGuardian files come in 7zip format, so you'll need to extract them first and then feed Deluge the plain text file. Files may be specified as URL's to a website, the local filesystem, or a network host.

## Example URL's

Unix URL's of a local file:

```
file:///home/username/the%20file.dat.gz
file://localhost/home/username/the%20file.dat.gz
```

Windows URL's of a local file:

```
file:///c:/path/to/the%20file.dat.gz
file://localhost/c:/path/to/the%20file.dat.gz
```

URL of a network (LAN/WAN) file:

```
file://hostname/shared/the%20file.dat.gz
```

## Download

The Deluge Team does not evaluate or endorse any specific blocklists anymore, however you can search the internet (e.g. `blocklist url`) to find and evaluate your own ones.

## Multiple lists

When you import a new blocklist, the new IP's are combined with the previously loaded ones.  The only way to clear it at the moment is by restarting deluge(d).
