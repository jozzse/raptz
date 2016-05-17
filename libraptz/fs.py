
import os
from subprocess import call
import time
import atexit
import progs
from config import config
import stat
from stat import S_IFCHR, S_IFBLK

NODES = (
	( "mem",     0o640, S_IFCHR, 1, 1 ),
	( "kmem",    0o640, S_IFBLK, 1, 2 ),
	( "null",    0o666, S_IFCHR, 1, 3 ),
	( "port",    0o640, S_IFCHR, 1, 4 ),
	( "zero",    0o666, S_IFCHR, 1, 5 ),
	( "full",    0o666, S_IFCHR, 1, 7 ),
	( "random",  0o666, S_IFCHR, 1, 8 ),
	( "urandom", 0o666, S_IFCHR, 1, 9 ),
	( "tty",     0o666, S_IFCHR, 5, 0 ),
	( "console", 0o622, S_IFCHR, 5, 1 ),
	( "ptmx",    0o666, S_IFCHR, 5, 2 ),
	( "ram",     0o660, S_IFBLK, 1, 0 ),
	( "loop",    0o660, S_IFBLK, 7, 0 ),
)

LNS = (
    ( "/proc/self/fd", "/dev/fd" ),
    ( "/proc/self/fd/0", "/dev/stdin" ),
    ( "/proc/self/fd/1", "/dev/stdout" ),
    ( "/proc/self/fd/2", "/dev/stderr" ),
    ( "/proc/kcore", "/dev/core" ),
)


def umount_all(unmountall, base, fs):
	if not unmountall:
		fs.umount_system()
		return True
	# Unmount all in base
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
	SYS=("/sys", "/proc", "/dev/pts", "/dev/shm")
	def __init__(self, host):
		self._host = host

	def mknod(self, name, mode, type, maj, min):
		raise

	def symlink(self, src, dst): 
		dst = config.rootfs(dst)
		if not os.path.exists(dst):
			os.symlink(src, dst)

	def mount_system(self):
		for mp in self.SYS:
			if self.bound(mp):
				continue
			if not self.bind(mp):
				return False
		[ self.mknod(*node) for node in NODES ]
		[ self.symlink(*ln) for ln in LNS ]
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
	def binds(self):
		return self._binds

	def mknod(self, name, mode, type, maj, min):
		path = config.rootfs("/dev/"+name)
		cmd = [ "mknod", "-m", "%o" % mode, path ]
		if type == S_IFCHR:
			cmd.append("c")
		else:
			cmd.append("b")
		cmd.append(str(maj))
		cmd.append(str(min))
		r = self._host.runner
		r.run(cmd)

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
	def __init__(self, host, unmountall):
		Fs.__init__(self, host)
		progs.register("mount");
		progs.register("umount");
		atexit.register(umount_all, unmountall, config.rootfs(), self)
	
	def mknod(self, name, mode, type, maj, min):
		path = config.rootfs("/dev/"+name)
		if os.path.exists(path):
			os.chmod(path, mode)
		else:
			os.mknod(path, mode | type, os.makedev(maj, min))

	def bind(self, path):
		mp = config.rootfs(path)
		if not os.path.isdir(mp):
			os.mkdir(mp)
		r = self._host.runner
		ret = r.run(["mount", "--bind", path, mp]) == 0
		return ret

	def unbind(self, path):
		mp = config.rootfs(path)
		r = self._host.runner
		return r.run(["umount", mp]) == 0

	def bound(self, path):
		mp = config.rootfs(path)
		f = open("/proc/mounts", "r")
		for line in f:
			if line.split()[1] == mp:
				return True
		return False

