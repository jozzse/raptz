
import os
import os.path
import tools
import subprocess
import tempfile


class FileOpt():
	def __init__(self, tools, ui):
		self.tools = tools
		self.ui = ui

	def mk_cpio(self, inpath, cpiofile):
		if inpath.endswith("/"):
			inpath = inpath[:-1]
		files = self.tools.files(inpath, topdown=True)
		self.ui.start("Make " + cpiofile + "(cpio)", len(files))
		l = len(inpath)
		f = ["".join([".", fl[l:], "\n"]) for fl in files]
		fd=open(cpiofile, "wb", 0644)
		p = subprocess.Popen(["cpio", "-o"], 
			cwd=inpath,
		    stdin=subprocess.PIPE,
			stderr=subprocess.PIPE,
			stdout=fd)
		for ff in f:
			p.stdin.write(ff)
			self.ui.line(ff)
		p.stdin.close()
		p.wait()
		self.ui.stop()
	
	def ext_cpio(self, cpiofile, outpath):
		self.ui.start("Exctract " + cpiofile + "(cpio)")
		fd=open(cpiofile, "rb")
		p = subprocess.Popen(["cpio", "--verbose", "-i"],
			cwd=outpath,
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT,
			stdin=fd)
		while p.poll() == None:
			self.ui.line(p.stdout.readline())
		p.wait()
		fd.close()
		self.ui.stop()
		

	def mk_jffs2(self, inpath, jffs2file, jffs2ext=""):
		self.ui.start(jffs2file + "(jffs2)")
		self.ui.line("Creating " + jffs2file + " Ext:" + jffs2ext)
		self.tools.run("mkfs.jffs2", 
			"-r", inpath,
			"-p", "-l", "-n" ,"-e", "128",
			"-o", jffs2file, *jffs2ext.split())
		self.ui.stop()

	def mk_ext3(self, inpath, ext3file, mkfs, extargs="", cpiofile=""):
		files = self.tools.files(inpath, topdown=True)
		if mkfs:
			self.ui.start("Mkfs")
			if not self.tools.run("mkfs.ext3", *" ".join([extargs, ext3file]).split()):
				print "Could not create ext3"
				return False
			self.ui.stop()
		
		mp = tempfile.mkdtemp(dir="/tmp")
		self.ui.start("Mount(" + mp + ")")
		self.tools.mount(ext3file, mp, options="loop")
		self.ui.stop()
		
		if cpiofile:
			try:
				self.ext_cpio(cpiofile, mp);
			except:
				print "Exception!"
				print "Trying to unmount", mp, " (this might take a while)"
				self.tools.umount(mp)
				raise
		else:			
			tmpfile = tempfile.mktemp()
			try:
				self.mk_cpio(inpath, tmpfile)
				self.ext_cpio(tmpfile, mp);
			except:
				print "Exception!"
				print "Trying to remove tmpfile", tmpfile
				os.unlink(tmpfile)
				print "Trying to unmount", mp, " (this might take a while)"
				self.tools.umount(mp)
				raise
			os.unlink(tmpfile)
			
		self.ui.start("Umount(" + mp + ")")
		self.tools.umount(mp)
		self.ui.stop()
		return True


