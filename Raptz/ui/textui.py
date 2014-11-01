
import sys
from baseui import BaseUI
import time as ttt
from time import time
import os
class Group():
	def __init__(self, label="Init", subgroup=0, lines=0):
		"""
		Initialize a Group as a top most child
		"""
		try:
			self.columns = int(os.popen('stty size', 'r').read().split()[1])
		except:
			self.columns = 79
		self.label = label
		self.subgroup = subgroup
		self.totlines = lines
		self.child = None
		self.lines = lines
		self.cline = 0
		self.time = 0.0

	def set_lines(self, lines):
		if self.child:
			self.child.set_lines(lines)
		else:
			self.lines = lines
			self.cline = 0

	def line(self, text, pre=""):
		"""
		Top most child will print the text
		"""
		if self.child:
			return self.child.line(text, pre + self.label + ":")
		self.cline = self.cline + 1
		t = time()
		if t - self.time < 1.0/30:
			return
		self.time = t
		sys.stdout.write("\r\033[K")
		sys.stdout.flush()
		pre = pre + self.label
		if self.lines:
			pre+="(%3d%%)" % (self.cline * 100 / self.lines)
		pre += "> " 
		pre += text[0:self.columns-len(pre)].strip() 
		sys.stdout.write(pre)
		sys.stdout.flush()

	def done(self, pre=""):
		"""
		Removes the top most child. If a child returns True it wants to be removed
		"""
		if not self.child:
			return True
		if self.child.done(pre + self.label + ":"):
			self.child = None
		sys.stdout.write("\r\033[K")
		sys.stdout.flush()
		return False

	def sub(self, text, lines):
		"""
		Generates a new child and returns the new child
		"""
		if self.child:
			return self.child.sub(text, lines)
		self.child = Group(text, self.subgroup + 1, lines)
		return self.child

class UI(BaseUI):
	def __init__(self, logfile):
		BaseUI.__init__(self, logfile)
		self.group = None

	def set_lines(self, lines):
		self.group.set_lines(lines)

	def start(self, text, lines=None):
		BaseUI.start(self, text, lines)
		if self.group:
			self.group.sub(text, lines)
		else:
			self.group = Group(text, 0, lines)

	def stop(self):
		BaseUI.stop(self)
		if not self.group:
			print "No print group!"
			raise
		if self.group.done():
			self.group = None

	def line(self, text):
		BaseUI.line(self, text)
		self.group.line(text)

	def message(self, text):
		BaseUI.message(self, text)
		print ""
		print text
