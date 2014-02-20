#!/bin/dash  -e
echo "PreConfig"
export DEBIAN_FRONTEND=noninteractive DEBCONF_NONINTERACTIVE_SEEN=true

debconf-set-selections $1/debconf.cfg

/var/lib/dpkg/info/dash.preinst install
dpkg --configure -a

printf "root\nroot\n" | passwd

[ -c /dev/ttyO0 ] || mknod /dev/ttyO0 c 253 0
[ -c /dev/ttyO1 ] || mknod /dev/ttyO1 c 253 1
[ -c /dev/ttyO2 ] || mknod /dev/ttyO2 c 253 2

apt-get update
