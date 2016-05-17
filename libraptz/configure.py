#!/usr/bin/python

import os
import tempfile
import shutil
from raptzerror import RaptzException
from config import config
from host import host

class Configure:
	def clean(self):
		if os.path.isdir(config.rootfs()):
			shutil.rmtree(config.rootfs())

	def setup(self):
		self.copy2rootfs(config.confpath("root"))
		debconfsrc=config.confpath("debconf.cfg")
		if os.path.isfile(config.confpath("debconf.cfg")):
			debconfdst=config.rootfs("/tmp/debconf.cfg")
			shutil.copy2(debconfsrc, debconfdst)
			if host.runner.chroot(["debconf-set-selections", "-v", "/tmp/debconf.cfg"]):
				raise RaptzException("Debconf failed")
			os.unlink(debconfdst)

	def copy2rootfs(self, src, dst="/"):
		for srcroot, dirs, files in os.walk(src):
			dstroot = config.rootfs(dst + srcroot[len(src):])
			for d in dirs:
				dstd = os.path.join(dstroot, d)
				if not os.path.isdir(dstd):
					os.mkdir(dstd)
			for f in files:
				srcf = os.path.join(srcroot, f)
				dstf = os.path.join(dstroot, f)
				host.text(" ".join(["cp ", srcf, dstf]))
				shutil.copy2(srcf, dstf)

	def configure(self):
		cfgroot = config.confpath("conf")
		srcroot, dirs, files = os.walk(cfgroot).next()
		ch = host.runner
		i = 0
		for d in dirs:
			src = os.path.join(srcroot, d)
			dst = tempfile.mkdtemp(dir=config.rootfs("/tmp"))

			dstinit = config.rmrootfs(os.path.join(dst, "init.sh"))
			dstarg = config.rmrootfs(dst)
			self.copy2rootfs(src, dstarg)
			ret = ch.chroot([dstinit, dstarg],
				stdoutfunc=self._stdout,
				stderrfunc=self._stdout)

			shutil.rmtree(dst)
			if ret != 0:
				raise RaptzException("Configure " + d + " failed")
			i+=1

	def _stdout(self, line):
		host.text(line)
		return True

