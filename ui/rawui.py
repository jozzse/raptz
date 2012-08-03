
from baseui import BaseUI

class UI(BaseUI):
	def __init__(self, logfile):
		BaseUI.__init__(self, logfile)

	def start(self, text, lines=None):
		BaseUI.start(self, text, lines)
		print "*** Running: " + text,
		if lines:
			print "(" + str(lines) + " lines)"
		else:
			print ""
		
	def stop(self):
		BaseUI.stop(self)
		print "*** Done"

	def line(self, text):
		BaseUI.line(self, text)
		print text

	def message(self, text):
		BaseUI.message(self, text)
		print "*** Message: " + text
