
if ! which dialog ; then
	echo "Please make sure dialog is in your path"
	exit 1
fi

UI_W=$(tput cols)
[ -z "$UI_W" ] && UI_W=80
UI_H=$(tput lines)
[ -z "$UI_H" ] && UI_H=80

let UI_H="$UI_H - 5"
let UI_W="$UI_W - 5"
echo $UI_H $UI_W

_error()
{
	echo -n "ERROR: " >> $RAPTZ_LOGFILE
	echo $* >> $RAPTZ_LOGFILE
	dialog --msgbox "ERROR:\n\n$*" $UI_H $UI_W --backtitle ERROR 
	exit 1
}


_log()
{
	echo "***" >> $RAPTZ_LOGFILE
	echo $* >> $RAPTZ_LOGFILE
	tee -a $RAPTZ_LOGFILE | dialog --progressbox "$*" $UI_H $UI_W
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
	done | dialog --gauge "$*" 8 $UI_W 0 
}
