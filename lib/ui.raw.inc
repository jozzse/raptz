

_error()
{
	echo ""
	echo -n "ERROR: "
	echo $*
	exit 1
}

_log()
{
	echo $*
	cat
}

_log_num()
{
	TOT=$1
	shift
	echo $*
	cat
}
