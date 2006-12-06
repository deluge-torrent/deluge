#!/usr/bin/env python2.4

import mmap, os, time
mx = mmap.mmap(os.open('xxx',os.O_RDWR), 1)
last = None
while True:
	mx.resize(mx.size())
	data = mx[:]
	if data != last:
		print data
		last = data
	time.sleep(1)