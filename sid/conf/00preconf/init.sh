#!/bin/dash  -e

printf "root\nroot\n" | passwd

[ -c /dev/ttyO0 ] || mknod /dev/ttyO0 c 253 0
[ -c /dev/ttyO1 ] || mknod /dev/ttyO1 c 253 1
[ -c /dev/ttyO2 ] || mknod /dev/ttyO2 c 253 2
