
import subprocess
import shutil
import os
import re

# BSD New Licence (c) 2012 Jonas Zetterberg

class Tools():
	def __init__(self, ui):
		self.ui = ui

	def run(self, *command):
		p = subprocess.Popen(command,
			stderr=subprocess.STDOUT,
			stdout=subprocess.PIPE)
		line = "."
		while line != "":
			line = p.stdout.readline()
			self.ui.line(line[:-1])
		ret = p.wait()
		return ret == 0

	def mkfile(self, filename, size=0):
		file = open(filename, "w")
		if not file:
			return False
		file.truncate(size)
		file.close()
		return True

	def txt2size(self, txtsize):
		dec = txtsize[-1]
		try:
			if dec == "k":
				return int(txtsize[:-1]) * 1024
			if dec == "M":
				return int(txtsize[:-1]) * 1024 * 1024
			if dec == "G":
				return int(txtsize[:-1]) * 1024 * 1024 * 1024
			return int(txtsize)
		except ValueError:
			pass
		return 0

	def ismount(self, mp):
		""" Check if a mount point is already mounted.
		return True if mountpoint is mounted, False otherwize
		"""
		# remove ending / if any
		if mp.endswith('/'):
			mp = mp[:-1] 
		f = open("/etc/mtab")
		for line in f:
				if (line.split()[1] == mp):
					return True
		return False

	def mount(self, device, mp, fstype=None, options=None):
		""" Mount device (device) on mountpoint (mp) using optional type (fstype) with option options(options)
		return True if mountpoint is mounted after operation, False otherwize
		"""
		if not os.path.exists(mp):
			return False	
		if self.ismount(mp):
			return True
		cmd=["mount"]
		if fstype:
			cmd = cmd + ["-t", fstype ]
		if options:
			cmd = cmd + ["-o", options ]
		cmd = cmd + [device, mp]
		if subprocess.call(cmd) == 0:
			return True
		return False

	def umount(self, mp):
		""" Unmount mountpoint mp 
		return True if mountpoint is unmounted after operation, False otherwize
		"""
		if not self.ismount(mp):
			return True
		if subprocess.call(["umount", mp]) == 0:
			return True
		return False

	def dirsize(self, path):
		""" Get size of dir """
		p = subprocess.Popen(("du", "--max-depth=0", path),
			stdout=subprocess.PIPE)
		output = p.communicate()[0]
		return int(output.split()[0]) # remove ending path

	def files(self, path, topdown=False):
		""" Retrive the list of files below path """
		f = []
		if topdown:
			f.append(path)
		for root, dirs, files in os.walk(path, topdown=topdown):
			for filename in files:
				f.append(os.path.join(root, filename))
			for dirname in dirs:
				f.append(os.path.join(root, dirname))
		if not topdown:
			f.append(path)
		return f

	def dirs(self, path):
		""" Get list of dirs """
		f = []
		for root, dirs, files in os.walk(path, topdown=False):
			for dirname in dirs:
				f.append(os.path.join(root, dirname))
		f.append(path)
		return f


	def copydir(self, frm, to):
		""" Copy path frm to path to (like cp -r) """
		if frm.endswith("/"):
			frm = frm[:-1]
		if not to.endswith("/"):
			to = to + "/"

		files = self.files(frm, topdown=True)
		self.ui.set_lines(len(files))

		if not os.path.isdir(to):
			os.mkdir(to)
		for item in files:
			src = item
			dst = to + item[len(frm):]
			if os.path.isdir(src):
				self.ui.line(" ".join(["dir ", src, dst]))
				if not os.path.isdir(dst):
					os.mkdir(dst)
			else:
				self.ui.line(" ".join(["file", src, dst]))
				shutil.copy2(src, dst)

	def CopyList(self, lst):
		if lst[0][0] != None:
			return False # Not topdown
		self.ui.start("Copy Tree to " + lst[0][1])
		for (frm, to) in lst[1:]:
			if os.path.isdir(frm):
					self.ui.line(" ".join(["dir ", frm, to]))
					if not os.path.isdir(to):
						os.mkdir(to)
			else:
				self.ui.line(" ".join(["file", frm, to]))
				shutil.copy2(frm, to)
		self.ui.stop()
		return True

	def fixmultistrap(self, filename, codename):
		file = open(filename, "r")
		if not file:
			return False
		s = file.read()
		file.close()

		m = re.search(".*\[FLIR\].+suite=(\w+).*", s, re.DOTALL)
		if m and m.groups() > 0:
			s = s[:m.start(1)] + codename + s[m.end(1):]

		file = open(os.path.join(os.path.dirname(filename), "multistrap.conf"), "w");
		if not file:
			return False
		file.write(s);
		file.close()

		return True

	def rmtree(self, path):
		""" Remove complete path from filesystem """
		self.ui.start("rmtree("+path+")")
		flist = self.files(path)
		self.ui.set_lines(len(flist))
		i =0
		for f in flist:
			self.ui.line(f)
			i = i+1
			if f == path:
				continue
			try:
				if os.path.isdir(f) and not os.path.islink(f):
					os.rmdir(f)
				else:
					os.unlink(f)
			except OSError:
				print f
				raise
		self.ui.stop()
