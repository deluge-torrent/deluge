#!/bin/bash
for size in 16 22 24 32 36 48 64 72 96 128 192 256; do mkdir -p deluge/ui/data/\
icons/hicolor/${size}x${size}/apps; rsvg-convert -w ${size} -h ${size} \
-o deluge/ui/data/icons/hicolor/${size}x${size}/apps/deluge.png deluge/ui/data/pixmaps\
/deluge.svg; mkdir -p deluge/ui/data/icons/scalable/apps/; cp deluge/ui/data/pixmaps/\
deluge.svg deluge/ui/data/icons/scalable/apps/deluge.svg; done
