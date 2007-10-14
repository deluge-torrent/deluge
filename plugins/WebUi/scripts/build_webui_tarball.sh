#!/bin/sh
cd ~/prj/WebUi
bzr revno > revno
bzr version-info > version
rm ~/prj/WebUi/WebUi.tgz
cd ~/prj
tar -zcvf ~/prj/WebUi/WebUi.tgz WebUi/ --exclude '.*' --exclude '*.pyc' --exclude '*.tgz' --exclude 'attic' --exclude 'xul' --exclude '*.sh' --exclude '*.*~'