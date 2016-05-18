#!/usr/bin/python

from raptzerror import RaptzException
from bootstrap import Bootstrap
from config import config
from host import host
import progs

class Debootstrap(Bootstrap):
	_variant="minbase"
	def __init__(self):
		Bootstrap.__init__(self)
		self._tot_packs = 1
		self._done_packs = 0
		progs.register("debootstrap")


	def bootstrap(self):
		""" Will install using debootstrap """
		cmds=["debootstrap", "--variant="+self._variant]

		if config.arch():
			cmds.append("--foreign")
			cmds.append("--arch="+config.arch())
		if not config.auth():
			cmds.append("--no-check-gpg")

		keyrings = config.keyrings()
		for keyring in keyrings:
			cmds.append("--keyring="+keyring)

		cmds.append(config.suite())
		cmds.append(config.rootfs())
		cmds.append(config.source())
		cmds.append("/usr/share/debootstrap/scripts/testing")
		r = host.runner

		first = [cmds[0], "--print-debs", "--keep-debootstrap-dir" ]	+ cmds[1:]
		if r.run(first) != 0:
			raise RaptzException("Debootstrap pre stage failed")
		if r.run(cmds) != 0:
			raise RaptzException("Debootstrap main stage failed")

	def secondstage(self):
		host.fs.mount_system()
		r = host.runner
		if r.chroot(["debootstrap/debootstrap", "--second-stage", "--variant=" + self._variant]) != 0:
			raise RaptzException("Debootstap second stage failed")

