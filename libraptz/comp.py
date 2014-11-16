
import os
import select
from subprocess import Popen, PIPE

class Tar:
	_outputs = []
	def __init__(self, host):
		self._host = host

	def add(self, output):
		self._outputs.append(output)

	def write(self):
		inlen=0
		sysroot = self._host.conf.sysroot()
		cmd=["tar", "cf", "-", sysroot] # tar to output
		self._fds = [ o.open() for o in self._outputs]

		p = Popen(cmd, stdout=PIPE)
		while p.poll() == None:
			d = p.stdout.read(select.PIPE_BUF)
			inlen+=len(d)
			for f in self._fds:
				f.write(d)
		p.wait()
		while len(d):
			d = p.stdout.read(select.PIPE_BUF)
			p.stdout.flush()
			inlen+=len(d)
			for f in self._fds:
				f.write(d)
				f.flush()
			if len(d) == 0:
				ok = True
		#print poller.poll(.01)
		print "Wait", inlen
		for f in self._fds:
			f.close()
		for o in self._outputs:
			o.close()

class OutputFile:
	def __init__(self, filename):
		self._filename = filename
		self._fd = os.open(self._filename, os.O_WRONLY | os.O_CREAT)

	def open(self):
		raise

	def close(self):
		os.close(self._fd)

class OutputPipe(OutputFile):
	def __init__(self, filename, prog):
		OutputFile.__init__(self, filename)
		self._prog = prog

	def open(self):
		self._p = Popen([self._prog], stdout=self._fd, stdin=PIPE)
		return self._p.stdin
	
	def close(self):
		self._p.wait()
		OutputFile.close(self)

class Cat(OutputPipe):
	def __init__(self, filename):
		OutputPipe.__init__(self, filename, "cat")

class GZip(OutputPipe):
	def __init__(self, filename):
		OutputPipe.__init__(self, filename, "pigz")

class BZip2(OutputPipe):
	def __init__(self, filename):
		OutputPipe.__init__(self, filename, "bzip2")

class XZ(OutputPipe):
	def __init__(self, filename):
		OutputPipe.__init__(self, filename, "xz")


