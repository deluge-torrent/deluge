#!/usr/bin/env python

import os
import sys
import cPickle as pickle
if sys.version_info > (2, 6):
    import json
else:
    import simplejson as json

from deluge.common import get_default_config_dir

config_dir = get_default_config_dir()
files = []
for filename in os.listdir(config_dir):
    filename = os.path.join(config_dir, filename)
    if not os.path.isfile(filename):
        continue
    if filename.endswith(".log"):
        continue
    
    basename = os.path.basename(filename)
    sys.stdout.write("Converting %s..." % (basename) + ' '*(20-len(basename)))
    try:
        config = json.load(open(filename, "r"))
        pickle.dump(config, open(filename, "wb"))
        print "\033[032mdone\033[0m"
    except:
        try:
            pickle.load(open(filename, "rb"))
            print "\033[032malready converted\033[0m"
        except:
            print "\033[031mfailed\033[1;m"
