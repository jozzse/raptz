
from ConfigParser import SafeConfigParser
import os


class Conf():
	conf_paths=(
		".",
		os.path.expanduser("~/.config/ratpz/targets"),
		"/usr/share/raptz/targets", 
		)
	confs = []
	def __init__(self, name, sysroot):
		self._sysroot = sysroot
		# Find all sub configurations.
		path = self.expand_path(name)
		if not path:
			raise "Inifile " + name + " not found"
		while path:
			self.confs.append((name, path))
			inifile = os.path.join(path, "raptz.ini")
			if os.path.isfile(inifile):
				tmpc = SafeConfigParser()
				if tmpc.read(inifile)[0] != inifile:
					raise "Could not read inifile"
				if tmpc.has_option("raptz", "base"):
					name = tmpc.get("raptz", "base")
				else:
					name = None
			path = self.expand_path(name)

		# Load configuration files in order
		confs = [os.path.join(x[1], "raptz.ini") for x in self.confs]
		self.config = SafeConfigParser()
		self.config.read(confs)

	def expand_path(self, name):
		if not name:
			return None
		for path in self.conf_paths:
			p = os.path.join(path, name)
			if os.path.exists(p):
				return p
		return None

	def Name(self):
		""" Return configuration name """
		return self.confs[0][0]

	def sysrootPath(self, path=""):
		""" Return path which have sysroot path prepended """
		if path.startswith("/"):
			path = path[1:]
		return os.path.join(self._sysroot, path)

	def chrootPath(self, path="/"):
		""" Return path which have sysroot path removed """
		if not path.startswith("/"):
			return None
		if not path.startswith(self._sysroot):
			return None
		return path[len(self._sysroot):]

	def confName(self, path=""):
		""" Return full path to specific configuration file """
		for c in self.confs:
			filename = os.path.join(c[1], path)
			if os.path.exists(filename):
				return filename
		return None

	def __inlist(self, name, lst):
		""" Return true if name is in dirlist [x, "name" ] item """
		for item in lst:
			if item[1] == name:
				return True
		return False

	def confLs(self, path):
		if not path:
			return None
		f = []
		for name, base in self.confs:
			basepath = os.path.join(base, path)
			if not os.path.isdir(basepath):
				continue
			for item in os.listdir(basepath):
				if not self.__inlist(item, f):
					f.append((os.path.join(basepath, item), item))
		return f

	def confTree(self, path, topdown=False):
		""" Retrive the list of files below path from all configs
			Each item is [ fromfile, /tofile ]
			The root element will contain [ None, "" ] and is therefor special.
		"""
		if not path:
			return None
		f = []
		if topdown:
			f.append((None, ""))
		for name, base in self.confs:
			basepath = os.path.join(base, path)
			for root, dirs, files in os.walk(basepath, topdown=topdown):
				for filename in files:
					filepath = os.path.join(root, filename)
					topath = filepath[len(basepath)+1:]
					if not self.__inlist(topath, f):
						f.append((filepath, topath))
				for dirname in dirs:
					dirpath = os.path.join(root, dirname)
					topath = dirpath[len(basepath)+1:]
					if not self.__inlist(topath, f):
						f.append((dirpath, topath))
		if not topdown:
			f.append((None, ""))
		return f
