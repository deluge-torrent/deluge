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

