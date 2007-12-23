from __future__ import with_statement
import os
import re
template_dirs = ['~/prj/WebUi/templates/deluge',
    '~/prj/WebUi/templates/advanced']

template_dirs  = [os.path.expanduser(template_dir ) for template_dir in template_dirs]


files = []
for template_dir in template_dirs:
    files += [os.path.join(template_dir,fname)
        for fname in os.listdir(template_dir)
        if fname.endswith('.html')]


all_strings = []
for filename in files:
    with open(filename,'r') as f:
        content = f.read()
        all_strings += re.findall("_\(\"(.*?)\"\)",content)
        all_strings += re.findall("_\(\'(.*?)\'\)",content)

all_strings = sorted(set(all_strings))

with open ('./template_strings.py','w') as f:
    for value in all_strings:
        f.write("_('%s')\n"  % value )

