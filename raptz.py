#!/usr/bin/python

# BSD New Licence (c) 2012 Jonas Zetterberg

import time
import tempfile
import fileopt
import stat
import shutil
import sys
import subprocess
import os

import rargs
import ui
from tools import Tools

RCDFILE_CONTENT = """#!/bin/dash
exit 101
"""

DEF_NAME="/opt/<name>"

class RaptzError(Exception):
	def __init__(self, text):
		self.text = text
	def __str__(self):
		return self.text

class Raptz():
	def mount(self):
		self.tools.mount("none", os.path.join(self.args.path, "proc"), fstype="proc")
		#tools.mount("/dev", os.path.join(self.args.path, "dev"), options="bind")
		#tools.mount("/dev/pts", os.path.join(self.args.path, "dev/pts"), options="bind")

	def umount(self):
		#tools.umount(os.path.join(self.args.path, "dev/pts"))
		#tools.umount(os.path.join(self.args.path, "dev"))
		self.tools.umount(os.path.join(self.args.path, "proc"))
		
	def chroot(self, *cmd):

		ret = True
		# Setup needed filenames
		sr_rcdfile = os.path.join(self.args.path, "usr/sbin/policy-rc.d")
		sr_qemufile = os.path.join(self.args.path, "usr/bin/qemu-arm-static")
		lo_qemufile = "/usr/bin/qemu-arm-static"
		sr_linuxsofile = os.path.join(self.args.path, "/lib/ld-linux.so.3")
		lo_linuxsofile = u"/lib/ld-linux.so.3"
		
		# Prepare from lost previous commands
		self.umount()
		
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
		self.mount()
		
		# Do the actuall chroot
		if len(cmd) == 0:
			# Invokation from commandline
			ret = subprocess.call(["chroot", self.args.path] + self.argv)
		else:
			# Invokation from command
			ret = self.tools.run("chroot", self.args.path, *cmd)

		# Unmount
		self.umount()

		# Unlink
		#os.unlink(lo_linuxsofile)
		os.unlink(sr_qemufile)
		os.unlink(sr_rcdfile)
		return ret

	def multistrap(self):
		""" Will multistrap and copy extra root files from the root configuration structure """
		file_multistrap = os.path.join(self.args.name, "multistrap.cfg")
		# Do multistrap
		self.ui.start("Multistrap")
		if not os.path.exists(file_multistrap):
			raise RaptzError("Could not find multistrap file \"" + file_multistrap + "\"")
		if not self.tools.run("multistrap", '-f', file_multistrap, '-d', self.args.path):
			raise RaptzError("Multistrapping failed")
		# Copy root filesystem
		self.ui.start("Preparing")
		self.tools.copydir(os.path.join(self.args.name, "root/"), self.args.path)
		self.ui.stop()
		self.ui.stop()

	def configure(self):
		""" Copy and run configuration system """
		self.ui.start("Configure")
		bdir = os.path.join(self.args.name, "conf")
		tdir = tempfile.mkdtemp(dir=os.path.join(self.args.path, "tmp"))
		localtdir = tdir[len(self.args.path):]
		for item in sorted(os.listdir(bdir)):
			cdir = os.path.join(bdir, item)
			if os.path.isfile(os.path.join(cdir, "init.sh")):
				self.ui.start(item)
				shutil.rmtree(tdir)
				self.tools.copydir(cdir, tdir)
				self.ui.start("Config")
				if not self.chroot("/bin/bash", os.path.join(localtdir, "init.sh"), localtdir):
					raise RaptzError("init.sh arm chroot failure for configuration " + item)
				self.ui.stop()
				if self.args.dev==True and os.path.isfile(os.path.join(tdir, "init.dev.sh")):
					self.ui.start("DevConfig")
					if not self.chroot("/bin/bash", os.path.join(localtdir, "init.dev.sh"), localtdir):
						raise RaptzError("init.dev.sh arm chroot failure for configuration " + item)
					self.ui.stop()
				self.ui.stop()
		shutil.rmtree(tdir)
		self.ui.stop()

	def mksys(self):
		# Make sure we are unmounted
		self.ui.start(self.args.name)
		self.umount() 

		if self.args.clean and os.path.isdir(self.args.path):
			# Remove files
			self.tools.rmtree(self.args.path)

		self.multistrap()
		self.configure()
		
		self.ui.stop()
		self.ui.message("Sysroot in %s size is %d MB" % (self.args.path ,self.tools.dirsize(self.args.path) / 1024))

	def image(self):
		fo = fileopt.FileOpt(self.tools, self.ui)
		if self.args.jffs2:
			fo.mk_jffs2(self.args.path, self.args.jffs2)
		if self.args.cpio:
			fo.mk_cpio(self.args.path, self.args.cpio)
		if self.args.ext3:
			size = self.tools.txt2size(self.args.size)
			self.ui.start("Make " + self.args.ext3 + " (ext3 " + str(size) + " Bytes)")
			self.tools.mkfile(self.args.ext3, self.tools.txt2size(self.args.size))
			fo.mk_ext3(self.args.path, os.path.abspath(self.args.ext3), True, "-F", self.args.cpio)
			self.ui.stop()
		
	def mkdev(self):
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
		fo.mk_ext3(self.args.path, self.args.device, self.args.mkfs, "", self.args.cpio)

	def config(self):
		if self.args.resolv_conf:
			print "/etc/resolv.conf", self.args.name + "/root/etc/resolv.conf"
			shutil.copy2("/etc/resolv.conf", self.args.name + "/root/etc/resolv.conf")
	def __init__(self):
		self.args = rargs.Rargs("Raptz sysroot handler")
		self.args.AddArg("name", "n", "default", "Configuration Name")
			
		cmd = self.args.AddCmd("mksys", self.mksys, "Create a rootfs system");
		cmd.AddArg("clean", "c", hlp="Clear sysroot directory before creating rootfs")
		cmd.AddArg("dev", "D", hlp='Add development packages to sysroot')
		
		cmd = self.args.AddCmd("chroot", self.chroot, "Run commands after -- argument in arm chroot enviroment");
		cmd.DashDashArgs(True)
		
		cmd = self.args.AddCmd("image", self.image, "Create image from a sysroot");
		cmd.AddArg("jffs2", "j", "", "Create jffs2 image")
		cmd.AddArg("cpio", "c", "", "Create cpio image")
		cmd.AddArg("ext3", "e", "", "Create ext3 image")
		cmd.AddArg("size", "s", "256M", "Specify image size if size can be specified (ext3). (postfix with k, M and G avalible)")

		cmd = self.args.AddCmd("mkdev", self.mkdev, "Make block device root fs from rootfs")
		cmd.AddArg("device", "d", "", "Move sysroot to ext3 filesystem on block device")
		cmd.AddArg("mkfs", "m", hlp="Create ext3 filesystem on --device device")
		cmd.AddArg("cpio", "c", "", hlp="Use this CPIO file instead of sysroot")

		cmd = self.args.AddCmd("config", self.config, "Change certain part of configuration")
		cmd.AddArg("resolv-conf", "r", hlp="Copy host system resolv.conf to configuration")
		
		self.args.AddArg("debug", hlp="Enable debugmode")
		self.args.AddArg("path", "p", DEF_NAME, "Path to sysroot")
		self.args.AddArg("name", "n", "default", "Configuration name")
		self.args.AddArg("ui", "u", "auto", "Select UI")
		self.args.AddArg("logfile", "l", "raptz.log", "Set logfile")
		
		self.argv = self.args.Parse(sys.argv[1:])
		
		if self.args.help:
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
				
		self.ui = ui.get(self.args.ui)(self.args.logfile)
		self.tools = Tools(self.ui)

	def start(self):
		return self.args.Func()

if __name__=="__main__":
	debug = False
	try:
		raptz = Raptz()
		debug = raptz.args.debug
		raptz.start()
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

print ""
