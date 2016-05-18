#!/usr/bin/python

import sys
import os
import select
from host import host
from subprocess import Popen, check_output

class Apt():
	_progto = [0.0, 0.0]
	_prog = [0.0, 0.0]

	def _prog_reset(self, pm=False):
		self._prog = [0.0, 0.0]
		self._progto[0] = 0.0
		if pm:
			self._progto[1] = 1.0
		else:
			self._progto[1] = 0.0

	def _prog_set(self, progtype, prog):
		if progtype == "dlstatus":
			self._progto[0] = 1.0
			self._prog[0] = prog/100.0
		else:
			self._prog[1] = prog/100.0
		prog = (self._prog[0] + self._prog[1]) / (self._progto[0] + self._progto[1])
		return prog

	def clean(self):
		self._prog_reset()
		return self._run("update")

	def update(self):
		self._prog_reset()
		return self._run("update")

	def upgrade(self):
		self._prog_reset(True)
		return self._run("upgrade", opts=["-y"])

	def install(self, pkgs):
		self._prog_reset(True)
		return self._run("install", opts=["-y"], pkgs=pkgs)

	def remove(self, pkgs):
		self._prog_reset(True)
		return self._run("remove", opts=["-y"], pkgs=pkgs)

	def _run(self, command, opts=None, pkgs=None):
		pout, pin = os.pipe()

		cmd = [
			"apt-get",
			"-o", "APT::Status-Fd="+str(pin),
		]
		if opts != None:
			cmd += opts
		cmd.append(command)
		if pkgs != None:
			cmd += pkgs

		stfile = os.fdopen(pout)
		ret = host.runner.chroot(cmd)
		return ret

	def _apt_status(self, f, ev):
		if ev != select.POLLIN:
			return False
		st = f.readline().strip().split(":")
		prog = 0.0
		if st[0] == "dlstatus" or st[0] == "pmstatus":
			prog = self._prog_set(st[0], float(st[2]))
		else:
			return True
		host.progress(prog, st[3])
		return True

