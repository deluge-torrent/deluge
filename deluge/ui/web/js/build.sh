DELUGE_FILES="rpc.js deluge.js deluge-login.js deluge-menus.js deluge-bars.js deluge-connections.js deluge-torrents.js deluge-details.js deluge-add.js deluge-preferences.js deluge-ui.js"
ALL_FILES="ext-extensions-debug.js $DELUGE_FILES"

scan() {
    cat /dev/null > .build_data.tmp
    for FILE in $ALL_FILES; do
        md5sum $FILE >> .build_data.tmp
    done;
}

check_file() {
    # No build data is stored so return 1 since we can't make any guesses.
    [ ! -e .build_data ] && return 1;

    FILE=$1
    LAST_BUILD=`grep $FILE .build_data`
    if [ $? == 1 ]; then return 1; fi;

    CURRENT=`grep $FILE .build_data.tmp`

    [ "$CURRENT" != "$LAST_BUILD" ] && return 1

    return 0;
}

build_deluge() {
    NEEDS_BUILD=false;
    for FILE in $DELUGE_FILES; do
        check_file $FILE
        [ $? == 1 ] && NEEDS_BUILD=true
    done;

    [ $NEEDS_BUILD == false ] && return 0

    echo "Building deluge-yc.js"
    cat $DELUGE_FILES > deluge-yc.js.tmp
    yuicompressor --type=js -o "deluge-yc.js" "deluge-yc.js.tmp" && rm "deluge-yc.js.tmp"
}

build_ext() {
    check_file "ext-extensions-debug.js"
    if [ $? == 1 ]; then
        echo "Building ext-extensions.js"
        yuicompressor --type=js -o "ext-extensions.js" "ext-extensions-debug.js"
    fi;
}

scan
build_ext
build_deluge

mv .build_data.tmp .build_data
