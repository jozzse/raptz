
from ConfigParser import SafeConfigParser
import os

class Conf():
	def __init__(self, name, path):
		self.__names = []
		self.__path = os.path.abspath(path)
		self.__conf = SafeConfigParser()
		inifiles = []
		while os.path.exists(name):
			self.__names.append(name)
			inifile = os.path.join(name, "raptz.ini")
			if os.path.isfile(inifile):
				tmpc = SafeConfigParser()
				if tmpc.read((inifile,))[0] == inifile:
					inifiles = [inifile] + inifiles
				if tmpc.has_option("raptz", "base"):
					name = tmpc.get("raptz", "base")
				else:
					name = ""
			else:
				name = os.path.join(self.__names[-1], "base")
		#print self.__conf.get("raptz", "conf")


	def Name(self):
		return self.__names[0]

	def sysrootPath(self, path=""):
		if path.startswith("/"):
			return os.path.join(self.__path, path[1:])
		return os.path.join(self.__path, path)

	def chrootPath(self, path="/"):
		if not path.startswith("/"):
			return None
		return path[len(self.__path):]

	def confName(self, path=""):
		for x in self.__names:
			filename = os.path.join(x, path)
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
		for base in self.__names:
			basepath = os.path.join(base, path)
			if not os.path.isdir(basepath):
				continue
			for item in os.listdir(basepath):
				if not self.__inlist(item, f):
					f.append((os.path.join(basepath, item), item))
		return f

	def confTree(self, path, topdown=False):
		""" Retrive the list of files below path from all configs
			Each item is [ rel fromfile, /tofile ]
			The root element will contain [ None, "" ] and is therefor special.
		"""
		if not path:
			return None
		f = []
		baseroot = os.path.join(self.__names[0], path)
		if topdown:
			f.append((None, ""))
		for base in self.__names:
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
