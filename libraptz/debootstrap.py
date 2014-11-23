#!/usr/bin/python

from raptzerror import RaptzException
from bootstrap import Bootstrap
from config import config
from host import host

class Debootstrap(Bootstrap):
	_variant="minbase"
	def __init__(self):
		Bootstrap.__init__(self)
		self._tot_packs = 1
		self._done_packs = 0

	def _setpaks(self, line):
		self._tot_packs = len(line.split()) * 4
		return False

	def _stdout(self, l):
		if l.startswith("I: Validating") or l.startswith("I: Extracting") or l.startswith("I: Configuring") or l.startswith("I: Unpacking"):
			self._done_packs += 1
		elif l == "I: Base system installed successfully.":
			self._done_packs = self._tot_packs
		prog = self._done_packs/float(self._tot_packs)
		host.progress(prog, l)
		return True

	def _stderr(self, line):
		if line.startswith("I"):
			host.text(line)
		else:
			host.dbg(line)
		return True

	def bootstrap(self):
		""" Will install using debootstrap """
		cmds=["/usr/sbin/debootstrap", "--variant="+self._variant]

		if config.arch():
			cmds.append("--foreign")
			cmds.append("--arch="+config.arch())
		if not config.auth():
			cmds.append("--no-check-gpg")

		keyrings = config.keyrings()
		for keyring in keyrings:
			cmds.append("--keyring="+keyring)

		cmds.append(config.suite())
		cmds.append(config.sysroot())
		cmds.append(config.source())
		cmds.append("/usr/share/debootstrap/scripts/testing")
		r = host.runner

		first = [cmds[0], "--print-debs", "--keep-debootstrap-dir" ]	+ cmds[1:]
		if r.run(first, stdoutfunc=self._setpaks, stderrfunc=self._stderr) != 0:
			raise RaptzException("Debootstrap pre stage failed")
		if r.run(cmds, stdoutfunc=self._stdout, stderrfunc=self._stderr) != 0:
			raise RaptzException("Debootstrap main stage failed")

	def secondstage(self):
		r = host.runner
		if r.chroot(["debootstrap/debootstrap", "--second-stage", "--variant=" + self._variant],
			stdoutfunc=self._stdout, stderrfunc=self._stderr) != 0:
			raise RaptzException("Debootstap second stage failed")

