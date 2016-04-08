#! /bin/bash

BUNDLE=$1
PATCHJSON=$2
PREAMBLE=$3 #eg "FEB and GLIBC Patch Bundle : "
SIGNOFFTEAM=$4 # one of LOG_TRANSPORT LOG_ANALYTICS DATA_BROKER ARGUS ALERTING

echo "Enter Gus Password:"
stty -echo
read PASS
stty echo


expect - <<EOF 
set timeout -1
spawn ./dva_create_cases.sh $BUNDLE $PATCHJSON $PREAMBLE $SIGNOFFTEAM
expect password: {
	send "$PASS\r"
	exp_continue
}
EOF
