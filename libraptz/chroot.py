#!/usr/bin/python

import sys
import os
import select
from subprocess import Popen, check_output, call

import shutil
class ChRoot:
	RCDFILE_CONTENT="""#!/bin/dash\nexit 101\n"""
	_qemusrc = "/usr/bin/qemu-arm-static"
	def __init__(self, host):
		self._host = host
		self._rcddst = host.conf.sysroot("/usr/sbin/policy-rc.d")
		self._qemudst = host.conf.sysroot(self._qemusrc)

	def run(self, cmds, env=None, stdoutfunc=None, stderrfunc=None, *kargs):
		stdout = self._host.stdoutfd()
		stderr = self._host.stderrfd()
		if stdout != 1 or stderr != 2:
			self._host.add_outcb(stdoutfunc, *kargs)
			self._host.add_errcb(stderrfunc, *kargs)
			self._host.text("$ " + " ".join(cmds))
			p = Popen(cmds, env=env,
				stdout=stdout, stderr=stderr)
			while p.poll() == None:
				self._host.poller.poll(.01)
			ret = p.wait()
			self._host.remove_outcb(stdoutfunc)
			self._host.remove_errcb(stderrfunc)
			return ret
		return call(cmds, env=env)

	def _ch_setup(self):
		shutil.copy(self._qemusrc, self._qemudst)
		open(self._rcddst, "w").write(self.RCDFILE_CONTENT)
		os.chmod(self._rcddst, 0755)

	def _ch_setdown(self):
		if os.path.isfile(self._rcddst):
			os.unlink(self._rcddst)
		if os.path.isfile(self._qemudst):
			os.unlink(self._qemudst)

	def chroot(self, cmds, env={}, stdoutfunc=None, stderrfunc=None, *kargs):
		self._ch_setup()
		ch = [ "chroot", self._host.conf.sysroot() ]
		cmds = ch + cmds
		oenv = os.environ
		oenv["HOME"]="/root"
		oenv["LANG"]="C"
		for e in env:
			oenv[e] = env[e]
		ret = self.run(cmds, oenv, stdoutfunc, stderrfunc, *kargs)
		self._ch_setdown()
		return ret


class FakeRoot(ChRoot):
	RCDFILE_CONTENT="""#!/bin/dash\nexit 101\n"""
	_qemusrc = "/usr/bin/qemu-arm-static"
	def __init__(self, host):
		ChRoot.__init__(self, host)

	def run(self, cmds, env={}, stdoutfunc=None, stderrfunc=None, *kargs):
		envfile = self._host.conf.sysroot("/lib/fake.env")
		fakecmd = [ "fakechroot", 
			"fakeroot", 
			"-s", envfile,
			"-i", envfile,
		]
		cmds = fakecmd + cmds
		env["FAKECHROOT_EXCLUDE_PATH"] = self._host.fs.binds()
		return ChRoot.run(self, cmds, env, stdoutfunc, stderrfunc, *kargs)
