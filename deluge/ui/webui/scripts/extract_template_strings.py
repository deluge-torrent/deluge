#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Martijn Voncken 2008 <mvoncken@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, write to:
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
#

import os
import re
template_dirs = ['../templates/classic','../templates/white','../templates/ajax/static/js']

template_dirs  = [os.path.expanduser(template_dir ) for template_dir in template_dirs]


files = []
for template_dir in template_dirs:
    files += [os.path.join(template_dir,fname)
        for fname in os.listdir(template_dir)
        if fname.endswith('.html') or  fname.endswith('.js')]


all_strings = []
for filename in files:
    f = open(filename,'r')
    content = f.read()
    all_strings += re.findall("_\(\"(.*?)\"\)",content)
    all_strings += re.findall("_\(\'(.*?)\'\)",content)
    all_strings += re.findall("Deluge\.Strings\.get\(\'(.*?)\'\)",content)
    all_strings += re.findall("Deluge\.Strings\.get\(\'(.*?)\'\)",content)

all_strings = sorted(set(all_strings))

f = open ('./template_strings.py','w')
for value in all_strings:
    f.write("_('%s')\n"  % value )

