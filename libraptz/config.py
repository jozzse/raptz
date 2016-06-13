#!/usr/bin/python

import sys
import os
import select
from subprocess import Popen, check_output, call
from ConfigParser import SafeConfigParser, NoOptionError
from argparse import ArgumentParser

class Config:
	arg_command = "help"
	arg_pass = None
	name = "sid"
	mode = "root"
	stdout = None # No redirection
	stderr = None # No redirection
	def __init__(self):
		config = self
		self.arg_exec = sys.argv[0]
		self._rootfs = "./dummmy"
		if len(sys.argv) > 2:
			self.arg_command = sys.argv[1]
			self.arg_rootfs = sys.argv[2]
			self._rootfs = os.path.abspath(sys.argv[2])
                        if sys.argv[1] == "help":
                                self.arg_command = sys.argv[2]
                                sys.argv[2] = "--help"
	        elif len(sys.argv) == 2:
			self.arg_command = sys.argv[1]
			self.arg_opts = ["--help"]
		else:
			self.arg_command = "help"
	        self._argp = ArgumentParser(prog="raptz", usage='%(prog)s ' +
                                            self.arg_command +
                                            ' <rootfs-path> [options]')
		if len(sys.argv) <= 2 or sys.argv[2] == "-h" or sys.argv[2] == "--help":
			self.arg_opts = [ "--help" ]
		elif "--" in sys.argv:
			i = sys.argv.index("--")
			self.arg_pass = sys.argv[i+1:]
			self.arg_opts = sys.argv[3:i]
		else:
			self.arg_opts = sys.argv[3:]


	def get_argparser(self):
		return self._argp

	def setup(self):
		setup = SafeConfigParser()
		self._setupfile = self.rootfs("/var/lib/raptz.setup")
		if os.path.isfile(self._setupfile):
			setup.read(self._setupfile)
		else:
			setup.add_section("raptz")
			setup.set("raptz", "name", self.name)
			setup.set("raptz", "mode", self.mode)
		self._argp.add_argument('-n', '--name',
			default=setup.get("raptz", "name"),
			help="Name or path of configuration. *"
		)
		self._argp.add_argument('-m', '--mode',
			default=setup.get("raptz", "mode"),
			help="Mode (fake or root) *"
		)

		self._argp.add_argument("--debug", default=False,
			action='store_true',
			help="Enable debug mode"
		)
		self._argp.add_argument('-l', '--logfile',
			default=None,
			help="Log to file instead of terminal"
		)
		self._argp.add_argument('-q', '--quiet',
			action='store_true', default=False,
			help="Do not print log from standard-out"
		)

		args = self._argp.parse_args(self.arg_opts)
#		if args.mode == "fake" and not os.getenv("FAKECHROOT"):
#			fakeenv = self.rootfs("fake.env")
#			cmd = ["fakechroot", "-c", "fcr" ]
#			cmd+= ["fakeroot",
#				"-s", self.rootfs(fakeenv)]
#			if os.path.exists(fakeenv):
#				cmd+=["-i", self.rootfs(fakeenv)]
#			cmd+= sys.argv
#			env = os.environ
#			env["PATH"]+=":/usr/sbin"
#			env["PATH"]+=":/sbin"
#			if args.debug:
#				env["FAKECHROOT_DEBUG"] = "1"
#			print " ".join(cmd)
#			ret = call(cmd, env=env)
#			print ret
#			exit(ret)

		self.mode = args.mode
		self.name = args.name
		if args.logfile is not None:
			logfile = open(args.logfile, "w")
			self.stdout = logfile
			self.stderr = logfile
		if args.quiet:
			nullfile = open("/dev/null", "w")
			self.stdout = nullfile
		self.debug = args.debug
		self._confpath = os.path.abspath(args.name)
		self._config = SafeConfigParser()
		self._config.read(os.path.join(self._confpath, "raptz.cfg"))
		return args

	def get_conf_path(self, for_file=None):
		if not for_file:
			return self._confpath
		return os.path.join(self._confpath, for_file)

	def save(self):
		try:
			self._setupfile
		except AttributeError:
			return
		setup = SafeConfigParser()
		setup.add_section("raptz")
		setup.set("raptz", "mode", self.mode)
		setup.set("raptz", "name", self.name)
		with open(self._setupfile, "wb") as setupfile:
			setup.write(setupfile)

	def repros(self):
		return self._config.get("General", "bootstrap").split()

	def source(self, repro=None):
		if repro == None:
			repro = self.repros()[0]
		return self._config.get(repro, "source")

	def suite(self, repro=None):
		if repro != None:
			return self._config.get(repro, "suite")
		bootstraps=self._config.get("General", "bootstrap").split()
		return self._config.get(bootstraps[0], "suite")

	def components(self, repro=None):
		if repro != None:
			return self._config.get(repro, "components").split()
		raise

	def arch(self):
		return self._config.get("General", "arch")

	def auth(self):
		return not self._config.getboolean("General", "noauth")

	def keyrings(self, ctype="bootstrap"):
		cs=self._config.get("General", ctype).split()
		ret={}
		for c in cs:
			ret[c] = self._config.get(c, "keyring")
		return ret

	def packages(self, part=None, ctype="bootstrap"):
		cs=self._config.get("General", ctype).split()
		if part is None:
			ret=[]
			for c in cs:
				ret += self._config.get(c, "packages").split()
			return ret
		return self._config.get(part, "packages").split()

	def early_packages(self):
		if self.mode == "fake":
			return self._config.get("General", "fakepackages").split()
		return []

	def rootfs(self, path=None):
		""" Get a rootfs path """
		if path == None:
			return self._rootfs
		while path.startswith("/"):
			path = path[1:]
#			return os.path.join(self._rootfs, path[1:])
		return os.path.join(self._rootfs, path)
	
	def addsrcs(self, repro):
		try:
			return not self._config.getboolean(repro, "omitdebsrc")
		except NoOptionError:
			return True
	
	def rmrootfs(self, path):
		#FIXME: Move me
		return path[len(self._rootfs):]

	def confpath(self, path=None):
		""" Get configuration path """
		if path == None:
			return self._confpath
		if path.startswith("/"):
			return os.path.join(self._confpath, path[1:])
		return os.path.join(self._confpath, path)

global config
config = Config()
