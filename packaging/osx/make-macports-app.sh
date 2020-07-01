#!/bin/bash
set -o errexit

SOURCE="${BASH_SOURCE[0]}"
while [ -h "${SOURCE}" ]
    do # resolve $SOURCE until the file is no longer a symlink
        DIR="$( cd -P "$( dirname "${SOURCE}" )" && pwd )"
        SOURCE="$(readlink "${SOURCE}")"
        [[ "${SOURCE}" != /* ]] && SOURCE="${DIR}/${SOURCE}" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
    done
CURRDIR="$( cd -P "$( dirname "$SOURCE" )" && cd ../.. && pwd )"

if [ -z "${BUILDDIR}" ]; then
export BUILDDIR="${CURRDIR}/py2app-build/"
fi


APPDIR="./app/Deluge.app"
RSCDIR="${APPDIR}/Contents/Resources"
LIBDIR="${RSCDIR}/lib"
VERSION=$(cat ../../RELEASE-VERSION)
YEAR=$(date +'%Y')

export DELUGEDIR=$(cd ../../ && pwd)

echo "DELUGEDIR: ${DELUGEDIR}"

if [ -z "${PY2APP_PREFIX}" ]; then
export PY2APP_PREFIX="${BUILDDIR}/app/deluge.app/Contents/"
fi


function msg() { echo "==> $1"; }

echo "*** Packaging Deluge.app to $APPDIR..."

msg "Clearing build dir"
rm -fr $BUILDDIR

msg "Clearing app dir"
rm -fr $APPDIR

pushd ../../
python3 setup.py clean --all
find ./ \( -name '__pycache__' -or -name 'build' \) -type d -ls -depth -delete
msg "Running build"
msg "Creating app skeleton"
python3 setup.py py2app --verbose --dist-dir "${BUILDDIR}/app" --no-strip --graph --xref  --use-faulthandler --verbose-interpreter 
msg "Creating Wheel"
python3 setup.py bdist_wheel --dist-dir "${BUILDDIR}/wheel"
rm -fv "${BUILDDIR}/app/deluge.app/Contents/MacOS/deluge"
python3 setup.py install_scripts --install-dir "${BUILDDIR}/app/deluge.app/Contents/MacOS/"
popd

export PY2APP_PYTHON_VERSION=$("${PY2APP_PREFIX}/MacOS/python" --version | sed 's|Python ||' | cut -f 1,2 -d '.')

SITEPACKAGES="/opt/local/Library/Frameworks/Python.framework/Versions/${PY2APP_PYTHON_VERSION}/lib/python${PY2APP_PYTHON_VERSION}/site-packages"
    
msg "Create Info.plist for Deluge $version"
sed -e s/%VERSION%/$VERSION/ -e s/%YEAR%/$YEAR/ Info.plist.in > Info.plist

msg "Calling gtk-mac-bundler to create the skeleton"
gtk-mac-bundler deluge-macports.bundle

msg "Unzip site-packages and make python softlink without version number"
pushd ${LIBDIR} || exit 1
ln -sf "./python${PY2APP_PYTHON_VERSION}" "./python"
unzip -nq python*.zip -d "./python/"
rm python*.zip
popd

msg "Replacing deluge by its wheel..."
rm -fr "${LIBDIR}/python/deluge"
deluge_wheel="${BUILDDIR}/wheel/deluge*.whl"
unzip -nq ${deluge_wheel} -d "${LIBDIR}/python/"

msg "Will now try to fix dependencies manually because gtk-mac-bundler sucks at that"
msg "First, let's fix the Python executable."

install_name_tool -change "@executable_path/../Frameworks/Python.framework/Versions/${PY2APP_PYTHON_VERSION}/Python" "@rpath/libpython${PY2APP_PYTHON_VERSION}.dylib" "${APPDIR}/Contents/MacOS/python"

msg "Generating charset.alias..."

/opt/local/share/gettext/intl/config.charset $(uname -m)-apple-$(uname -s)-$(uname -r) > "${LIBDIR}/charset.alias"

msg "Getting list of files to fix..."

FILES=$(
  find "${APPDIR}" -type f \
   | xargs file \
   | grep ' Mach-O '|awk -F ':' '{print $1}'
)
OLDPATH='\/opt\/local\/lib\/libgcc\/|\/opt\/local\/lib\/|@executable_path\/..\/Frameworks\/'
msg "Replacing pathnames and @executable_path/../Frameworks/ with @rpath/..."

for file in $FILES
do
   set -x
   chmod 755 "${file}"
   install_name_tool -id "@rpath/$(basename ${file})" "${file}"
   ( install_name_tool -delete_rpath /opt/local/lib "${file}" 2>/dev/null || true)
   ( install_name_tool -delete_rpath @executable_path/../Frameworks "${file}" 2>/dev/null || true)
   ( install_name_tool -delete_rpath /opt/local/lib/libgcc "${file}" 2>/dev/null || true)
   { set +x; } 2>/dev/null
  otool -L "${file}" \
   | grep -E "\t${OLDPATH}" \
   | sed -E "s/${OLDPATH}//" \
   | awk -v fname="$file" -v old_path_1="/opt/local/lib/libgcc/" -v old_path_2="/opt/local/lib/" -v old_path_3="@executable_path/../Frameworks/" '{ \
   print "set -x\n\
   install_name_tool -change "old_path_1 $1" @rpath/"$1\
   " -change "old_path_2 $1" @rpath/"$1\
   " -change "old_path_3 $1" @rpath/"$1" "fname"\n\
   { set +x; } 2>/dev/null"\
   }' \
   | bash
   install_name_tool -add_rpath @executable_path/../Resources/lib "${file}"
done

msg "Copying distribution info for dependencies..."
# Ideally either py2app or gtk-mac-bundler would take care of this but I guess that's too much to ask.
# Maybe we can remove this eventually if they get their shit together.
cp -Rv "${SITEPACKAGES}"/zope.interface-*.egg-info \
    "${SITEPACKAGES}"/setproctitle-*.egg-info \
    "${SITEPACKAGES}"/six-*.egg-info \
    "${SITEPACKAGES}"/chardet*.egg-info \
    "${SITEPACKAGES}"/Mako*.egg-info \
    "${SITEPACKAGES}"/Pillow*.egg-info \
    "${SITEPACKAGES}"/pyxdg-*.egg-info \
    "${SITEPACKAGES}"/pycairo-*.egg-info \
    "${SITEPACKAGES}"/PyGObject-*.egg-info \
    "${SITEPACKAGES}"/pyOpenSSL-*.egg-info \
    "${SITEPACKAGES}"/rencode-*.egg-info \
    "${SITEPACKAGES}"/pyasn1-*.egg-info \
    "${SITEPACKAGES}"/pyasn1_modules-*.egg-info \
    "${SITEPACKAGES}"/pyasn1-*.egg-info \
    "${SITEPACKAGES}"/Twisted-*.egg-info \
    "${SITEPACKAGES}"/setuptools-*.egg-info \
    "${SITEPACKAGES}"/MarkupSafe-*.egg-info \
    "${SITEPACKAGES}"/cryptography-*.egg-info \
    "${SITEPACKAGES}"/idna-*.egg-info \
    "${SITEPACKAGES}"/service_identity-*.egg-info \
    "${SITEPACKAGES}"/attrs-*.egg-info \
    "${SITEPACKAGES}"/PyHamcrest-*.egg-info \
    "${SITEPACKAGES}"/hyperlink-*.egg-info \
    "${SITEPACKAGES}"/Automat-*.egg-info \
    "${SITEPACKAGES}"/incremental-*.egg-info \
    "${SITEPACKAGES}"/constantly-*.egg-info \
    "${SITEPACKAGES}"/asn1crypto-*.egg-info \
    "${SITEPACKAGES}"/pycparser-*.egg-info \
    "${SITEPACKAGES}"/cffi-*.egg-info \
    "${LIBDIR}/python${PY2APP_PYTHON_VERSION}/"

echo "*** Packaging done:$(du -hs ${APPDIR} | cut -f 1)"
