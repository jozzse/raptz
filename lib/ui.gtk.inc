
_error()
{
	echo -n "ERROR: " >> $RAPTZ_LOGFILE
	echo $* >> $RAPTZ_LOGFILE
	echo $*
	zenity --error --text="$*" --no-markup 
	exit 1
}



_log()
{
	echo "***" >> $RAPTZ_LOGFILE
	echo $* >> $RAPTZ_LOGFILE
	tee -a $RAPTZ_LOGFILE | zenity --progress --text "$*" --pulsate --no-cancel --auto-close 
}

_log_num()
{
	TOT=$1
	shift
	echo "*** $TOT" >> $RAPTZ_LOGFILE
	echo $* >> $RAPTZ_LOGFILE
	C=0
	OLD=0
	while read LINE ; do
		echo $LINE >> $RAPTZ_LOGFILE
		let C=$C+1
		P=$(( $C * 100 / $TOT ))
		if (( $OLD != $P )) ; then
			echo "XXX"
			echo "$P"
			echo "$*" 
			OLD=$P
			echo $LINE
		fi
	done | zenity --progress --text "$*" --no-cancel --auto-close 
}
