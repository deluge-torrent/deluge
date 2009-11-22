#!/bin/bash
cd /home/vampas/projects/DelugeNotify/deluge/plugins/notifications
mkdir temp
export PYTHONPATH=./temp
python setup.py build develop --install-dir ./temp
cp ./temp/Notifications.egg-link .config//plugins
rm -fr ./temp
