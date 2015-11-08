#!/usr/bin/python
import stat
import tempfile
import sys
import subprocess
import os
import shutil
from ConfigParser import SafeConfigParser

serr = os.open("/dev/null", os.O_WRONLY)
sout = serr
log = lambda txt: None

old_symlinks = False

def error(x):
	sys.stderr.write("ERROR: " + x + "\n")

unlink = lambda tmpf, dbgf: os.unlink(tmpf)

def debug_unlink(tmpfile, dbgfile):
	print "Store " + dbgfile
	return shutil.copy(tmpfile, dbgfile)

SECT_SIZE=512
class Parser(SafeConfigParser):
	def getdef(self, sect, name, default):
		if not self.has_option(sect, name):
			return default
		return self.get(sect, name)
	def getdict(self, sect):
		ret = {}
		for item in  self.items(sect):
			ret[item[0]] = item[1]
		return ret

def htos(hsize):
	if hsize.endswith("TB"):
		return int(hsize[:-2])*1024*1024*1024*1024
	elif hsize.endswith("GB"):
		return int(hsize[:-2])*1024*1024*1024
	elif hsize.endswith("MB"):
		return int(hsize[:-2])*1024*1024
	elif hsize.endswith("kB"):
		return int(hsize[:-2])*1024
	elif hsize.endswith("B"):
		return int(hsize[:-1])
	return int(hsize)*SECT_SIZE

def align(offset):
	if (offset % SECT_SIZE) == 0:
		return offset
	offset = offset + SECT_SIZE
	return offset - (offset % SECT_SIZE)

class Part():
	_device = -1
	_mountpoint = None
	_pass = "0"
	_dump = "0"
	_options = "defaults"
	_offset = -1
	_size = 0
	_image = None
	def __init__(self, name, info):
		self.name = name
		if "mountpoint" in info:
			self._mountpoint = info["mountpoint"]
		if "options" in info:
			self._options = info["options"]
		if "pass" in info:
			self._pass = info["pass"]
		if "dump" in info:
			self._dump = info["dump"]
		if "filesystem" in info:
			self._filesystem = info["filesystem"]
	def mk_image(self, baseimage, rootfs, populate):
		return True
	def get_image(self):
		return (self._offset, self._size, self._image)
	def get_sfdiskline(self):
		return None
	def get_fstabline(self, device):
		if not self._mountpoint:
			return None
		if self._device >= 0:
			dev = device + str(self._device)
		else:
			dev = "none"

		return " ".join([
			dev,
			self._mountpoint,
			self._filesystem,
			self._options,
			str(self._dump),
			str(self._pass)])

class Mount(Part):
	pass

class File(Part):
	def __init__(self, name, info):
		Part.__init__(self, name, info)
		self.source = info["source"]
		self._offset = htos(info["offset"])

	def mk_image(self, baseimage, rootfs, populate):
		source = self.source
		while source.startswith("/"):
			source = source[1:]
		self._image = os.path.join(rootfs, source)
		if not os.path.isfile(self._image):
			error("Could not find " + self.source + " in " + self._image)
			return False
		self._size = os.path.getsize(self._image)
		return True

class Partition(Part):
	fs2id = {
		"vfat" : "0C",
		"ext2" : "83",
		"ext3" : "83",
		"ext4" : "83"
	}
	_boot = False
	@staticmethod
	def factory(name, info):
		ret = None
		if info["filesystem"].startswith("ext"):
			ret = Ext(name, info)
		elif info["filesystem"] == "vfat":
			ret = VFat(name, info)
		else:
			ret = Partition(name, info)
		return ret
	def __init__(self, name, info):
		Part.__init__(self, name, info)
		if "offset" in info:
			self._offset = align(htos(info["offset"]))
		self._size = align(htos(info["size"]))
		self.fsid = self.fs2id[self._filesystem]
		if "bootable" in info:
			self._boot = bool(info["bootable"])
		self._device = int(info["device"])

	def mk_image(self, baseimage, rootfs, populate):
		self._image = baseimage + "." + self.name
		if os.path.isfile(self._image):
			os.unlink(self._image)
		fd = os.open(self._image, os.O_WRONLY | os.O_CREAT)
		os.ftruncate(fd, self._size)
		os.close(fd)
		if not self.mk_fs():
			return False
		if not populate:
			return True
		return self.pop_fs(rootfs)
	def mk_fs(self, args=[]):
		ret = subprocess.call(["/sbin/mkfs."+self._filesystem] + args + [self._image],
			stdout=sout, stderr=serr)
		return ret == 0
	def get_sfdiskline(self):
		ret = " " + self._image
		ret += ": start= " + str(self._offset/SECT_SIZE)
		ret += ", size= " + str(self._size/SECT_SIZE)
		ret += ", Id= " + self.fsid
		if self._boot:
			ret += ", bootable"
		return ret

class VFat(Partition):
	def pop_fs(self, rootfs):
		if not self._mountpoint:
			return True
		rootfs = os.path.join(rootfs, self._mountpoint[1:])
		slen = len(rootfs)
		root, dirs, files = os.walk(rootfs).next()
		srcs = []
		for f in dirs + files:
			srcs.append(os.path.join(root, f))
		ret = subprocess.call(["mcopy", "-D", "skip", "-b", "-s",
			"-i", self._image] + srcs + ["::/"],
			stdout=sout, stderr=serr)
		return ret == 0
class Ext(Partition):
	hardlinks = {}
	symlinks = []
	def pop_ext_path(self, rootfs, path, name):
		srcpath = os.path.join(path, name)
		st = os.lstat(srcpath)
		src = '"' + srcpath + '"'
		dst = '"' + name + '"'
		m = st.st_mode
		cmd = []
		if st.st_nlink > 1 and not stat.S_ISDIR(m):
			if st.st_ino in self.hardlinks:
				cmd.append(" ".join(["ln", self.hardlinks[st.st_ino], dst]))
				return cmd
			self.hardlinks[st.st_ino] = '"/' + srcpath[len(rootfs):] + '"'
		if stat.S_ISLNK(m):
			if old_symlinks:
				(fd, tmplink) = tempfile.mkstemp()
				os.write(fd, os.readlink(srcpath))
				os.close(fd)
				cmd.append(" ".join(["write", tmplink, dst]))
				self.symlinks.append(tmplink)
			else:
				return 'symlink '+dst+' "'+os.readlink(srcpath)+'"'
		elif stat.S_ISDIR(m):
			cmd.append("mkdir " + dst)
		elif stat.S_ISREG(m):
			cmd.append(" ".join(["write", src, dst]))
		elif stat.S_ISFIFO(m):
			return None
		elif stat.S_ISCHR(m):
			cmd.append(" ".join(["mknod", dst, "c",str(os.major(st.st_rdev)),
				str(os.minor(st.st_rdev))]))
		elif stat.S_ISBLK(m):
			cmd.append(" ".join(["mknod", dst, "b",str(os.major(st.st_rdev)),
				str(os.minor(st.st_rdev))]))
		else:
			raise "Unhandled filetype ", srcpath, st
		cmd.append("sif " + dst + " mode " + str(st.st_mode))
		cmd.append("sif " + dst + " links_count " + str(st.st_nlink))
		if st.st_uid != 0:
			cmd.append(" ".join(["sif", dst, "uid", str(st.st_uid)]))
		if st.st_gid != 0:
			cmd.append(" ".join(["sif", dst, "gid", str(st.st_gid)]))
		return cmd

	def mk_fs(self, args=[]):
		return Partition.mk_fs(self, args + ["-F"])

	def pop_fs(self, rootfs):
		if not self._mountpoint:
			return True
		rootfs = os.path.join(rootfs, self._mountpoint[1:])
		slen = len(rootfs)
		(fd, cmdfile) = tempfile.mkstemp()
		for root, dirs, files in os.walk(rootfs):
			if os.path.islink(root):
				continue
			dstdir = root[slen:]
			os.write(fd, 'cd "/' + dstdir + '"\n')
			for f in files + dirs:
				ret = self.pop_ext_path(rootfs, root, f)
				if ret == None:
					continue
				elif isinstance(ret, str):
					os.write(fd, ret + '\n')
				else:
					for cmd in ret:
						os.write(fd, cmd + '\n')
		os.write(fd, "quit\n\n")
		os.close(fd)
		ret = subprocess.call(["/sbin/debugfs", "-w", self._image,
			"-f", cmdfile],
			stdout=sout, stderr=serr)
		for tmpfile in self.symlinks:
			os.unlink(tmpfile)
		unlink(cmdfile, "debugfs.cmds")
		if ret != 0:
			error("Could not create filesystem")
			return False
		ret = subprocess.call(["fsck." + self._filesystem, "-y", "-f",	self._image], stdout=sout, stderr=serr)
		return ret == 0 or ret == 1

class Disk():
	"""
	Create images and/or fstab information from image configuration file.
	If image creation is required then a rootfs path should be supplied
	to populate the rootfs.
	"""
	parts = []
	_image = "<NOT SPECIFIED>"
	rootfs = None
	CHUNK_WRITE = 1024*1024*4
	def __init__(self, rootfs_path, config_file, image, populate=True):
		if image:
			self._image = image
		self.populate = populate
		if rootfs_path:
			self.rootfs = rootfs_path
			while self.rootfs.endswith("/"):
				self.rootfs = self.rootfs[:-1]
		parser = Parser()
		parser.read(config_file)
		parts = parser.sections()
		for p in parts:
			d = parser.getdict(p)
			if not "device" in d:
				error("Part " + p + " has no device description, skipping")
				continue
			elif d["device"] == "file":
				part = File(p, d)
			elif d["device"] == "none":
				part = Mount(p, d)
			elif d["device"] == "space":
				print "SPACE SKIP"
				continue
			else:
				part = Partition.factory(p, d)
			self.parts.append(part)

	def gen_fstab(self):
		if not args.fstab:
			error("You must specify a fstab file")
			return False
		if not args.device:
			return False
		f = sys.stdout
		if args.fstab != "-":
			f = open(args.fstab, "w")
		f.write("# Autogenerated by raptz image tool\n")
		f.write("\n")
		f.write("# <fs> <mp> <type> <opts> <dump> <pass>\n")
		f.write("proc /proc proc nodev,noexec,nosuid 0 0\n")
		for part in self.parts:
			line = part.get_fstabline(args.device)
			if line:
				log(["FSLINE", part.name])
				f.write(line+"\n")
		if f != sys.stdout:
			f.close()
		return True

	def dump(self, fdout, offset, name):
		os.lseek(fdout, offset, os.SEEK_SET)
		fdin = os.open(name, os.O_RDONLY)
		ret = self.CHUNK_WRITE
		size = 0
		while ret == self.CHUNK_WRITE:
			ret = os.write(fdout, os.read(fdin, self.CHUNK_WRITE))
			size += ret
		os.close(fdin)
		os.write(fdout, '\0'*(self.CHUNK_WRITE-ret))
		return ret == 0

	def calc_pos(self):
		self.parts = sorted(self.parts, key=lambda part: part._device)
		offset = 0
		# FIXME: This can be done better
		for part in self.parts:
			if part._size == 0:
				part._offset = -1
				continue
			if part._offset < 0:
				part._offset = offset
			elif part._offset < offset:
				pass
			else:
				offset = part._offset
			offset += part._size
		self.parts = sorted(self.parts, key=lambda part: part._offset)
		# Verify (this also gives us the size)
		offset = 0
		for part in self.parts:
			if part._size == 0:
				continue
			if offset > part._offset:
				print "OVERLAP"
			offset = part._offset + part._size
		return offset + 1024*1024*8

	def gen_img(self):
		if not self.rootfs:
			error("You must specify a rootfs to generate images.")
			return False
		for part in self.parts:
			log(["MAKE", "image", part.name, str(part._size),"start"])
			if not part.mk_image(self._image, self.rootfs, self.populate):
				error("Could not create image " + part.name)
				return False
			log(["MAKE", "image", part.name, str(part._size), "done"])

		log(["CALC", "offsets", "start"])
		size = self.calc_pos()
		log(["CALC", "offsets", "done"])

		log(["GEN", "image", "start"])
		if os.path.isfile(self._image):
			os.unlink(self._image)
		fd = os.open(self._image, os.O_WRONLY | os.O_CREAT)
		os.write(fd, '\0'*SECT_SIZE)
		os.ftruncate(fd, size)
		os.close(fd)
		log(["GEN", "image", "done", "0"])

		log(["GEN", "paritiontable", "start"])
		dfd, deffile = tempfile.mkstemp()
		os.write(dfd, "# partition table generated by raptz\n")
		os.write(dfd, "unit: sectors\n")
		os.write(dfd, "\n")
		for part in self.parts:
			line = part.get_sfdiskline()
			if line:
				os.write(dfd, line + "\n")
		os.write(dfd, "\n")
		os.lseek(dfd, 0, os.SEEK_SET)
		log(["GEN", "paritiontable", "done"])

		# Write partition table
		log(["WRT", "partitiontable", "start"])
		ret = subprocess.call(["/sbin/sfdisk", "--no-reread", self._image],
			stdin=dfd, stdout=sout, stderr=serr)
		os.close(dfd)
		if ret != 0:
			error("Could not create partition table")
			return False
		unlink(deffile, "sfdisk.def")
		log(["WRT", "partitiontable", "done"])

		fd = os.open(self._image, os.O_WRONLY)
		for part in sorted(self.parts, key=lambda x: x._offset):
			offset, size, image = part.get_image()
			if size > 0:
				log(["WRT", "image", part.name, str(offset),"start"])
				self.dump(fd, offset, image)
				log(["WRT", "image", part.name, str(offset), "done"])
		os.close(fd)
		return True
