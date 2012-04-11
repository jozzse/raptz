

_error()
{
	echo -n "ERROR: " >> $RAPTZ_LOGFILE
	echo $* >> $RAPTZ_LOGFILE
	echo ""
	echo -n "ERROR: "
	echo $*
	
	exit 1
}

_log()
{
	echo "***" >> $RAPTZ_LOGFILE
	echo $* >> $RAPTZ_LOGFILE
	echo ""
	echo $*
	C=0
	STR="-/|\\"

	while read LINE ; do
		C=$(( $C + 1 ))
		P=$(( $C % 4 ))
		printf "\\r${STR:$P:1}    %10s lines" $C
		echo $LINE >> $RAPTZ_LOGFILE
	done
	echo ""
}

_log_num()
{
	TOT=$1
	shift
	echo "*** $TOT" >> $RAPTZ_LOGFILE
	echo $* >> $RAPTZ_LOGFILE
	echo ""
	echo $*
	C=0
	NEXT=0
	while read LINE ; do
		C=$(( $C + 1 ))
		if (( $C > $NEXT )) ; then
			P=$(( $C * 100 / $TOT ))
			printf "\\r%3d%% %10d lines" $P $C
			NEXT=$(( $NEXT + $TOT / 100 ))
		fi
		echo $LINE >> $RAPTZ_LOGFILE
	done
	echo ""
}
