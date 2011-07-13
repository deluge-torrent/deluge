#!/usr/bin/env python
import os
import re
import sys
# Paths to exclude
EXCLUSIONS = [
    "deluge/scripts",
    "deluge/i18n",
]

POTFILE_IN = "deluge/i18n/POTFILES.in"

pattern = "deluge\/plugins\/.*\/build"
compiled = re.compile(pattern)

sys.stdout.write("Creating " + POTFILE_IN + " ... ")
sys.stdout.flush()
to_translate = []
for (dirpath, dirnames, filenames) in os.walk("deluge"):
    for filename in filenames:
        if os.path.splitext(filename)[1] in (".py", ".glade", ".in") \
                                            and dirpath not in EXCLUSIONS \
                                            and not compiled.match(dirpath):
            to_translate.append(os.path.join(dirpath, filename))

f = open(POTFILE_IN, "wb")
for line in to_translate:
    f.write(line + "\n")

f.close()

print "Done"
