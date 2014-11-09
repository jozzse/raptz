
from bootstrap import Bootstrap
from raptzerror import RaptzException
import os, select
import time
import tempfile
import shutil
from ConfigParser import SafeConfigParser


class Multistrap(Bootstrap):
	def __init__(self, host):
		Bootstrap.__init__(self, host)
		self._msfile = tempfile.NamedTemporaryFile()
		self._msfile.delete = False
		self._items=0
		self._done=0
	def bootstrap(self):
		# Lets build the multistrap configuration file
		conf = self._host.conf()
		par = SafeConfigParser()
		par.add_section("General")
		par.set("General", "arch", conf.arch())
		par.set("General", "directory", conf.sysroot())
		par.set("General", "cleanup", str(True))
		par.set("General", "noauth", str(not conf.auth()))
		keyrings = conf.keyrings()
		par.set("General", "bootstrap", " ".join(keyrings.keys()))
		repros = conf.repros()
		par.set("General", "aptsources", " ".join(repros))

		for repro in conf.repros():
			par.add_section(repro)
			par.set(repro, "keyring", keyrings[repro])
			par.set(repro, "packages", "dash apt apt-utils")
			par.set(repro, "source", conf.source(repro))
			par.set(repro, "suite", conf.suite(repro))
			par.set(repro, "components", " ".join(conf.components(repro)))
		par.write(self._msfile)
		self._msfile.close()
		r = self._host.runner
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
		self._host.progress(float(self._done)/self._items)
		return True
	def _stderr(self, line):
		print "WARN:" + line
		self._host.warn(line)
		return True

	def secondstage(self):
		self._done = 0.0
		r = self._host.runner
		p = self._host.poller
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
			self._host.progress(float(self._done)/self._items)
		return True
	
	def finalize(self):
		conf = self._host.conf()
		listd = conf.sysroot("/etc/apt/sources.list.d")
		if os.path.isdir(listd):
			shutil.rmtree(listd)
		Bootstrap.finalize(self)

