

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
	STR=".:|:.      "
	P2=0
	OA="."
	OB="."
	OC="."
	OD="."
	OE="."
	OF="."
	OG="."
	OH="."
	while read LINE ; do
		C=$(( $C + 1 ))
		P1=$(( $C / 4 % 8 ))
		if (( $P2 != $P1 )) ; then
			OH=$OG
			OG=$OF
			OF=$OE
			OE=$OD
			OD=$OC
			OC=$OB
			OB=$OA
			OA=${STR:$P1:1}
			P2=$P1
		fi
		printf "\\r"
		echo -n "$OA$OB$OC$OD$OE$OF$OG$OH"
		echo -n "$OA$OB$OC$OD$OE$OF$OG$OH"
		echo -n "$OA$OB$OC$OD$OE$OF$OG$OH"
		echo -n "$OA$OB$OC$OD$OE$OF$OG$OH"
		printf " %10s lines" $C
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
	C=1
	NEXT=1
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
