echo "building deluge hang tight...."
echo off
cd C:\Deluge
python setup.py clean -a
python setup.py build
python setup.py install
cd win32
python deluge-bbfreeze.py
CD ..
"C:\Program Files (x86)\NSIS\makensis" deluge-win32-installer.nsi
echo "Build Complete! Installer in C:\Deluge\build-win32"