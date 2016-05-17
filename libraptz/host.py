#!/usr/bin/python

import sys
import os
import select
from cbpoller import CbPoller
from chroot import FakeRoot, ChRoot
from fs import FakeFs, RootFs
from raptzerror import RaptzException

from config import config

class Host():
	_stdoutfd = sys.stdout.fileno()
	_stderrfd = sys.stderr.fileno()
	_outcb = {}
	_errcb = {}
	_outline = ""
	_errline = ""
	poller = CbPoller()
	def __init__(self):
		pass

	def setup(self, umountall=False):
		self._log = open(config.logfile, "w")

		if config.mode == "fake":
			self.runner = FakeRoot(self)
			self.fs = FakeFs(self)
		else:
			if os.getuid() != 0:
				raise RaptzException("You shall be root to run in root mode")
			self.runner = ChRoot(self)
			self.fs = RootFs(self, umountall)

	def redirout(self):
		pin, self._stdoutfd = os.pipe()
		self.poller.add(pin, self._stdout)
		pin, self._stderrfd = os.pipe()
		self.poller.add(pin, self._stderr)

	def add_outcb(self, cb, *kargs):
		if cb:
			self._outcb[cb] = kargs	
	def add_errcb(self, cb, *kargs):
		if cb:
			self._errcb[cb] = kargs

	def remove_outcb(self, cb):
		if cb and cb in self._outcb:
			del self._outcb[cb]

	def remove_errcb(self, cb):
		if cb and cb in self._errcb:
			del self._errcb[cb]

	def start(self, name):
		print("*** " + name + " ***")
		return self


global host
host = Host()

