from distutils.core import setup
from subprocess import call

def a():
	m = open("MANIFEST.in", "w")
	if call(["git", "ls-tree", "-r", "--name-only", "master"], stdout=m) != 0:
		print "Could not create MANIFEST.in with git"
		exit(1)

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
	)

