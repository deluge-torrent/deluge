#!/bin/bash
for size in 16 22 24 32 36 48 64 72 96 128 192 256; do mkdir -p icons/hicolor/\
${size}x${size}/apps; rsvg-convert -w ${size} -h ${size} \
-o icons/hicolor/${size}x${size}/apps/deluge.png pixmaps/deluge.svg; mkdir -p \
icons/scalable/apps/; cp pixmaps/deluge.svg icons/scalable/apps/deluge.svg; done
