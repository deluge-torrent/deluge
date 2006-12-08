# 
# Copyright (c) 2006 Alon Zakai ('Kripken') <kripkensteiner@gmail.com>
#
# 2006-15-9
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#

import sys
command = sys.argv[1]

removals = ['-g', '-DNDEBUG', '-O2', '-Wstrict-prototypes']
addition = "-DNDEBUG -O2" # Oddly, -O2 gives smaller .o's than -Os

import platform

pythonVersion = platform.python_version()[0:3]

print "====================================="
print "Creating flood_core for Python " + pythonVersion
print "====================================="

import os

p = os.popen("python setup_naive.py --dry-run " + command)
data = p.readlines()
p.close()

print "Executing modified commands: "
for line in data:
	if line[0:3] in ['gcc', 'g++']:
#		print "OLD: ", line
		for removal in removals:
			line = line.replace(" " + removal + " ", " ")
		line = line[0:4] + addition + " " + line[4:]
		print line

		p = os.popen(line)
		data = p.readlines()
		p.close()

		print ""
#	else:
#		print "NOT DOING: ", line

# Now redo it, for real. Nothing should occur, except for installation, if requested
print "Finalizing..."

p = os.popen("python setup_naive.py " + command)
data = p.readlines()
p.close()

#print "".join(data) # Errors from the pipe are shown before we print... not good
