#!/usr/bin/python

import sys
from subprocess import check_output

class Ui():
	def __init__(self):
		pass
	def progress(self, prog):
		pass
	def part(self):
		pass
	def start(self, name):
		pass
	def done(self):
		pass
	def text(self, text):
		raise # Must be implemented
	def dbg(self, text):
		print
		print "DEBUG: " + text
		print
	def warn(self, text):
		self.text(text)

class UiLog(Ui):
	def start(self, name):
		print "***", name
	def text(self, text):
		print text

class UiTerm(Ui):
	_prog = 0.0
	_parts = 0
	_part = 0
	_name = ""
	_text = ""
	columns = 79
	def __init__(self):
		Ui.__init__(self)

	def progress(self, prog):
		if prog <= 1.0:
			self._prog = prog
	
	def part(self):
		return "%2d/%d" % (self._part, self._parts)
	
	def start(self, name):
		try:
			self.columns = int(check_output(['stty','size']).split()[1])-1
		except:
			pass
		self._name = name
		self._part += 1
		self._prog = 0.0
		return self

	def done(self):
		self._prog = 0.0
		sys.stdout.write("\r\033[K")
		sys.stdout.write("%s:%5.1f%%:%s:Done" % (self.part(), self._prog*100.0, self._name))
		if self._part == self._parts:
			sys.stdout.write("\n")
		sys.stdout.flush()

	def text(self, text):
		self._text = text.strip()
		sys.stdout.write("\r\033[K")
		txt = "%s:%5.1f%%:%s> " % (self.part(), self._prog*100.0, self._name)
		txt += self._text[0:self.columns-len(txt)]
		sys.stdout.write(txt)
		sys.stdout.flush()
		
	def warn(self, text):
		self.text("!!" + text)

