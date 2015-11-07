from distutils.core import setup
if __name__=="__main__":
	from subprocess import call
	import os

	targets=[]
	for td in ["sid"]:
		for root, dirs, files in os.walk(td):
			fs = []
			for f in files:
				fs.append(os.path.join(root, f))
			targets.append(("share/raptz/targets/" + root, fs))

	setup(name='raptz',
		version='0.1',
		description='Rapid rootfs builder for Debian derivatives',
		author='Jonas Zetteberg',
		author_email='jozz@jozz.se',
		url='http://jozz.no-ip.org/wiki/igep/emdebian/installer/raptz', # Fixme: make site
		scripts=['raptz'],
		packages=('libraptz',),
		data_files=targets
		)

