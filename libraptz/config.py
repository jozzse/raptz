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
	name = ""
	mode = "fake"
	logfile = "raptz.log"
	ui = "term"
	def __init__(self):
		config = self
		self.arg_exec = sys.argv[0]
		if len(sys.argv) > 2:
			self.arg_command = sys.argv[1]
			self.arg_sysroot = sys.argv[2]
			self._sysroot = os.path.abspath(sys.argv[2])
		elif len(sys.argv) == 2:
			self.arg_command = sys.argv[1]
			self.arg_opts = ["--help"]
		else:
			self.arg_command = "help"

		if "--" in sys.argv:
			i = sys.argv.index("--")
			self.arg_pass = sys.argv[i+1:]
			self.arg_opts = sys.argv[3:i]
		else:
			self.arg_opts = sys.argv[3:]

		self._argp = ArgumentParser(prog="raptz")

	def get_argparser(self):
		return self._argp

	def setup(self):
		setup = SafeConfigParser()
		self._setupfile = self.sysroot("/var/lib/raptz.setup")
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
			default=self.logfile,
			help="Set logfile (default raptz.log)"
		)
		self._argp.add_argument('-u', '--ui', default=self.ui,
			help="Ui selection (log, term)"
		)

		args = self._argp.parse_args(self.arg_opts)
		if args.mode == "fake" and not os.getenv("FAKECHROOT"):
			fakeenv = self.sysroot("fake.env")
			cmd = ["fakechroot", "-c", "fcr" ]
			cmd+= ["fakeroot",
				"-s", self.sysroot(fakeenv)]
			if os.path.exists(fakeenv):
				cmd+=["-i", self.sysroot(fakeenv)]
			cmd+= sys.argv
			env = os.environ
			env["PATH"]+=":/usr/sbin"
			env["PATH"]+=":/sbin"
			if args.debug:
				env["FAKECHROOT_DEBUG"] = "1"
			print " ".join(cmd)
			ret = call(cmd, env=env)
			print ret
			exit(ret)

		self.mode = args.mode
		self.name = args.name
		self.logfile = args.logfile
		self.ui = args.ui
		self.debug = args.debug
		self._confpath = os.path.abspath(args.name)
		self._config = SafeConfigParser()
		self._config.read(os.path.join(self._confpath, "raptz.cfg"))
		return args

	def save(self):
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

	def packages(self, ctype="bootstrap"):
		cs=self._config.get("General", ctype).split()
		ret=[]
		for c in cs:
			ret += self._config.get(c, "packages").split()
		return ret
	def early_packages(self):
		if self.mode == "fake":
			return self._config.get("General", "fakepackages").split()
		return []

	def sysroot(self, path=None):
		""" Get a sysroot path """
		if path == None:
			return self._sysroot
		while path.startswith("/"):
			path = path[1:]
#			return os.path.join(self._sysroot, path[1:])
		return os.path.join(self._sysroot, path)
	
	def addsrcs(self, repro):
		try:
			return not self._config.getboolean(repro, "omitdebsrc")
		except NoOptionError:
			return True
	
	def rmsysroot(self, path):
		#FIXME: Move me
		return path[len(self._sysroot):]

	def confpath(self, path=None):
		""" Get configuration path """
		if path == None:
			return self._confpath
		if path.startswith("/"):
			return os.path.join(self._confpath, path[1:])
		return os.path.join(self._confpath, path)

global config
config = Config()
