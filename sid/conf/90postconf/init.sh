#!/bin/dash -e

echo "PostConfig"

# Configure network
if ! cat /etc/network/interfaces | grep "auto lo" ; then
	echo "auto lo" >> /etc/network/interfaces
	echo "iface lo inet loopback" >> /etc/network/interfaces
	echo ""
fi
if ! cat /etc/network/interfaces | grep eth0 ; then
cat >>/etc/network/interfaces <<EOF

auto eth0
iface eth0 inet dhcp
   # Do not bring up interface if it was defined on commandline
   pre-up /bin/grep -v -e "ip=dhcp" /proc/cmdline >/dev/null
   pre-up /bin/grep -v -e "ip=[0-9]\+\.[0-9]\+\.[0-9]\+\.[0-9]\+" /proc/cmdline >/dev/null

EOF
fi


if ! cat /root/.bashrc | grep "bash_completion" ; then
cat >>/root/.bashrc <<EOF
if [ -f /etc/bash_completion ] && ! shopt -oq posix; then
	    . /etc/bash_completion
fi
EOF
fi
