
import os
from subprocess import call
import time
import atexit
from config import config

def umount_all(base):
	f = open("/proc/mounts", "r")
	mps=[]
	for line in f:
		mp=line.split()[1]
		if mp.startswith(base) and mp != base:
			mps.append(mp)
	ok = True
	for mp in mps:
		cnt=5
		print "UMOUNT:", mp
		while call(["umount", mp]) != 0 and cnt != 0:
			time.sleep(0.25)
			cnt-=1

		if cnt==0:
			ok=False
			print "COULD NOT UNMOUNT"
	return ok

class Fs:
	SYS=("/sys", "/proc", "/dev")
	def __init__(self, host):
		self._host = host
	
	def mount_system(self):
		for mp in self.SYS:
			if self.bound(mp):
				continue
			if not self.bind(mp):
				return False
		return True
	
	def umount_system(self):
		ok = True
		for mp in self.SYS:
			if not self.bound(mp):
				continue
			if not self.unbind(mp):
				ok = False
				self._host.warn("Failed to unmount " + mp)
		return ok

	def env(self):
		return {}

	def bound(self, mp):
		raise

	def bind(self, mp):
		raise

	def unbinfs(self, mp):
		raise

class FakeFs(Fs):
	_binds=[]
	def bind(self, mp):
		self._binds.append(mp)
		return True

	def unbind(self, mp):
		del self._binds[self._binds.index(mp)]
		return True

	def bound(self, mp):
		return mp in self._binds

	def env(self):
		return { "FAKECHROOT_EXCLUDE_PATH" : ":".join(self._binds) }

class RootFs(Fs):
	def __init__(self, host):
		self._host = host
		atexit.register(umount_all, config.sysroot())

	def bind(self, path):
		mp = config.sysroot(path)
		r = self._host.runner
		ret = r.run(["mount", "--bind", path, mp]) == 0
		return ret

	def unbind(self, path):
		mp = config.sysroot(path)
		r = self._host.runner
		return r.run(["umount", mp]) == 0

	def bound(self, path):
		mp = config.sysroot(path)
		f = open("/proc/mounts", "r")
		for line in f:
			if line.split()[1] == mp:
				return True
		return False

