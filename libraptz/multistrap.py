
from bootstrap import Bootstrap
from raptzerror import RaptzException
import os, select
import time
import tempfile
import shutil
from ConfigParser import SafeConfigParser
from config import config
from host import host
from time import time
import progs

class Multistrap(Bootstrap):
	def __init__(self):
		Bootstrap.__init__(self)
		self._msfile = tempfile.NamedTemporaryFile()
		self._msfile.delete = False
		self._items=0
		self._done=0
	        progs.register("multistrap");

	def fullinstall(self):
		return True
	
	def bootstrap(self):
		# Lets build the multistrap configuration file
		par = SafeConfigParser()
		par.add_section("General")
		par.set("General", "arch", config.arch())
		par.set("General", "directory", config.rootfs())
		par.set("General", "cleanup", str(True))
		par.set("General", "noauth", str(not config.auth()))
		keyrings = config.keyrings()
		par.set("General", "bootstrap", " ".join(keyrings.keys()))
		repros = config.repros()
		par.set("General", "aptsources", " ".join(repros))

		for repro in config.repros():
			par.add_section(repro)
			par.set(repro, "keyring", keyrings[repro])
			par.set(repro, "packages", "dash apt apt-utils " + " ".join(config.early_packages() + config.packages()))
			par.set(repro, "source", config.source(repro))
			par.set(repro, "suite", config.suite(repro))
			par.set(repro, "components", " ".join(config.components(repro)))
		par.write(self._msfile)
		self._msfile.close()
		r = host.runner
		cmds = ["multistrap", "-f", self._msfile.name]
		if r.run(cmds, stdoutfunc=self._stdout, stderrfunc=self._stderr) != 0:
			raise RaptzException("Multistrap main stage failed")

	def _stdout(self, line):
		if line.find("upgraded, ") < line.find("newly installed, "):
			# Use re
			p = line.split(",")[1].strip().split(" ")[0]
			self._items += int(p)
		if not self._items:
			return True
		if line.startswith("Get:"):
			self._done+=0.5
		elif line.startswith("I:"):
			self._done+=0.5
		host.progress(float(self._done)/self._items)
		return True
	def _stderr(self, line):
		host.warn(line)
		return True

	def secondstage(self):
		host.fs.mount_system()
		self._done = 0.0
		r = host.runner
		p = host.poller
		env={
			"DEBIAN_FRONTEND" : "noninteractive",
			"DEBCONF_NONINTERACTIVE_SEEN" : "true",
		}
		cmds = ["/var/lib/dpkg/info/dash.preinst", "install"]
		if r.chroot(cmds, env) != 0:
			raise RaptzException("Multistrap second stage failed")
		pout, pin = os.pipe()
		cmds = [ "dpkg", "--configure", "-a", "--status-fd", str(pin)]
		stfile = os.fdopen(pout)
		p.add(stfile, self._dpkg_status)
		if r.chroot(cmds, env) != 0:
			p.remove(stfile)
			raise RaptzException("Multistrap second stage failed")
		p.remove(stfile)

	def _dpkg_status(self, f, ev):
		if ev != select.POLLIN:
			return False
		st = [ x.strip() for x in  f.readline().split(":") ]
		if st[0] == "status" and st[-1] == "installed":
			self._done += 1.0
			host.progress(float(self._done)/self._items)
		return True
	
	def finalize(self):
		listd = config.rootfs("/etc/apt/sources.list.d")
		if os.path.isdir(listd):
			shutil.rmtree(listd)
		Bootstrap.finalize(self)

