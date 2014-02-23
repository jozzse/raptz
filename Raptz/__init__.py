#!/usr/bin/python2

# BSD New Licence (c) 2012 Jonas Zetterberg

import sys

sys.path.append("/usr/share/pyshared/")

import conf as conf
import time
import tempfile
import fileopt as fileopt
import stat
import shutil
import subprocess
import os

import rargs as rargs
import ui as ui
from tools import Tools

RCDFILE_CONTENT = """#!/bin/dash
exit 101
"""


DEF_NAME="/opt/<name>"

class RaptzError(Exception):
	""" Exception class for Raptz internal Errors """
	def __init__(self, text):
		self.text = text
	def __str__(self):
		return self.text

class Raptz(conf.Conf):
	""" The raptz base class.
	FIXME: Move none subcommand functions from this class
	"""
	def chroot(self, *cmd):
		""" Run Arm Chroot """
		ret = True
		# Setup needed filenames
		sr_rcdfile = self.sysrootPath("usr/sbin/policy-rc.d")
		sr_qemufile = self.sysrootPath("usr/bin/qemu-arm-static")
		lo_qemufile = "/usr/bin/qemu-arm-static"
		sr_linuxsofile = self.sysrootPath("/lib/ld-linux.so.3")
		lo_linuxsofile = u"/lib/ld-linux.so.3"

		# Prepare from lost previous commands
		self.tools.umount(self.sysrootPath("dev/pts"))
		self.tools.umount(self.sysrootPath("proc"))

		# Prepare sysroot files
		shutil.copy2(lo_qemufile, sr_qemufile)
		#os.chmod(sr_qemufile, 0755)

		f = open(sr_rcdfile, "w")
		f.write(RCDFILE_CONTENT)
		f.close()
		os.chmod(sr_rcdfile, 0755)

		# Move linux.so to local system
		try:
			pass#os.symlink(sr_linuxsofile, lo_linuxsofile)
		except OSError, why:
			if not why.errno == 17:
				self.ui.message(why.errno)
				raise
			self.ui.message("PASS")
			pass

		# Reset enviroment
		os.putenv("LC_ALL", "C")
		os.putenv("LANGUAGE", "C")
		os.putenv("LANG", "C")

		# Mount mountpoints
		self.tools.mount("/dev/pts", self.sysrootPath("dev/pts"), options="bind")
		if not self.tools.mount("none", self.sysrootPath("proc"), fstype="proc"):
			raise RaptzError("Could not mount proc filesystem")

		# Do the actuall chroot
		if len(cmd) == 0:
			# recombind args at ;
			cmds = " ".join(self.argv).split(";")
			for cmd in cmds:
				# Invokation from commandline
				run = cmd.strip().split(" ")
				if run == ['']:
					run = ["bash"]
				# resplit each command at " "
				ret = subprocess.call(["chroot", self.sysrootPath()] + run)
		else:
			# Invokation from command
			ret = self.tools.run("chroot", self.sysrootPath(), *cmd)
		# Unlink
		#os.unlink(lo_linuxsofile)
		os.unlink(sr_qemufile)
		os.unlink(sr_rcdfile)
		
		# Un ount
		self.tools.umount(self.sysrootPath("dev/pts"))
		if not self.tools.umount(self.sysrootPath("proc")):
			ret = 1
		return ret

	def multistrap(self):
		""" Will multistrap and copy extra root files from the root configuration structure """
		# First run multistrap
		self.ui.start("Multistrap")
		if self.args.suite:
			#
			# Replace suite name in multistrap configuration file.
			# The multistrap.cfg is read-only (Perforce), i.e. need
			# to create a copy...
			#
			self.tools.fixmultistrap(self.confName("multistrap.cfg"), self.args.suite)
			msfile = self.confName("multistrap.conf")
		else:
			# Keep original behaviour...
			msfile = self.confName("multistrap.cfg")
		if not msfile:
			raise RaptzError("Could not find multistrap file.")

		# Do multistrap
		if not self.tools.run("multistrap", '-f', msfile, '-d', self.sysrootPath()):
			raise RaptzError("Multistrapping failed")
		self.ui.stop()

		# Copy root filesystem
		tree = self.confTree("root", True)
		tree = [ ( x[0], self.sysrootPath(x[1])) for x in tree ]
		self.tools.CopyList(tree)

	def configure(self):
		""" Copy and run configuration system """
		# init scripts to run
		runfiles = ("init.sh",)
		if self.args.dev:
			runfiles = ("init.sh", "init.dev.sh")

		self.ui.start("Configure")
		# Run configurations in sorted order
		conflist = sorted(self.confLs("conf"), key=lambda sec: sec[1])
		for item in conflist:
			tmpdir = tempfile.mkdtemp(dir=self.sysrootPath("tmp"))
			self.ui.start(item[1])
			confdir = self.confTree(os.path.join("conf", item[1]), True)
			confdir = [(x[0], os.path.join(tmpdir, x[1])) for x in confdir]
			self.tools.CopyList(confdir)
			for ifile in runfiles:
				runfile = os.path.join(tmpdir, ifile)
				if not os.path.isfile(runfile):
					continue
				self.ui.start(ifile)
				if not self.chroot("/bin/bash", self.chrootPath(runfile), self.chrootPath(tmpdir)):
					raise RaptzError("Failed to execute " + runfile + " for config " + str(item))
				self.ui.stop()
			shutil.rmtree(tmpdir)
			self.ui.stop()
		self.ui.stop()

	def mksys(self):
		""" Create a system
		That is multistrap and configure.
		"""
		# Make sure we are unmounted
		self.ui.start(self.Name())
		self.tools.umount(self.sysrootPath("dev/pts"))
		self.tools.umount(self.sysrootPath("proc"))
		if not self.tools.umount(self.sysrootPath("")):
			raise RaptzError("Failed to unmount old sysroot " + self.sysrootPath(""))

		if self.args.clean and os.path.isdir(self.sysrootPath()):
			# Remove files
			self.tools.rmtree(self.sysrootPath())

		if self.args.tmpfs:
			if not self.tools.mount("none", self.sysrootPath(""), fstype="tmpfs", mkdir=True):
				raise RaptzError("Failed to create tmpfs on " + self.sysrootPath(""))

		self.multistrap()
		self.configure()

		self.ui.stop()
		self.ui.message("Sysroot in %s size is %d MB" % (self.sysrootPath(), self.tools.dirsize(self.sysrootPath()) / 1024))

	def image(self):
		""" Create a image of selected type """
		fo = fileopt.FileOpt(self.tools, self.ui)
		if self.args.jffs2:
			fo.mk_jffs2(self.sysrootPath(), self.args.jffs2, self.args.jffs2ext)
		if self.args.cpio:
			fo.mk_cpio(self.sysrootPath(), self.args.cpio)
		if self.args.tar:
			fo.mk_targz(self.sysrootPath(), self.args.tar)
		if self.args.ext3:
			size = self.tools.txt2size(self.args.size)
			self.ui.start("Make " + self.args.ext3 + " (ext3 " + str(size) + " Bytes)")
			self.tools.mkfile(self.args.ext3, self.tools.txt2size(self.args.size))
			fo.mk_ext3(self.sysrootPath(), os.path.abspath(self.args.ext3), True, "-F")
			self.ui.stop()

	def extract(self):
		""" Extract a image of selected type """
		fo = fileopt.FileOpt(self.tools, self.ui)
		if self.args.cpio:
			fo.ext_cpio(self.args.cpio, self.sysrootPath())
		if self.args.tar:
			fo.ext_targz(self.args.tar, self.sysrootPath())

	def mkdev(self):
		""" Fill a device with sysroot """
		if not self.args.device:
			print "No device specified"
			exit(1)
		if not self.args.device.startswith("/"):
			self.args.device="/dev/" + self.args.device
		part = self.args.device[-4:]
		dev = part[:-1]
		m = os.stat(self.args.device).st_mode;
		if not stat.S_ISBLK(m):
			print "Not a Blockdevice"
			exit(1)
		if not os.path.isfile("/sys/block/" + dev + "/removable"):
			print "Not a removable device"
			exit(1)
		fo = fileopt.FileOpt(self.tools, self.ui)
		fo.mk_ext3(self.sysrootPath(), self.args.device, self.args.mkfs, "")

	def config(self):
		""" Ugly extra configuration if needed """
		if self.args.resolv_conf:
			print "/etc/resolv.conf", self.args.name + "/root/etc/resolv.conf"
			shutil.copy2("/etc/resolv.conf", self.args.name + "/root/etc/resolv.conf")

	def __init__(self, ui=None):
		""" Setup args and parse.
		FIXME: Move to caller
		"""
		self.args = rargs.Rargs("Raptz sysroot handler")
		self.args.AddArg("name", "n", "default", "Configuration Name")

		cmd = self.args.AddCmd("mksys", self.mksys, "Create a rootfs system");
		cmd.AddArg("clean", "c", hlp="Clear sysroot directory before creating rootfs")
		cmd.AddArg("dev", "D", hlp='Add development packages to sysroot')
		cmd.AddArg("tmpfs", "t", hlp='Create tmpfs SYSROOT directory (forced clean)')

		cmd = self.args.AddCmd("chroot", self.chroot, "Run commands after -- argument in arm chroot enviroment");
		cmd.DashDashArgs(True)

		cmd = self.args.AddCmd("image", self.image, "Create image from a sysroot");
		cmd.AddArg("jffs2", "j", "", "Create jffs2 image")
		cmd.AddArg("jffs2ext", None, "", "Add extra commands to jffs2 within \"'s") # FIXME: we should be able to replace commands
		cmd.AddArg("cpio", "c", "", "Create cpio image")
		cmd.AddArg("tar", "t", "", "Create tar.gz image")
		cmd.AddArg("ext3", "e", "", "Create ext3 image")
		cmd.AddArg("size", "s", "256M", "Specify image size if size can be specified (ext3). (postfix with k, M and G avalible)")

		cmd = self.args.AddCmd("extract", self.extract, "Extract sysroot image")
		cmd.AddArg("tar", "t", "", "Extract tar.gz image")
		cmd.AddArg("cpio", "c", "", "Extract cpio image")

		cmd = self.args.AddCmd("mkdev", self.mkdev, "Make block device root fs from rootfs")
		cmd.AddArg("device", "d", "", "Move sysroot to ext3 filesystem on block device")
		cmd.AddArg("mkfs", "m", hlp="Create ext3 filesystem on --device device")

		cmd = self.args.AddCmd("config", self.config, "Change certain part of configuration")
		cmd.AddArg("resolv-conf", "r", hlp="Copy host system resolv.conf to configuration")

		self.args.AddArg("debug", hlp="Enable debugmode")
		self.args.AddArg("path", "p", DEF_NAME, "Path to sysroot")
		self.args.AddArg("name", "n", "default", "Configuration name")
		self.args.AddArg("ui", "u", "auto", "Select UI")
		self.args.AddArg("logfile", "l", "raptz.log", "Set logfile")
		self.args.AddArg("suite", "S", "", "Select distro for multistrap")

		self.argv = self.args.Parse(sys.argv[1:])

		if self.args.help or self.argv == None:
			return


		if not os.path.exists(self.args.name):
			raise RaptzError("Specified configuration \"" + self.args.name + "\" does not exist")

		if self.args.name == "default":
			# if name is default and a link then use linkname, otherwise use the name in name even if link.
			if os.path.islink(self.args.name):
				self.args.name = os.path.relpath(os.path.realpath(self.args.name))
			if self.args.path==DEF_NAME:
				self.args.path=DEF_NAME.replace("<name>", self.args.name)
		else:
			if self.args.path==DEF_NAME:
				self.args.path=DEF_NAME.replace("<name>", self.args.name)
			if os.path.islink(self.args.name):
				self.args.name = os.path.relpath(os.path.realpath(self.args.name))

		conf.Conf.__init__(self, self.args.name, self.args.path)
		if ui:
			self.ui = ui
		else:
			self.ui = ui.get(self.args.ui)(self.args.logfile)
		self.tools = Tools(self.ui)

	def start(self):
		""" Run configuration script
		"""
		if self.argv == None:
			return True
		return self.args.Func()


if __name__=="__main__":
	debug = False
	ret = 1
	try:
		raptz = Raptz()
		debug = raptz.args.debug
		ret = raptz.start()
	except RaptzError, why:
		print ""
		print ""
		print "Failed to create sysroot: " + str(why)
	except KeyboardInterrupt:
		print ""
		print ""
		print "It looks like you have canceled the Sysroot installation. Installation is not complete."
	except BaseException,why:
		print ""
		print ""
		print "Got Base exception ", repr(why), ". Installation failed."
		if debug:
			raise
	except Exception, why:
		print ""
		print ""
		print "Got exception", repr(why), ". Installation failed."
		if debug:
			raise
	exit(ret)
