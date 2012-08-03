#!/usr/bin/python

# BSD New Licence (c) 2012 Jonas Zetterberg

import stat
import argparse
import shutil
import tempfile
import sys
import subprocess
import os

import ui
from tools import Tools

RCDFILE_CONTENT = """#!/bin/dash
exit 101
"""


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
			ret = subprocess.call(["chroot", self.args.path] + self.args.command.split())
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
		# Copy and run configuration system
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
		self.ui.message("Sysroot size is %d MB" % (self.tools.dirsize(self.args.path) / 1024))

	def image(self):
		files = self.tools.files(self.args.path, topdown=True)
		dirs = self.tools.dirs(self.args.path)
		if self.args.jffs2:
			self.ui.start(self.args.jffs2 + "(jffs2)", len(files) + len(dirs))
			self.tools.run("mkfs.jffs2", 
				"-r", self.args.path,
				"-l", "-n" ,"-e", "128",
				"-v", "-o", self.args.jffs2)
			self.ui.stop()
		if self.args.cpio:
			self.ui.start(self.args.cpio + "(cpio)", len(files))
			l = len(self.args.path)
			f = ["".join([".", fl[l:], "\n"]) for fl in files]
			fd=open("c", "wb", 0644)
			p = subprocess.Popen(["cpio", "-o"], 
				cwd=self.args.path,
			    stdin=subprocess.PIPE,
				stdout=fd)
			for ff in f:
				p.stdin.write(ff)
				self.ui.line(ff)
			p.stdin.close()
			p.wait()
			self.ui.stop()
		if self.args.device:
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
			
			if self.args.mkfs:
				self.ui.start("Mkfs")
				self.tools.run("mkfs.ext3", self.args.device)
				self.ui.stop()
			
			mp = tempfile.mkdtemp(dir="/tmp")
			self.ui.start("Mount(" + mp + ")")
			self.tools.mount(self.args.device, mp)
			self.ui.stop()
			
			self.ui.start(self.args.cpio + "(copy)", len(files))
			l = len(self.args.path)
			f = ["".join([".", fl[l:], "\n"]) for fl in files]
			pipe = os.pipe()
			po = subprocess.Popen(["cpio", "-o"],
				cwd=self.args.path,
			    stdin=subprocess.PIPE,
				stdout=os.fdopen(pipe[1], "wb"))
			pi = subprocess.Popen(["cpio", "-i"],
				cwd=mp,
				stdin=os.fdopen(pipe[0], "rb"))
			for ff in f:
				po.stdin.write(ff)
				self.ui.line(ff)
			po.stdin.close()
			po.wait()
			pi.wait()
			self.ui.stop()
			self.ui.start("UnMount(" + mp + ")")
			self.tools.umount(mp)
			self.ui.stop()


	def config(self):
		if self.args.resolv_conf:
			print "/etc/resolv.conf", self.args.name + "/root/etc/resolv.conf"
			shutil.copy2("/etc/resolv.conf", self.args.name + "/root/etc/resolv.conf")
	def __init__(self):
		parser = argparse.ArgumentParser(description='Raptz python UI.')
		subp = parser.add_subparsers()
		
		# SYSROOT
		mksysp = subp.add_parser("mksys", help="Create a sysroot")
		mksysp.set_defaults(func=self.mksys)
		mksysp.add_argument('-c', '--clean', action='store_true',
							   help='Clean sysroot before multistrapping')
		mksysp.add_argument('-D', '--dev', action='store_true',
							   help='Add development packages to sysroot')
	
		# CHROOT
		chrootp = subp.add_parser("chroot", help="Run arm chroot")
		chrootp.add_argument('command', default="/bin/bash", help="Command to call")
		chrootp.set_defaults(func=self.chroot)
	
		# IMAGE
		imagep = subp.add_parser("image", help="Create image from a sysroot")
		imagep.set_defaults(func=self.image)
		imagep.add_argument('-j', '--jffs2', metavar='<file>', default="", 
							   help='Create jffs2 image')
		imagep.add_argument('-c', '--cpio', metavar='<file>', default="", 
							   help='Create cpio image')
		imagep.add_argument('-d', '--device', metavar='<device>', default="", 
							   help='Move to device')
		imagep.add_argument("-m", "--mkfs", action='store_true',
								help='Create filesystem')
		
		# CONFIG
		imagep = subp.add_parser("config", help="Change certain part of configuration")
		imagep.set_defaults(func=self.config)
		imagep.add_argument('-r', '--resolv-conf', action='store_true',
							   help='Copy host system resolv.conf to configuration')

		# BASIC
		parser.add_argument('--debug', action='store_true',
							   help='Enable debugmode')
		parser.add_argument('-p', '--path', metavar='<path>', default="", 
							   help='Path to sysroot (default=/opt/<name>)')
		parser.add_argument('-n', '--name', metavar='<name>', default="default", 
							   help='Name of configuration to use (default=default)')
		parser.add_argument('-u', '--ui', metavar='<auto|raw|text>', default="auto", 
							   help='UI selection (default=text)')

		parser.add_argument('-l', "--logfile", metavar='<filename>', default="raptz.log",
							   help='Set logfile to <filename>')
	
		self.args = parser.parse_args()
	

		if os.path.islink(self.args.name):
				self.args.name = os.path.relpath(os.path.realpath(self.args.name))
	
		if self.args.path=="":
			self.args.path="/opt/" + self.args.name
		
		self.ui = ui.get(self.args.ui)(self.args.logfile)
		self.tools = Tools(self.ui)

	def start(self):
		self.args.func()
	
if __name__=="__main__":
	raptz = Raptz()
	try:
		raptz.start()
	except RaptzError, why:
		print ""
		print ""
		print "Failed to create sysroot. " + str(why)
	except KeyboardInterrupt:
		print ""
		print ""
		print "It looks like you have canceled the Sysroot installation. Installation is not complete."
	except BaseException,why:
		print ""
		print ""
		print "Got Base exception ", repr(why), ". Installation failed."
		if raptz.args.debug:
			raise
	except Exception, why:
		print ""
		print ""
		print "Got exception", repr(why), ". Installation failed."
		if raptz.args.debug:
			raise

print ""
