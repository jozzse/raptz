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
	def __init__(self):
		config = self
		self.arg_exec = sys.argv[0]
		if len(sys.argv) >= 1:
			self.arg_command = sys.argv[1]
		try:
			i = sys.argv.index("--")
			self.arg_pass = sys.argv[i+1:]
			self.arg_opts = sys.argv[2:i]
		except ValueError:
			self.arg_opts = sys.argv[2:]

		self._argp = ArgumentParser(prog="raptz")
		self._argp.add_argument('-p', '--path', default="sysroot",
			help="Path to sysroot"
		)
		self._argp.add_argument("--debug", default=False,
			action='store_true',
			help="Enable debug mode"
		)
		self._argp.add_argument('-n', '--name', default="default",
			help="Configuration name"
		)
		self._argp.add_argument('-l', '--logfile', default="raptz.log",
			help="Set logfile (default raptz.log)"
		)
		self._argp.add_argument('-u', '--ui', default="term",
			help="Ui selection (log, term)"
		)
		self._argp.add_argument('-m', '--mode', default="fake",
			help="Mode (fake or root)"
		)

	def get_argparser(self):
		return self._argp

	def setup(self):
		args = self._argp.parse_args(self.arg_opts)
		self.args = args
		self._sysroot = os.path.abspath(args.path)
		if self.args.mode == "fake" and not os.getenv("FAKECHROOT"):
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
			if self.args.debug:
				env["FAKECHROOT_DEBUG"] = "1"
			print " ".join(cmd)
			ret = call(cmd, env=env)
			print ret
			exit(ret)
		self._confpath = os.path.abspath(args.name)
		self._config = SafeConfigParser()
		self._config.read(os.path.join(self._confpath, "raptz.cfg"))
		self.debug = args.debug

	def repros(self):
		return self._config.get("General", "bootstrap").split()

	def source(self, repro=None):
		if repro == None:
			repro = self.repros()[0]
		return self._config.get(repro, "source")

	def suite(self, repro=None):
		if repro != None:
			return self._config.get(repro, "suite")
		if self.args.suite:
			return self.args.suite
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
		if self.args.mode == "fake":
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
