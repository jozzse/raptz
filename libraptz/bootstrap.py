import os

class Bootstrap:
	def __init__(self, host):
		self._host = host


	def bootstrap(self):
		# The stage where nothing is mounted
		pass

	def secondstage(self):
		# Here the system is mounted
		pass
	
	def finalize(self):
		conf = self._host.conf()
		listd = conf.sysroot("/etc/apt/sources.list.d")

		if not os.path.isdir(listd):
			os.makedirs(listd)
		for repro in conf.repros():
			listfile = os.path.join(listd, repro.lower() + ".list")
			source = conf.source(repro)
			suite = conf.suite(repro)
			comp = " ".join(conf.components(repro))
			f = open(listfile, "w")
			f.write("deb %s %s %s\n" % (source, suite, comp))
			if conf.addsrcs(repro):
				f.write("deb-src %s %s %s\n" % (source, suite, comp))

