#!/usr/bin/python

import hashlib
import sys
import os
import select
from subprocess import Popen, check_output, call
from config import config
import progs

import shutil

QEMU_BIN="qemu-arm-static"

RESOLV_CONF_PATH="/etc/resolv.conf"

def hashfile(filename):
	if not os.path.exists(filename):
		return None
	ret = hashlib.md5()
	with open(filename, "r") as f:
		for line in f:
			ret.update(line)
	return ret.hexdigest()

class ChRoot:
	RCDFILE_CONTENT="""#!/bin/dash\nexit 101\n"""
	def __init__(self, host):
		self._host = host
		self._rcddst = config.rootfs("/usr/sbin/policy-rc.d")
		progs.register(QEMU_BIN)
		progs.register("chroot")
		self._qemudst = config.rootfs(progs.get(QEMU_BIN))

	def run(self, cmds, env={}, *kargs):
		renv = os.environ
		cmds[0] = progs.get(cmds[0])
		for key, value in env.items():
			renv[key] = value
		for key, value in self._host.fs.env().items():
			renv[key] = value
		
		return call(cmds, env=renv, stdout=config.stdout, stderr=config.stderr)

	def _ch_setup(self):
		shutil.copy(progs.get(QEMU_BIN), self._qemudst)
		open(self._rcddst, "w").write(self.RCDFILE_CONTENT)
		os.chmod(self._rcddst, 0755)
		# resolv.conf handling
		# If there is a resolv.conf move it to resolv.conf.real
		# Move host resolv.conf to target resolv.conf and store its md5 in self._resolvhash
		tconf=config.rootfs(RESOLV_CONF_PATH)
		if os.path.exists(tconf):
			os.rename(tconf, tconf+".real")
		shutil.copy(RESOLV_CONF_PATH, tconf)
		open(tconf, "a").write("""
# This is the Hosts resolv.conf.
# If changed in any way the target resolv.conf will not be restored.
""")
		self._resolvhash = hashfile(tconf)

	def _ch_teardown(self):
		# resolv.conf handling
		# Check that resolv.conf is a file and hash matches stored hash and is a file
		# if there is change. Leave as is and remove resolv.conf.real
		# if there is not change. Restore .real file if it exists
		tconf = config.rootfs(RESOLV_CONF_PATH)
		if not os.path.islink(tconf) and hashfile(tconf) == self._resolvhash:
			os.unlink(tconf)
			if os.path.exists(tconf+".real"):
				os.rename(tconf+".real", tconf)
		else:
			if os.path.exists(tconf+".real"):
				os.unlink(tconf + ".real")
		del self._resolvhash

		if os.path.isfile(self._rcddst):
			os.unlink(self._rcddst)
		if os.path.isfile(self._qemudst):
			os.unlink(self._qemudst)

	def chroot(self, cmds, env={}, stdoutfunc=None, stderrfunc=None, *kargs):
		self._ch_setup()
		ch = [ "chroot", config.rootfs() ]
		cmds = ch + cmds
		oenv = os.environ
		oenv["HOME"]="/root"
		oenv["LANG"]="C"
		for e in env:
			oenv[e] = env[e]
		ret = self.run(cmds, oenv, stdoutfunc, stderrfunc, *kargs)
		self._ch_teardown()
		return ret

class FakeRoot(ChRoot):
	RCDFILE_CONTENT="""#!/bin/dash\nexit 101\n"""
	_qemusrc = "/usr/bin/qemu-arm-static"
	def __init__(self, host):
		progs.register("fakechroot")
		progs.register("fakeroot")
		ChRoot.__init__(self, host)

	def run(self, cmds, env={}, stdoutfunc=None, stderrfunc=None, *kargs):
		envfile = config.rootfs("/lib/fake.env")
		fakecmd = [ "fakechroot",
			"fakeroot",
			"-s", envfile,
			"-i", envfile,
		]
			#"-c", "fcr",
		cmds = fakecmd + cmds
#		env["FAKECHROOT_EXCLUDE_PATH"] =	":".join(self._host.fs.binds())
		return ChRoot.run(self, cmds, env, stdoutfunc, stderrfunc, *kargs)

	def chroot(self, cmds, env={}, stdoutfunc=None, stderrfunc=None, *kargs):
		print(env)
		self.copy_ld()
		return ChRoot.chroot(self, cmds, env, stdoutfunc, stderrfunc, *kargs)

	def copy_ld(self):
		return
		libdir=config.rootfs("lib")
		ld = os.path.join(libdir, "ld-linux.so.3")
		lddst = os.path.join(libdir, os.readlink(ld))
		ldln = "/lib/ld-linux.so.3"
		try:
			ldsrc = os.readlink(ldln)
			if ldsrc == lddst:
				return True
		except:
			pass
		print "Change"
		cmd=["ln", "-sf", lddst, ldln]
		if os.getuid() != 0:
			print "SUDO"
			cmd = ["sudo"] + cmd
		return call(cmd, stdout=config.stdout, stderr=config.stderr) == 0

