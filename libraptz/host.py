#!/usr/bin/python

import sys
import os
import select
from chroot import FakeRoot, ChRoot
from fs import FakeFs, RootFs
from raptzerror import RaptzException

from config import config

class Host():
	def __init__(self):
		pass

	def setup(self, umountall=False):
		if config.mode == "fake":
			self.runner = FakeRoot(self)
			self.fs = FakeFs(self)
		else:
			if os.getuid() != 0:
				raise RaptzException("You shall be root to run in root mode")
			self.runner = ChRoot(self)
			self.fs = RootFs(self, umountall)

	def start(self, name):
		print("*** " + name + " ***")
		return self


global host
host = Host()

