import os
from config import config

class Bootstrap:
	def __init__(self):
		pass

	def bootstrap(self):
		# The stage where nothing is mounted
		pass

	def secondstage(self):
		# Here the system is mounted
		pass
	
	def finalize(self):
		listd = config.sysroot("/etc/apt/sources.list.d")

		if not os.path.isdir(listd):
			os.makedirs(listd)
		for repro in config.repros():
			listfile = os.path.join(listd, repro.lower() + ".list")
			source = config.source(repro)
			suite = config.suite(repro)
			comp = " ".join(config.components(repro))
			f = open(listfile, "w")
			f.write("deb %s %s %s\n" % (source, suite, comp))
			if config.addsrcs(repro):
				f.write("deb-src %s %s %s\n" % (source, suite, comp))

