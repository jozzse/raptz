#!/usr/bin/python

import sys
import os
import select
from subprocess import Popen

class CbPoller:
	def __init__(self):
		self.poller = select.poll()
		self.cb = {}

	def add(self, rfile, func, *kargs):
		fd = -1
		if isinstance(rfile, file):
			fd = rfile.fileno()
		else:
			fd = rfile
		self.cb[fd] = (rfile, func, kargs)
		self.poller.register(fd, select.POLLIN | select.POLLERR | select.POLLHUP)

	def remove(self, rfile):
		fd = -1
		if isinstance(rfile, file):
			fd = rfile.fileno()
		else:
			fd = rfile
		if fd == -1:
			return
		self.poller.unregister(fd)
		del self.cb[fd]

	def poll(self, timeout):
		while True:
			res = self.poller.poll(int(timeout * 1000))
			if res == None:
				return -1
			if res == []:
				return 0
			for fd, ev in res:
				cb = self.cb[fd]
				if not cb[1](cb[0], ev, *cb[2]):
					self.remove(fd)
		return len(res)

	def close(self):
		while len(self.cb):
			fd = self.cb.keys()[0]
			cb = self.cb[fd]
			cb[1](cb[0], select.POLLHUP, *cb[2])
			self.poller.unregister(fd)
			del self.cb[fd]
