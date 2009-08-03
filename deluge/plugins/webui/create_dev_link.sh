#!/bin/bash
cd /home/damien/Projects/deluge/deluge/plugins/webui
mkdir temp
export PYTHONPATH=./temp
python setup.py build develop --install-dir ./temp
cp ./temp/WebUi.egg-link /home/damien/.config/deluge/plugins
rm -fr ./temp
