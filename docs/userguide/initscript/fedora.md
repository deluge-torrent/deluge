**For Fedora version > 15 use: [UserGuide/Service/systemd](/userguide-service/systemd)**

# Fedora Init Script

```sh
#!/bin/bash
# chkconfig: 345 85 15
# description: deluged is the Deulge bit torrent daemon,
# it performs downloads and manages torrents.
# Connect to the service through the configured port.
# Script to manage start and stopping the fedora service
# processname: deluged

    # Source function library.
    . /etc/init.d/functions

    RETVAL=0;

    start() {
        echo "Starting deluged service"
        daemon --user=deluge deluged -c /storage/fileshare/Torrents/.deluge/ -p 58846 -l /storage/fileshare/Torrents/.deluge/deluged.log
        RETVAL1=$?
        echo
        [ $RETVAL1 = 0 ] && touch /var/lock/subsys/deluged

        echo "Starting deluge webui"
        #daemon --user=deluge deluge -u web -c /storage/fileshare/Torrents/.deluge/ -l /storage/fileshare/Torrents/.deluge/deluge-web.log
        #deluge -u web -c /storage/fileshare/Torrents/.deluge/ -q &
        #cant find force background option in daemon function, so I add my own &
        runuser -s /bin/bash - deluge -c "ulimit -S -c ${DAEMON_COREFILE_LIMIT:-0} >/dev/null 2>&1 ; deluge -u web -c /storage/fileshare/Torrents/.deluge/ -l /storage/fileshare/Torrents/.deluge/deluge-web.log &"
        [ "$?" -eq 0 ] && success $"$base startup" || failure $"$base startup"

        RETVAL2=$?
        echo
        [ $RETVAL2 = 0 ] && touch /var/lock/subsys/deluge-web

        RETVAL=1
        if [ $RETVAL1 == 0 ]; then
            if [ $RETVAL2 == 0 ]; then
                RETVAL=0
            fi
        fi
        return $RETVAL
    }

    stop() {
        echo "Stopping deluge webui"
        killproc deluge
        RETVAL1=$?
        echo
        [ $RETVAL1 = 0 ] && rm -f /var/lock/subsys/deluge-web

        echo "Stopping deluged service"
        killproc deluged
        RETVAL2=$?
        echo
        [ $RETVAL2 = 0 ] && rm -f /var/lock/subsys/deluged
    }

    restart() {
        stop
        start
    }

case $1 in
    start)
        start
    ;;
    stop)
        stop
    ;;
    restart)
        restart
    ;;
    status)
        status deluged
        status deluge
        RETVAL=$?
    ;;
    *)
    echo $"Usage: $0 {start|stop|restart|status}"
    exit 1
esac

    exit $RETVAL
```

