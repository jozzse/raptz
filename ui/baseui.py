
class BaseUI():
	def __init__(self, logfile):
		self.logfile = open(logfile, "w", 0644)

	def set_lines(self, lines):
		pass

	def start(self, text, lines=None):
		self.logfile.write("*** " + text + " ***\n")
		self.logfile.flush()

	def stop(self):
		pass

	def line(self, text):
		self.logfile.write(text + "\n")
		self.logfile.flush()
		
	
	def message(self, text):
		self.logfile.write(">>> " + text + "\n")
		self.logfile.flush()
