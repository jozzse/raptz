#!/usr/bin/python

from raptzerror import RaptzException
from bootstrap import Bootstrap
from config import config
from host import host
import progs

class CDebootstrap(Bootstrap):
	_flavour="minimal"
	def __init__(self):
		self._tot_packs = 1
		self._done_packs = 0
		progs.register("cdebootstrap")

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
		cmds=["cdebootstrap", "--flavour="+self._flavour]

		if config.arch():
			cmds.append("--foreign")
			cmds.append("--arch="+config.arch())
		if not config.auth():
			cmds.append("--allow-unauthenticated")

		keyrings = config.keyrings()
		for keyring in keyrings:
			cmds.append("--keyring="+keyring)

		cmds.append(config.suite())
		cmds.append(config.rootfs())
		cmds.append(config.source())
#		cmds.append("/usr/share/debootstrap/scripts/testing")
		r = host.runner

		if r.run(cmds, stdoutfunc=self._stdout, stderrfunc=self._stderr) != 0:
			raise RaptzException("Debootstrap main stage failed")

	def secondstage(self):
		host.fs.mount_system()
		r = host.runner
		if r.chroot(["/sbin/cdebootstrap-foreign"],
			stdoutfunc=self._stdout, stderrfunc=self._stderr) != 0:
			raise RaptzException("Debootstap second stage failed")

