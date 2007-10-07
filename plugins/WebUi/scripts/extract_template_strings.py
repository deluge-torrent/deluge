from __future__ import with_statement
import os
import re
template_dir = '~/prj/WebUi/templates/deluge'
template_dir  = os.path.expanduser(template_dir )


files = [os.path.join(template_dir,fname)
    for fname in os.listdir(template_dir)
    if fname.endswith('.html')]

all_strings = []
for filename in files:
    with open(filename,'r') as f:
        content = f.read()
        all_strings += re.findall("\$\_\(\'(.*)\'\)",content)
        all_strings += re.findall("\$\_\(\"(.*)\"\)",content)

all_strings = sorted(set(all_strings))

with open ('./template_strings.py','w') as f:
    for value in all_strings:
        f.write("_('%s')\n"  % value )

