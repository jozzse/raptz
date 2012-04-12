
_common_root()
{
	# Make sure we are root
	if [ "$(whoami)" != "root" ]; then
		sudo $0 $@
		exit
	fi
}


# Set variables if not already set

[ -n "$RAPTZ_NAME" ] || export RAPTZ_NAME=default
# if raptz name is a link, then read the link
[ -h "$RAPTZ_NAME" ] && export RAPTZ_NAME=$(readlink $RAPTZ_NAME)

[ -n "$RAPTZ_CLEAN" ]   || export RAPTZ_CLEAN=0
[ -n "$RAPTZ_FORCE" ]   || export RAPTZ_FORCE=0
[ -n "$RAPTZ_SKIP" ]    || export RAPTZ_SKIP=0
[ -n "$RAPTZ_LOGFILE" ] || export RAPTZ_LOGFILE=$PWD/raptz.log
[ -n "$RAPTZ_UI" ]      || export RAPTZ_UI=text
[ -n "$RAPTZ_SYSROOT" ] || export RAPTZ_SYSROOT=/opt/$RAPTZ_NAME
[ -n "$RAPTZ_ADD_DEV" ] || export RAPTZ_ADD_DEV=0
[ -n "$RAPTZ_DEV" ] 	|| export RAPTZ_DEV=
[ -n "$RAPTZ_IMAGE" ]   || export RAPTZ_IMAGE=

_common_help()
{
	echo "Common Options:"
	echo "  -n <name> Change configuration name (default default)"
	echo "  -u <name> Set RAPTZ_UI (default: text, avalible: gtk, dialog, text, raw, quiet)"
	echo "  -r <path> Use specific sysroot path"
	echo "  -h        Show this help and exit"
}

# Get Options
# $1 defines avalible options in getopts way.
# The options n,u and h is always and should not be specified
# Use opts "-" if no aditional ops are needed 
# Call: _common_opts [opts] $@
_common_opts()
{
	ARGS="r:n:u:h"
	if [ "$1" != "-" ] ; then
		ARGS=$ARGS$1
	fi
	shift
	while getopts $ARGS OPT
	do
		case $OPT in
			c)
				RAPTZ_CLEAN=1
				;;
			f)
				RAPTZ_FORCE=1
				;;
			s)
				RAPTZ_SKIP=1
				;;
			D)
				RAPTZ_ADD_DEV=1
				;;
			d)
				RAPTZ_DEV=$OPTARG
				;;
			n)
				RAPTZ_NAME=$OPTARG
				RAPTZ_SYSROOT=/opt/$RAPTZ_NAME
				;;
			i)
				RAPTZ_IMAGE=$OPTARG
				;;
			r)
				RAPTZ_SYSROOT=$OPTARG
				;;
			u)
				RAPTZ_UI=$OPTARG
				;;
			h)
				_help
				exit
				;;
		esac
	done
	shift $((OPTIND-1))
}

_error()
{
	echo $*
	exit 1
}

_common_ui()
{
	if ! [ -f lib/ui.$RAPTZ_UI.inc ] ; then
		echo "RAPTZ_UI not found!, using text"
		RAPTZ_UI=text
	fi
	. lib/ui.$RAPTZ_UI.inc

	# Always check for dependencies
	[ -x /usr/sbin/multistrap ]     || _error "multistrap not found"
	[ -x /usr/bin/qemu-arm-static ] || _error "qemu-arm-static not found"
}

_common_chk_mount()
{
	[ -z "$RAPTZ_NAME" ] && _error "SYSROOT is $RAPTZ_NAME"
	[ -z "$RAPTZ_SYSROOT" ] && _error "SYSROOT is $RAPTZ_SYSROOT"
	[ -d "$RAPTZ_SYSROOT" ] || mkdir -p $RAPTZ_SYSROOT
	
	mount | grep $RAPTZ_SYSROOT/proc && umount $RAPTZ_SYSROOT/proc
	mount | grep $RAPTZ_SYSROOT/dev/pts && umount $RAPTZ_SYSROOT/dev/pts
	mount | grep $RAPTZ_SYSROOT/dev && umount $RAPTZ_SYSROOT/dev
	
	mount | grep $RAPTZ_SYSROOT/proc && _error "Could not unmount proc"
	mount | grep $RAPTZ_SYSROOT/dev/pts && _error "Could not unmount dev/pts"
	mount | grep $RAPTZ_SYSROOT/dev && _error "Could not unmount dev"
	return 0	
}

