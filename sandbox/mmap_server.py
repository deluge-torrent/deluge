#!/usr/bin/env python2.4

fileob = open('xxx','w')
while True:
	data = raw_input('Enter some text:')
	fileob.seek(0)
	fileob.write(data)
	fileob.truncate()
	fileob.flush()