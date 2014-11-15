#!/usr/bin/python

import os
import tempfile
import shutil
from raptzerror import RaptzException


class Configure:
	def __init__(self, host):
		self._host = host

	def clean(self):
		if os.path.isdir(self._host.conf.sysroot()):
			shutil.rmtree(self._host.conf.sysroot())

	def debconf(self):
		c = self._host.runner
		conf = self._host.conf
		debconfsrc=conf.confpath("debconf.cfg")
		if os.path.isfile(conf.confpath("debconf.cfg")):
			debconfdst=conf.sysroot("/tmp/debconf.cfg")
			shutil.copy2(debconfsrc, debconfdst)
			if c.chroot(["debconf-set-selections", "-v", "/tmp/debconf.cfg"]):
				raise RaptzException("Debconf failed")
			os.unlink(debconfdst)

	def copyroot(self):
		conf = self._host.conf
		self.copy2sysroot(conf.confpath("root"))

	def copy2sysroot(self, src, dst="/"):
		conf = self._host.conf
		for srcroot, dirs, files in os.walk(src):
			dstroot = conf.sysroot(dst + srcroot[len(src):])
			for d in dirs:
				dstd = os.path.join(dstroot, d)
				if not os.path.isdir(dstd):
					os.mkdir(dstd)
			for f in files:
				srcf = os.path.join(srcroot, f)
				dstf = os.path.join(dstroot, f)
				self._host.text(" ".join(["cp ", srcf, dstf]))
				shutil.copy2(srcf, dstf)

	def configure(self):
		conf = self._host.conf
		cfgroot = conf.confpath("conf")
		srcroot, dirs, files = os.walk(cfgroot).next()
		ch = self._host.runner
		i = 0
		for d in dirs:
			src = os.path.join(srcroot, d)
			dst = tempfile.mkdtemp(dir=conf.sysroot("/tmp"))

			dstinit = conf.rmsysroot(os.path.join(dst, "init.sh"))
			dstarg = conf.rmsysroot(dst)
			self.copy2sysroot(src, dstarg)
			ret = ch.chroot([dstinit, dstarg],
				stdoutfunc=self._stdout,
				stderrfunc=self._stdout)

			# Run dev scripts if avalible
			dstinit = conf.rmsysroot(os.path.join(dst, "init.dev.sh"))
			if conf.args.dev and os.path.isdir(conf.sysroot(dstinit)):
				dstarg = conf.rmsysroot(dst)
				ret = ch.chroot([dstinit, dstarg],
					stdoutfunc=self._stdout,
					stderrfunc=self._stdout)

			shutil.rmtree(dst)
			if ret != 0:
				raise RaptzException("Configure " + d + " failed")
			i+=1

	def _stdout(self, line):
		self._host.text(line)
		return True

