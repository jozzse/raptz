
import os
import select
from subprocess import Popen, PIPE

class InFile:
	_outputs = []
	def __init__(self, sysroot):
		self._sysroot = sysroot

	def add(self, output):
		self._outputs.append(output)

	def compress(self):
		raise

	def write(self, cmd, sin=None):
		inlen=0
		self._fds = [ o.open() for o in self._outputs]

		stdin=None
		selin=[]
		if sin:
			stdin=PIPE
		p = Popen(cmd, stdout=PIPE, stdin=stdin)

		selout=[p.stdout.fileno()]
		if sin:
			selin =[p.stdin.fileno()]
		while p.poll() == None:
			ret = select.select(selout, selin, [], 1)
			if ret[1] != []:
				w = sin()
				if w == None:
					p.stdin.close()
					selin=[]
					continue
				p.stdin.write(w+"\n")
			elif ret[0] != []:
				d = p.stdout.read(select.PIPE_BUF)
				inlen+=len(d)
				for f in self._fds:
					f.write(d)
		p.wait()
		d="A"
		while len(d):
			d = p.stdout.read(select.PIPE_BUF)
			inlen+=len(d)
			for f in self._fds:
				f.write(d)
				f.flush()
		#print poller.poll(.01)
		print "Archive is", inlen
		for f in self._fds:
			f.close()
		for o in self._outputs:
			o.close()

class Cpio(InFile):
	def compress(self):
		self._flist = []
		sysroot = self._sysroot
		sl = len(sysroot)+1
		for root, dirs, files in os.walk(sysroot):
			for d in dirs:
				self._flist.append(os.path.join(root, d)[sl:])
			for f in files:
				self._flist.append(os.path.join(root, f)[sl:])
		cwd = os.getcwd()
		os.chdir(sysroot)
		cmd=["cpio", "-o"]
		ret = self.write(cmd, self._stdin)
		os.chdir(cwd)
		return ret

	def _stdin(self):
		if self._flist == []:
			return None
		return self._flist.pop(0)

class Tar(InFile):
	def compress(self):
		sysroot = self._sysroot
		cmd=["tar", "-c", "-f", "-", "-C",  sysroot, "."] # tar to output
		return self.write(cmd)

class UnTar:
	def __init__(self, path):
		self._path = path

	def open(self):
		if not os.path.isdir(self._path):
			os.mkdir(self._path)
		cmd = ["tar", "-C", self._path, "-x", "-f", "-"]
		self._p = Popen(cmd, stdin=PIPE)
		return self._p.stdin

	def close(self):
		self._p.wait()


class OutputFile:
	def __init__(self, filename):
		self._filename = filename
		self._file = open(self._filename, "wb")

	def open(self):
		raise

	def close(self):
		self._file.close()

class OutputPipe(OutputFile):
	def __init__(self, filename):
		OutputFile.__init__(self, filename)

	def open(self):
		self._p = Popen(self._prog, stdout=self._file.fileno(), stdin=PIPE)
		return self._p.stdin

	def close(self):
		self._p.wait()
		OutputFile.close(self)

class Cat(OutputPipe):
	_prog=["cat"]


class GZip(OutputPipe):
	_prog=["pigz", "-c"]

class BZip2(OutputPipe):
	_prog=["pbzip2"]

class XZ(OutputPipe):
	_prog=["pxz"]

