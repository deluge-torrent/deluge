#!/bin/bash
set -o errexit

APPDIR="./app/Deluge.app"
RSCDIR="${APPDIR}/Contents/Resources"
LIBDIR="${RSCDIR}/lib"
VERSION=$(cat ../../RELEASE-VERSION)
YEAR=$(date +'%Y')

function msg() { echo "==> $1"; }

echo "*** Packaging Deluge.app to $APPDIR..."

msg "Clearing app dir"
rm -fr $APPDIR

msg "Fixing permissions on file we will need to relocate"
if [ ! -z "${JHBUILD_PREFIX}" ]; then
    chmod 755 "${JHBUILD_PREFIX}/lib/"libpython*.dylib
    chmod 755 "${JHBUILD_PREFIX}/lib/"libssl*.dylib
    chmod 755 "${JHBUILD_PREFIX}/lib/"libcrypto*.dylib
fi

chmod 755 deluge deluge-web deluge-console deluged

msg "Create Info.plist for Deluge $version"
sed -e s/%VERSION%/$VERSION/ -e s/%YEAR%/$YEAR/ Info.plist.in > Info.plist

msg "Calling gtk-mac-bundler"
gtk-mac-bundler deluge.bundle

msg "Unzip site-packages and make python softlink without version number"
pushd ${LIBDIR} || exit 1
ln -sf python* python
cd python
unzip -nq site-packages.zip
rm site-packages.zip
popd

msg "Replacing deluge by its egg..."
rm -fr ${LIBDIR}/python/deluge
rsync -rpl $JHBUILD_PREFIX/lib/python2.7/site-packages/deluge-*.egg "${LIBDIR}/python/"

msg "Clean unnecessary files"
find $APPDIR -name "*.la" -exec rm -f {} \;  # Should not be packaged
find $APPDIR -name "*.pyo" -exec rm -f {} \; # Just duplicates
find $LIBDIR/python/deluge-*.egg -name "*.py" -exec rm -f {} \; # Remove source files, leaving compiled only.
rm -fr $LIBDIR/pygtk/2.0/*demo*

echo "*** Packaging done:`du -hs $APPDIR | cut -f 1`"
