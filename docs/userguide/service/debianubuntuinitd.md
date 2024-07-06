# Ubuntu Init Script

---
**This page is for obsolete/unsupported Ubuntu distributions, see [systemd](/userguide/service/systemd) or [upstart](userguide/service/upstart) depending on your distribution.**

---

Based upon the script created [here](http://apocryph.org/2008/11/30/setting_deluge_headless_ubuntu_seedbox_windows_client/).

Put this in /etc/default/deluge-daemon and set DELUGED_USER to the user you which to run deluge as

```sh
# Configuration for /etc/init.d/deluge-daemon

# The init.d script will only run if this variable non-empty.
DELUGED_USER=""             # !!!CHANGE THIS!!!!

# Should we run at startup?
RUN_AT_STARTUP="YES"
```

This should be placed in /etc/init.d/deluge-daemon

```sh
#!/bin/sh
### BEGIN INIT INFO
# Provides:          deluge-daemon
# Required-Start:    $local_fs $remote_fs
# Required-Stop:     $local_fs $remote_fs
# Should-Start:      $network
# Should-Stop:       $network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Daemonized version of deluge and webui.
# Description:       Starts the deluge daemon with the user specified in
#                    /etc/default/deluge-daemon.
### END INIT INFO

# Author: Adolfo R. Brandes
# Updated by: Jean-Philippe "Orax" Roemer

PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
DESC="Deluge Daemon"
NAME1="deluged"
NAME2="deluge"
DAEMON1=/usr/bin/deluged
DAEMON1_ARGS="-d"             # Consult `man deluged` for more options
DAEMON2=/usr/bin/deluge-web
DAEMON2_ARGS=""               # Consult `man deluge-web` for more options
PIDFILE1=/var/run/$NAME1.pid
PIDFILE2=/var/run/$NAME2.pid
UMASK=022                     # Change this to 0 if running deluged as its own user
PKGNAME=deluge-daemon
SCRIPTNAME=/etc/init.d/$PKGNAME

# Exit if the package is not installed
[ -x "$DAEMON1" -a -x "$DAEMON2" ] || exit 0

# Read configuration variable file if it is present
[ -r /etc/default/$PKGNAME ] && . /etc/default/$PKGNAME

# Load the VERBOSE setting and other rcS variables
[ -f /etc/default/rcS ] && . /etc/default/rcS

# Define LSB log_* functions.
# Depend on lsb-base (>= 3.0-6) to ensure that this file is present.
. /lib/lsb/init-functions

if [ -z "$RUN_AT_STARTUP" -o "$RUN_AT_STARTUP" != "YES" ]
then
   log_warning_msg "Not starting $PKGNAME, edit /etc/default/$PKGNAME to start it."
   exit 0
fi

if [ -z "$DELUGED_USER" ]
then
    log_warning_msg "Not starting $PKGNAME, DELUGED_USER not set in /etc/default/$PKGNAME."
    exit 0
fi

#
# Function to verify if a pid is alive
#
is_alive()
{
   pid=`cat $1` > /dev/null 2>&1
   kill -0 $pid > /dev/null 2>&1
   return $?
}

#
# Function that starts the daemon/service
#
do_start()
{
   # Return
   #   0 if daemon has been started
   #   1 if daemon was already running
   #   2 if daemon could not be started

   is_alive $PIDFILE1
   RETVAL1="$?"

   if [ $RETVAL1 != 0 ]; then
       rm -f $PIDFILE1
       start-stop-daemon --start --background --quiet --pidfile $PIDFILE1 --make-pidfile \
       --exec $DAEMON1 --chuid $DELUGED_USER --user $DELUGED_USER --umask $UMASK -- $DAEMON1_ARGS
       RETVAL1="$?"
   else
       is_alive $PIDFILE2
       RETVAL2="$?"
       [ "$RETVAL2" = "0" -a "$RETVAL1" = "0" ] && return 1
   fi

   is_alive $PIDFILE2
   RETVAL2="$?"

   if [ $RETVAL2 != 0 ]; then
        sleep 2
        rm -f $PIDFILE2
        start-stop-daemon --start --background --quiet --pidfile $PIDFILE2 --make-pidfile \
        --exec $DAEMON2 --chuid $DELUGED_USER --user $DELUGED_USER --umask $UMASK -- $DAEMON2_ARGS
        RETVAL2="$?"
   fi
   [ "$RETVAL1" = "0" -a "$RETVAL2" = "0" ] || return 2
}

#
# Function that stops the daemon/service
#
do_stop()
{
   # Return
   #   0 if daemon has been stopped
   #   1 if daemon was already stopped
   #   2 if daemon could not be stopped
   #   other if a failure occurred

   start-stop-daemon --stop --quiet --retry=TERM/30/KILL/5 --user $DELUGED_USER --pidfile $PIDFILE2
   RETVAL2="$?"
   start-stop-daemon --stop --quiet --retry=TERM/30/KILL/5 --user $DELUGED_USER --pidfile $PIDFILE1
   RETVAL1="$?"
   [ "$RETVAL1" = "2" -o "$RETVAL2" = "2" ] && return 2

   rm -f $PIDFILE1 $PIDFILE2

   [ "$RETVAL1" = "0" -a "$RETVAL2" = "0" ] && return 0 || return 1
}

case "$1" in
  start)
   [ "$VERBOSE" != no ] && log_daemon_msg "Starting $DESC" "$NAME1"
   do_start
   case "$?" in
      0|1) [ "$VERBOSE" != no ] && log_end_msg 0 ;;
      2) [ "$VERBOSE" != no ] && log_end_msg 1 ;;
   esac
   ;;
  stop)
   [ "$VERBOSE" != no ] && log_daemon_msg "Stopping $DESC" "$NAME1"
   do_stop
   case "$?" in
      0|1) [ "$VERBOSE" != no ] && log_end_msg 0 ;;
      2) [ "$VERBOSE" != no ] && log_end_msg 1 ;;
   esac
   ;;
  restart|force-reload)
   log_daemon_msg "Restarting $DESC" "$NAME1"
   do_stop
   case "$?" in
     0|1)
      do_start
      case "$?" in
         0) log_end_msg 0 ;;
         1) log_end_msg 1 ;; # Old process is still running
         *) log_end_msg 1 ;; # Failed to start
      esac
      ;;
     *)
        # Failed to stop
      log_end_msg 1
      ;;
   esac
   ;;
  *)
   echo "Usage: $SCRIPTNAME {start|stop|restart|force-reload}" >&2
   exit 3
   ;;
esac

:

```

Make the script executable by root

```sh
sudo chmod 755 /etc/init.d/deluge-daemon
```

Run this script on start up

```sh
sudo update-rc.d deluge-daemon defaults
```

Start the daemon

```sh
sudo invoke-rc.d deluge-daemon start
```

## Make deluge log something
Create a structure for deluge to log to:

```
sudo mkdir -p /var/log/deluge/daemon
sudo mkdir /var/log/deluge/web
```
Give the user that deluge is running as (in this case deluge) write-access to the logs

```
sudo chmod -R 755 /var/log/deluge
sudo chown -R deluge /var/log/deluge
```
Edit the init-script like so:

```sh
DAEMON1=/usr/bin/deluged
DAEMON1_ARGS="-d -L warning -l /var/log/deluge/daemon/warning.log"             # Consult `man deluged` for more options
DAEMON2=/usr/bin/deluge-web
DAEMON2_ARGS="-L warning -l /var/log/deluge/web/warning.log"
```
* See [Logging](/faq#enabledelugelogging) for possible loglevels.
Restart the daemon

```
sudo invoke-rc.d deluge-daemon restart
```
Tell logrotate to rotate the logs

```
sudo cat > /etc/logrotate.d/deluge << EOF
/var/log/deluge/*/*.log {
        weekly
        missingok
        rotate 7
        compress
        notifempty
        copytruncate
        create 600
}
EOF

```