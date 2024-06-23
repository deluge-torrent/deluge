# Thin Client

Deluge can be setup in such a way that a Deluge daemon, `deluged`, can be setup on a central computer, `server`, which can then be accessed and controlled by other computers, `clients`, using one of Deluge's UIs.

* Both the Deluge client and daemon need to be the same major versions, i.e. both `1.2.x` or both `1.3.x`.

## Deluge Daemon Setup

The Deluge daemon `deluged` and `deluge-console` should be [installed](/installing) on the server.

See the [UserGuide/Service service guides] to run `deluged` as a service so that it starts/stops on server boot/shutdown. Substitute any daemon start or stop commands below with the appropriate service commands.

To debug any problems setting up `deluged` [enable logging](/faq#howdoistartthedaemonwithloggingenabled) and check for errors.

### Create Default Config

To create the config directory and populate with the default files, run and then stop `deluged`. *(If using a service substitute appropriate operating system commands)*:

```sh
deluged
killall deluged
```

*Note: The config location is either the [default location](/faq#wheredoesdelugestoreitssettingsconfig) with reference to the `user` that `deluged` is running as. Alternatively if using a service it will be specified in the service config files with `-c <path>` option.*

### Add User to the authentication file

Create a Deluge user for clients/UIs to access the daemon by editing the authentication file, `auth`, located in the above config location.

The `auth` file should consist of lines of `<username>:<password>:<level>`. Replace <username> and <password> with your choice and <level> with the desired [UserGuide/Authentication authentication level].

You can use your favourite text editor to achieve this or can be done with a one-line echo command e.g.:

```sh
echo "alice:MyC0mpL3xPass:10" >> ~/.config/deluge/auth
```

### Enable Remote Connection

We will use `deluge-console` to configure `deluged` to accept connections from computers other than `localhost`. For `SSH Tunnelling` you do not need to enable remote connections so this step can be skipped.

Using the Console in command-line mode, set the `allow_remote` option and then verify with these commands:

```sh
deluge-console "config -s allow_remote True"
deluge-console "config allow_remote"
```

If you are running `deluged` under another user (e.g. `deluge`) you will need to temporarily login as that user to enable deluge-console to access that daemon's config:

```sh
su --shell /bin/bash --login deluge
```

Alternatively you can edit `core.conf` (`deluged` must not be running) in the config and change `allow_remote` from `false` to `true`.

### Start Deluge Daemon

```
deluged
```

### Verify Server IP Address

You will need to know the server's IP address for configuring clients, for private IP: `hostname -I` or public IP: `curl ifconfig.me`

Congratulations! The server is now setup for remote client access.

---

## Client Setup

### Accessing deluged service with local UI Client
When attempting to access a daemon `deluged` on the same machine but running as a different user e.g. your login user is `user` and `deluged` is running as `deluge`, you may be unable access to `deluged`. This is due to the client automatically authorising using the localhost line in the auth file, which is assumed to be at the same config location as `deluged`.

The workaround is to replace the `localclient` line in your user config auth file (`~/.config/deluge/auth`) with the `localclient` line from the `deluged` config `auth` file e.g. `/var/lib/deluge/auth`.

### GTK UI

The Deluge GTK UI setup require switching the GTK UI from Classic mode to Thin-client mode, then adding and connecting to the remote daemon on the server.

1. In `Preferences -> Interface` and disable (untick) `Classic Mode`
2. Restart `deluge` and you should see the `Connection Manager`.
   * If it is not needed you can remove the `localhost` daemon.
   * If SSH Tunnelling, before continuing [UserGuide/ThinClient#CreateSSHTunnel Create SSH Tunnel], and for `Hostname`, below, `127.0.0.2` *must* be used.
3. Create a new entry with `Add` button:
   * `Hostname` is your server's IP.
   * `Port` should be default `58846`.
   * `Username` and `Password` are those added to the `deluged` config `auth` file.

If this was successful a green tick should now appear as the status for the daemon you just added.

Click on `Connect` and the Connection Manager should disappear.

*Optional step:* Expand `Options` and select '`Automatically connect to selected host on startup`' and '`Do not show this dialog on start-up`'.



Congratulations! You can now access the Deluge daemon, `deluged`, on the server via the GTK UI.


### Console

If accessing a local `deluged` daemon run the following and it will connect automatically:

```
deluge-console
```

To connect to a remote daemon use the `connect` command in deluge-console:

```
connect <host>[:<port>] <user> <password>
```
or from the terminal:

```
deluge-console "connect <host>[:<port>] <user> <password>"
```
For adding torrents directly to the daemon through automatic methods such as with autodl-irssi:

```
deluge-console "connect <host>[:<port>] <user> <password> ; add $(TorrentPathName) ; exit"
```


### Web UI

The Web UI is slightly different as the `client` is a web server daemon `deluge-web` that connects to a running `deluged`.

1. [Install ](/installing) `deluge-web` and run it:

```sh
deluge-web
```
   Note: To run it in the background as a daemon, use `--fork` option. You may also want to set it up as a [UserGuide/InitScript service].

In your web browser, enter the url below where <server> is the IP address of the server:

```
http://<server>:8112
```

* Default password is: `deluge`

Congratulations! You can now access deluge on the server via the Web UI.

---

## Create SSH Tunnel

From Deluge 1.2 onward, all communication between the GTK UI and daemon is encrypted using a automatically generated self-signed certificate so SSH tunneling is not a requirement if you are on a trusted local network. If you access the daemon over the internet, you should still use a SSH tunnel.

In a Terminal, enter the following, replacing `<server>` with the public IP of your server.

```sh
ssh -fNL 127.0.0.2:58846:localhost:58846 <server>
```
Note: We use `127.0.0.2` instead of `localhost` so that Deluge client knows that we are connecting to a remote daemon. Otherwise you will encounter problems with file browsing as it will assume to be on local client machine rather than remote server.

If you get the error '`bind: Can't assign requested address`', you need to add `127.0.0.2` as an alias for the loopback device:

```sh
sudo ifconfig lo0 add 127.0.0.2
```