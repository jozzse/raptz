
import os
from subprocess import call
import time
import atexit

def umount_all(base):
	f = open("/proc/mounts", "r")
	mps=[]
	for line in f:
		mp=line.split()[1]
		if mp.startswith(base):
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

class Mount:
	SYS=("/sys", "/proc", "/dev")
	TMP=("/var/cache/apt",)
	def __init__(self, host):
		self._host = host
		atexit.register(umount_all, self._host.conf().sysroot())

	def mount_system(self):
		for mp in self.SYS:
			if not self.bind(mp):
				return False
		return True

	def mount_tmp(self):
		for mp in self.TMP:
			if not self.tmpmount(mp, True):
				return False
		return True

	def umount_system(self):
		ok = True
		for mp in self.SYS:
			if not self.unbind(mp):
				ok = False
				print "Failed to unmount ", mp
		return ok

	def umount_tmp(self):
		ok = True
		for mp in self.TMP:
			if not self.tmpumount(mp):
				ok = False
				print "Failed to unmount ", mp
		return ok


	def mounted(self, mp):
		f = open("/proc/mounts", "r")
		for line in f:
			if line.split()[1] == mp:
				return True
		return False

	def tmpmount(self, path, mkdir=False):
		mp = self._host.conf().sysroot(path)
		if self.mounted(mp):
			return True
		if not os.path.isdir(mp) and mkdir:
			os.makedirs(mp, 0777)
		r = self._host.runner
		return r.run(["mount", "-t", "tmpfs", "none", mp]) == 0

	def tmpumount(self, path):
		return self.unbind(path)

	def bind(self, path, mp=None):
		if mp == None:
			mp = self._host.conf().sysroot(path)
		if self.mounted(mp):
			return True
		r = self._host.runner
		return r.run(["mount", "--bind", path, mp]) == 0

	def unbind(self, path):
		mp = self._host.conf().sysroot(path)
		if not self.mounted(mp):
			return True
		r = self._host.runner
		return r.run(["umount", mp]) == 0
