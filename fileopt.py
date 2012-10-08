
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
		if not os.path.isdir(outpath):
			os.mkdir(outpath)
			if not os.path.isdir(outpath):
				self.ui.message("Could not create " + outpath)
				self.ui.stop()
				return False
		fd=open(cpiofile, "rb")
		p = subprocess.Popen(["cpio", "--verbose", "-i"],
			cwd=outpath,
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT,
			stdin=fd)
		while p.poll() == None:
			self.ui.line(p.stdout.readline())
		fd.close()
		p.wait()
		self.ui.stop()
		return True

	def mk_targz(self, inpath, tarfile):
		files = self.tools.files(inpath, topdown=True)
		self.ui.start("Make " + tarfile + "(tar.gz)", len(files))
		p = subprocess.Popen(["tar", 
				"-c",
				"-v",
				"-C", inpath,
				"-z", 
				"-f", tarfile,
				"."],
			stdout=subprocess.PIPE)
		while p.poll() == None:
			self.ui.line(p.stdout.readline())
		p.wait()
		self.ui.stop()
	
	def ext_targz(self, tarfile, outpath):
		self.ui.start("Extract " + tarfile + "(tar.gz)")
		if not os.path.isdir(outpath):
			os.mkdir(outpath)
			if not os.path.isdir(outpath):
				self.ui.message("Could not create " + outpath)
				self.ui.stop()
				return False
		p = subprocess.Popen(["tar", 
				"-x",
				"-v",
				"-C", outpath,
				"-z",
				"-f", tarfile],
			stdout=subprocess.PIPE)
		while p.poll() == None:
			self.ui.line(p.stdout.readline())
		p.wait()
		self.ui.stop()
		return True

	def mk_jffs2(self, inpath, jffs2file, jffs2ext=""):
		self.ui.start(jffs2file + "(jffs2)")
		self.ui.line("Creating " + jffs2file + " Ext:" + jffs2ext)
		self.tools.run("mkfs.jffs2", 
			"-r", inpath,
			"-p", "-l", "-n" ,"-e", "128",
			"-o", jffs2file, *jffs2ext.split())
		self.ui.stop()

	def mk_ext3(self, inpath, ext3file, mkfs, extargs=""):
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
		self.ui.start("Move system", len(files))
		psrc = subprocess.Popen(["tar", 
				"-c",
				"-C", inpath,
				"-z", 
				"-f", "-",
				"."],
			stdout=subprocess.PIPE)
		pdst = subprocess.Popen(["tar", 
				"-x",
				"-v",
				"-C", mp,
				"-z",
				"-f", "-"],
			stdin=psrc.stdout,
			stdout=subprocess.PIPE)
		while pdst.poll() == None:
			self.ui.line(pdst.stdout.readline())
		psrc.wait()
		pdst.wait()
		self.ui.stop()
		
		self.ui.start("Umount(" + mp + ")")
		self.tools.umount(mp)
		self.ui.stop()
		return True


