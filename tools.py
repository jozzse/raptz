
import subprocess
import shutil
import os

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
		if not os.path.exists(mp):
			return 0
		p = subprocess.Popen(("df", "-P", mp),
			stdout=subprocess.PIPE)
		return p.communicate()[0].strip().endswith(mp)

	def mount(self, device, mp, fstype=None, options=None):
		cmd=["mount"]
		if fstype:
			cmd = cmd + ["-t", fstype ]
		if options:
			cmd = cmd + ["-o", options ]
		cmd = cmd + [device, mp]
		if subprocess.call(cmd) == 0:
			return 0
		raise

	def umount(self, mp):
		""" Unmount mountpoint mp """
		if not self.ismount(mp):
			return 0
		if subprocess.call(["umount", mp]) == 0:
			return 0
		raise

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

	def rmtree(self, path):
		""" Remove complete path from filesystem """
		self.ui.start("rmtree("+path+")")
		flist = self.files(path)
		self.ui.set_lines(len(flist))
		i =0
		for f in flist:
			self.ui.line(f)
			i = i+1
			try:
				if os.path.isdir(f) and not os.path.islink(f):
					os.rmdir(f)
				else:
					os.unlink(f)
			except OSError:
				print f
				raise
		self.ui.stop()
