# How to create systemd services for Linux

This guide walks you through setting up Deluge systemd services on Linux.

Ensure Deluge daemon `deluged` and Web UI `deluge-web` are installed. Use
`which` to check installation paths and if necessary modify the service
file `ExecStart` lines to point to alternative paths.

## Create a service specific user

For security it is best to run a service with a specific user and group.
You can create one using the following command:

```console
sudo adduser --system  --gecos "Deluge Service" --disabled-password --group --home /var/lib/deluge deluge
```

This creates a new system user and group named `deluge` with no login access
and home directory `/var/lib/deluge` which will be the default location for the
config files.

In addition you can add to the `deluge` group any users you wish to be able to
easily manage or access files downloaded by Deluge, for example:

```console
sudo adduser <username> deluge
```

## Daemon (deluged) service

Create the file `/etc/systemd/system/deluged.service` containing the following:

```eval_rst
.. literalinclude:: ../../../packaging/systemd/deluged.service
    :language: ini
```

### User configuration

To run the service using the previously created user e.g. `deluge`, first
create the service configuration directory:

```console
sudo mkdir /etc/systemd/system/deluged.service.d/
```

Then create a user file `/etc/systemd/system/deluged.service.d/user.conf` with
the following contents:

```eval_rst
.. literalinclude:: ../../../packaging/systemd/user.conf
    :language: ini
```

### Start deluged service

Now enable it to start up on boot, start the service and verify it is running:

```console
sudo systemctl enable /etc/systemd/system/deluged.service
sudo systemctl start deluged
sudo systemctl status deluged
```

### Umask for deluged downloaded files

The `umask` in the service file can be modified to determine access to files
downloaded by deluged (also applies to logging files). Some useful access
values are detailed as follows:

- `000` - full access for all users and groups.
- `007` - only user and group that `deluged` is running as (e.g. `deluge`)
  with no access from any other accounts.
- `002` - user and group `deluged` is running as with read-only for all other
  accounts.
- `022` - user `deluged` is running as with read-only for all other accounts.

The service for `deluged` must be stopped and started instead of just restarted
after changes.

## Web UI (deluge-web) service

Create the file `/etc/systemd/system/deluge-web.service` containing the following:

```eval_rst
.. literalinclude:: ../../../packaging/systemd/deluge-web.service
    :language: ini
```

### User configuration

To run the service using the previously created user e.g. `deluge`, first
create the service configuration directory:

```
sudo mkdir /etc/systemd/system/deluge-web.service.d/
```

Then create a user file `/etc/systemd/system/deluge-web.service.d/user.conf` with
the following contents:

```eval_rst
.. literalinclude:: ../../../packaging/systemd/user.conf
    :language: ini
```

### Start deluge-web service

Now enable it to start up on boot, start the service and verify it is running:

```console
sudo systemctl enable /etc/systemd/system/deluge-web.service
sudo systemctl start deluge-web
sudo systemctl status deluge-web
```

## Service logging

Create a log directory for Deluge and give the service user (e.g. `deluge`), full access:

```console
sudo mkdir -p /var/log/deluge
sudo chown -R deluge:deluge /var/log/deluge
sudo chmod -R 750 /var/log/deluge
```

The deluge log directory is now configured so that user `deluge` has full
access, group `deluge` read only and everyone else denied access. The `umask`
specified in the services sets the permission of new log files.

Enable logging in the service files by editing the `ExecStart` line, appending
`-l` and `-L` options:

```
ExecStart=/usr/bin/deluged -d -l /var/log/deluge/daemon.log -L warning
```

```
ExecStart=/usr/bin/deluge-web -d -l /var/log/deluge/web.log -L warning
```

See `deluged -h` for all available log-levels.

Restart the services:

```console
sudo systemctl daemon-reload
sudo systemctl restart deluged
sudo systemctl restart deluge-web
```

### Log rotation

To enable log rotation append `--logrotate` to the above `ExecStart` lines.

## Conditionally start deluged for mount points

If you have a USB disk drive or network drive that may not be immediately
available on boot or disconnected at random then you may want the `deluged`
service to wait for mount point to be ready before starting. If they are
unmounted or disconnected then `deluged` is stopped. When they become available
again `deluged` is started.

Ensure you have added the correct drive details to `fstab` or equivalent so
they are mounted at boot.

List the available drive mounts:

```console
sudo systemctl -t mount
```

Look for your mount point in the `Description` column. Mounts are formatted
similar to the mount point with `-`s replacing `/`s in the path.
e.g.: `media-xyz.mount`

Modify the `[Unit]` section of the `deluged.service` script by adding the
details below, substituting `xyz.mount` for the mount you want the service
to depend on:

```ini
[Unit]
Description=Deluge Bittorrent Client Daemon
# Start after network and specified mounts are available.
After=network-online.target xyz.mount
Requires=xyz.mount
# Stops deluged if mount points disconnect
BindsTo=xyz.mount
```

For multiple mount points add a space between additional entries. e.g.:

```init
After=network-online.target xyz.mount abc.mount def.mount
```

Modify the `[Install]` section to ensure the deluged service is started when
the mount point comes back online:

```ini
[Install]
WantedBy=multi-user.target xyz.mount
```

Reference: [systemd.unit](https://www.freedesktop.org/software/systemd/man/systemd.unit.html#RequiresMountsFor=)
