# Ubuntu Upstart Job

**This page only applies to Ubuntu 11.04 Natty up to 14.10 Utopic, for newer Ubuntu distributions see: [systemd](/userguide/service/systemd).**

Firstly ensure Deluge daemon and Web UI are installed:

```
sudo apt-get install deluged deluge-web
```

## User Management

It is best to run Deluge upstart scripts with a specific user and group. You can create one using the following command:

```
sudo adduser --system --group --home /var/lib/deluge deluge
```

* This creates a new system user and group named `deluge` with no login access and home directory: `/var/lib/deluge`

Add any users you wish to be able to easily manage or access files downloaded through Deluge to the group deluge will run as, for example:

```
sudo adduser <username> deluge
```

## Deluge Daemon (deluged) Job

Create the file `/etc/init/deluged.conf` with the following code and set `uid` and `gid` to the user and group you wish to run `deluged` as:

*Note: 11.04 Natty users replace `static-network-up` with `stopped networking`*

```
# deluged - Deluge daemon
#
# The daemon component of Deluge BitTorrent client. Deluge UI clients
# connect to this daemon via DelugeRPC protocol.

description "Deluge daemon"
author "Deluge Team"

start on filesystem and static-network-up
stop on runlevel [016]

respawn
respawn limit 5 30

env uid=deluge
env gid=deluge
env umask=007

exec start-stop-daemon -S -c $uid:$gid -k $umask -x /usr/bin/deluged -- -d
```
* You may wish to modify the above `umask` as it applies to any files downloaded by deluged.
  * 007 grants full access to the user and members of the group deluged is running as (in this case deluge) and prevents access from all other accounts.
  * 022 grants full access to the user deluged is running as and only read access to other accounts.
  * 000 grants full access to all accounts.
 Refer to [Wikipedia](http://en.wikipedia.org/wiki/Umask#Octal_umasks) for details of possible values and their effects. Deluged must be stopped and started instead of just restarted after changes. If you enable logging, as described later in this page, the umasks specified here also affect the permissions of newly created logs.

## Deluge Web UI (deluge-web) Job

Create the file `/etc/init/deluge-web.conf` with the following code and set `uid` and `gid` as required:'''

```
# deluge-web - Deluge Web UI
#
# The Web UI component of Deluge BitTorrent client, connects to deluged and
# provides a web application interface for users. Default url: http://localhost:8112

description "Deluge Web UI"
author "Deluge Team"

start on started deluged
stop on stopping deluged

respawn
respawn limit 5 30

env uid=deluge
env gid=deluge
env umask=027

exec start-stop-daemon -S -c $uid:$gid -k $umask -x /usr/bin/deluge-web
```
 *umask `027` grants full access to `uid`, read access to `gid` and prevents access from all other accounts. This should only affect the permissions of plugins installed through the Web UI and, if enabled, logs. Group permissions are restricted to read-only to prevent compromised member accounts injecting malicious code into plugins or modifying the logs.*


## Migration from init.d script
If you followed the old guide to create an init script you need to remove them:

```
sudo /etc/init.d/deluge-daemon stop
sudo rm /etc/init.d/deluge-daemon
sudo update-rc.d deluge-daemon remove
```

## Starting (and stopping) Upstart Scripts

### Deluge Daemon

```
sudo start deluged
```

```
sudo stop deluged
```

### Web UI
Although the Web UI will start/stop automatically when deluged starts/stops it can be manually controlled with:

```
sudo start deluge-web
```

```
sudo stop deluge-web
```
*Note: To prevent the web UI starting automatically comment out (# prefix) the '`start on`' line in `deluge-web.conf`.*

## Logging
Create a structure for Deluge to log to and give the user that Deluge is running as (in this case `deluge`) full access to that directory:

```
sudo mkdir -p /var/log/deluge
sudo chown -R deluge:deluge /var/log/deluge
sudo chmod -R 750 /var/log/deluge
```
* Note: The above commands affect the log directory and all files within it, combined with the umask specified in the upstart jobs these affect the permissions new logs are created with.
  * 750 grants full access to the deluge user, only recurse tree and read access to members of the deluge group and prevents access from all other accounts. [Chmod](http://en.wikipedia.org/wiki/Chmod#Octal_numbers)
Edit the upstart job confs like so:

```
exec start-stop-daemon -S -c $uid:$gid -k $umask -x /usr/bin/deluged -- -d -l /var/log/deluge/daemon.log -L warning
```

```
exec start-stop-daemon -S -c $uid:$gid -k $umask -x /usr/bin/deluge-web -- -l /var/log/deluge/web.log -L warning
```
* Refer to the [FAQ](/faq#enabledelugelogging) for possible log-levels.

Restart the daemon:

```
sudo restart deluged
```

Create `/etc/logrotate.d/deluge` with the following code to rotate the logs:

```
/var/log/deluge/*.log {
        rotate 4
        weekly
        missingok
        notifempty
        compress
        delaycompress
        sharedscripts
        postrotate
                initctl restart deluged >/dev/null 2>&1 || true
                initctl restart deluge-web >/dev/null 2>&1 || true
        endscript
}
```