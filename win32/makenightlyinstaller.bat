echo "Starting...."
echo off
cd C:\Deluge
echo "Getting all Deluge source code"
git fetch --all
echo "Changing to development branch"
git checkout development
echo "Building deluge hang tight...."
python setup.py clean -a
python setup.py build
python setup.py install
echo "Building installer hang tight...."
cd win32
python deluge-bbfreeze.py
CD ..
"C:\Program Files (x86)\NSIS\makensis" deluge-win32-installer.nsi
echo "Build Complete! Installer in C:\Deluge\build-win32"