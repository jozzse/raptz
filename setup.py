from distutils.core import setup
from subprocess import call
import os

targets=[]
for td in ["igepv2", "igepv2_sid"]:
	for root, dirs, files in os.walk("igepv2"):
		fs = []
		for f in files:
			fs.append(os.path.join(root, f))
		targets.append(("share/raptz/targets/" + root, fs))

mods=[
	"conf",
	"fileopt",
	"raptz",
	"rargs",
	"setup",
	"tools",
	"ui/rawui",
	"ui/baseui",
	"ui/textui",
	"ui/__init__"
]

setup(name='raptz',
	version='0.1',
	description='Rapid sysroot builder for Debian derivatives',
	author='Jonas Zetteberg',
	author_email='jozz@jozz.se',
	url='http://jozz.no-ip.org/wiki/igep/emdebian/installer/raptz', # Fixme: make site
	py_modules=mods,
	scripts=['raptz.py', 'raptz'],
	data_files=targets
	)

