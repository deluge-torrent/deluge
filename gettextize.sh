#!/bin/sh
PACKAGE="Deluge"
PKG_VERSION=`grep "version\ =\ \"" setup.py | cut -d '"' -f2`
PO_DIR="deluge/i18n"
POTFILES_IN="infiles.list"
POT_FILE=deluge.pot 

cp $PO_DIR/POTFILES.in $POTFILES_IN
DESKTOP_FILE=`grep ".*desktop.in$" $POTFILES_IN`

if [ $DESKTOP_FILE ]; then
    sed -i "\:$DESKTOP_FILE:d" $POTFILES_IN
    intltool-extract --quiet --type=gettext/ini $DESKTOP_FILE
    echo "$DESKTOP_FILE.h" >> $POTFILES_IN
fi

xgettext --from-code=UTF-8 -kN_:1 -f $POTFILES_IN -o $PO_DIR/$POT_FILE --package-name=$PACKAGE \
    --copyright-holder='Deluge Team' --package-version=$PKG_VERSION \
    --msgid-bugs-address=http://deluge-torrent.org

# sub the YEAR in the copyright message
sed -i -e '2s/YEAR/'`date +%Y`'/' "$PO_DIR/$POT_FILE"

rm -f $POTFILES_IN
rm -f "$DESKTOP_FILE.h"
echo "Created $PO_DIR/$POT_FILE"
