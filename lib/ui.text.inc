

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
	#    012345678
	STR="<==     "
	STR=$STR$STR
	P2=-1
	while read LINE ; do
		C=$(( $C + 1 ))
		P1=$(( $C / 4 % 8 ))
		if (( $P2 != $P1 )) ; then
			OA=${STR:$P1:8}
		fi
		printf "\\r%10s lines" $C
		echo -n "$OA"
		echo -n "$OA"
		echo -n "$OA"
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
			printf "\\r%10s lines    %3d%%" $C $P
			NEXT=$(( $NEXT + $TOT / 100 ))
		fi
		echo $LINE >> $RAPTZ_LOGFILE
	done
	printf "\\r%10s lines    %3d%%" $C 100
	echo ""
}
