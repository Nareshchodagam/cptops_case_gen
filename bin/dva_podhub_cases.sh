#! /bin/bash

BUNDLE=$1

function build_case {

DC=$1
ROLE=$2
PREAMBLE=$3
FOSTAT=$4
DRSTAT=$5


if [ $DRSTAT == 'True' ]; then PRODSTAT=DR; else PRODSTAT=PROD; fi

DCUP="$(echo $DC | awk '{print toupper($0)}')"
MYSUBJECT=$(echo "$PREAMBLE $ROLE $DC $FOSTAT $PRODSTAT" |  tr 'a-z' 'A-Z')
echo "TITLE will be $MYSUBJECT"
./build_plan.py -c 0000002 -C -G '{"clusterTypes" : "POD" ,"datacenter": "'$DC'", "dr" : "'$DRSTAT'" ,"grouping": "role", "maxgroupsize": 8 , "regexfilter" : "failOverStatus='$FOSTAT'", "roles" : "'$ROLE'" }' --exclude /Users/dsheehan/dva_canary --bundle $BUNDLE

/usr/local/bin/python gus_cases.py -T change -f ../templates/feb-patch.json -s "$MYSUBJECT" -k ../templates/6u6-plan.json -l ../output/summarylist.txt -D $DCUP -i ../output/plan_implementation.txt

}

CTYPE=POD
ROLE=mgmt_hub
PREAMBLE="FEB and GLIBC Patch Bundle : "

for DC in chi was lon dfw phx frf asg sjl
do
   build_case $DC $ROLE "$PREAMBLE" STANDBY False 
   build_case $DC $ROLE "$PREAMBLE" PRIMARY False
   build_case $DC $ROLE "$PREAMBLE" STANDBY True 
   build_case $DC $ROLE "$PREAMBLE" PRIMARY True
done
#no DR in TYO
build_case tyo $ROLE "$PREAMBLE" STANDBY False 
build_case tyo $ROLE "$PREAMBLE" PRIMARY False




