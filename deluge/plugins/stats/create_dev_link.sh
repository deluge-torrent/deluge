#!/bin/bash
mkdir temp
export PYTHONPATH=./temp
python setup.py develop --install-dir ./temp
cp ./temp/Stats.egg-link ~/.config/deluge/plugins
rm -fr ./temp
