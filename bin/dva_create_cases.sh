#! /bin/bash

BUNDLE=$1
PATCHJSON=$2
PREAMBLE=$3 #eg "FEB and GLIBC Patch Bundle : "
OTHER="-T"
EXCLUDE='../hostlists/dva_canary'
FILE_SPL_SWI_CRZ='../hostlists/file_spl_swi_crz'
FILE_SPL_WEB_CRZ='../hostlists/file_spl_web_crz'
FILE_SPL_API_CRZ='../hostlists/file_spl_api_crz'
FILE_SPL_DEP_CRZ='../hostlists/file_spl_dep_crz'
FILE_SPL_IDX_CRZ='../hostlists/file_spl_idx_crz'
FILE_SPL_IDX_CRZ_IDB='../hostlists/file_spl_idx_crz_idb'


function create_case {

SUBJECT=$1
DC=$2
DCUP="$(echo $DC | awk '{print toupper($0)}')"

/usr/local/bin/python gus_cases.py -T change -f ../templates/$PATCHJSON -s "$SUBJECT" -k ../templates/6u6-plan.json -l ../output/summarylist.txt -D $DCUP -i ../output/plan_implementation.txt --infra "Supporting Infrastructure" 
}

function build_case {

DC=$1
ROLE=$2
PREAMBLE=$3
CTYPE=$4
STATUS=$5
GROUPSIZE=$6
GROUPING=$7
TEMPLATEID=$8
if [ -z "$TEMPLATEID" ]; then TEMPLATEID=$ROLE; fi

./build_plan.py -c 0000001 -C -G '{"clusterTypes" : "'$CTYPE'" ,"datacenter": "'$DC'", "roles": "'$ROLE'", "grouping": "'$GROUPING'", "templateid" : "'$TEMPLATEID'",  "maxgroupsize": '$GROUPSIZE', "ho_opstat" : "'$STATUS'" }'  $OTHER --exclude $EXCLUDE --bundle $BUNDLE || exit 1

SUBJECT="$PREAMBLE $DC $ROLE PROD"
create_case "$SUBJECT" $DC

}

function build_case_hostlist {

DC=$1
ROLE=$2
PREAMBLE=$3
HOSTLIST=$4
GROUPSIZE=$5
GROUPING=$6
TEMPLATEID=$7
if [ -z "$TEMPLATEID" ]; then TEMPLATEID=$ROLE; fi

./build_plan.py -l $HOSTLIST -x -M $GROUPING --gsize $GROUPSIZE --bundle $BUNDLE -t $TEMPLATEID $EXTRA || exit 1

SUBJECT="$PREAMBLE $DC $ROLE PROD"
create_case "$SUBJECT" $DC

}

function build_case_hostlist_idb {

DC=$1
ROLE=$2
PREAMBLE=$3
HOSTLIST=$4
GROUPSIZE=$5
GROUPING=$6
TEMPLATEID=$7
if [ -z "$TEMPLATEID" ]; then TEMPLATEID=$ROLE; fi


./build_plan.py -l $HOSTLIST -M $GROUPING --gsize $GROUPSIZE --bundle $BUNDLE -t $TEMPLATEID $EXTRA || exit 1


SUBJECT="$PREAMBLE $DC $ROLE PROD"
create_case "$SUBJECT" $DC
}

function build_case_extra {

#this builds case dynamically looking up template and takes failoverstatus as well

DC=$1
ROLE=$2
PREAMBLE=$3
FOSTAT=$4
DRSTAT=$5


if [ $DRSTAT == 'True' ]; then PRODSTAT=DR; else PRODSTAT=PROD; fi

DCUP="$(echo $DC | awk '{print toupper($0)}')"
MYSUBJECT=$(echo "$PREAMBLE $ROLE $DC $FOSTAT $PRODSTAT" |  tr 'a-z' 'A-Z')
echo "TITLE will be $MYSUBJECT"
./build_plan.py -c 0000002 -C -G '{"clusterTypes" : "POD" ,"datacenter": "'$DC'", "dr" : "'$DRSTAT'" ,"grouping": "role", "maxgroupsize": 8 , "regexfilter" : "failOverStatus='$FOSTAT'", "roles" : "'$ROLE'" }' --exclude /Users/dsheehan/dva_canary --bundle $BUNDLE || exit 1

/usr/local/bin/python gus_cases.py -T change -f ../templates/$PATCHJSON -s "$MYSUBJECT" -k ../templates/6u6-plan.json -l ../output/summarylist.txt -D $DCUP -i ../output/plan_implementation.txt --infra "Supporting Infrastructure"

}

DC=crz

ROLE=mandm-splunk-api
build_case_hostlist $DC $ROLE "$PREAMBLE" $FILE_SPL_API_CRZ 1 role $ROLE

ROLE=mandm-splunk-deployer
build_case_hostlist $DC $ROLE "$PREAMBLE" $FILE_SPL_DEP_CRZ 1 role $ROLE

ROLE=mandm-splunk-idxr
build_case_hostlist $DC $ROLE "$PREAMBLE NON AFW" $FILE_SPL_IDX_CRZ 15 role $ROLE

ROLE=mandm-splunk-idxr
build_case_hostlist $DC $ROLE "$PREAMBLE AFW" $FILE_SPL_IDX_CRZ_IDB 15 role $ROLE

ROLE=mandm-splunk-web
build_case_hostlist $DC $ROLE "$PREAMBLE" $FILE_SPL_WEB_CRZ 1 role $ROLE

DC="asg,sjl,tyo,chi,was,lon,dfw,phx,frf"
ROLE=log_hub
CTYPE=HUB
STATUS=ACTIVE
#
build_case $DC $ROLE "$PREAMBLE" $CTYPE $STATUS 1 role
#
ROLE=mmxcvr
CTYPE=AJNA
STATUS=ACTIVE
DC="sfz"
#
build_case $DC $ROLE "$PREAMBLE" $CTYPE $STATUS 1 majorset,minorset
#
ROLE=mmmbus
CTYPE=AJNA
STATUS=ACTIVE
DC="sfz"
#
build_case $DC $ROLE "$PREAMBLE" $CTYPE $STATUS 1 majorset,minorset mmmbus_SFZ
#
#
CTYPE=AJNA
ROLE=mmdcs
STATUS=ACTIVE
for DC in asg sjl tyo chi was lon dfw phx frf
do
   echo "$DC $ROLE $PREAMBLE $CTYPE"
   build_case $DC $ROLE "$PREAMBLE" $CTYPE $STATUS 1 majorset,minorset
done
#
#
CTYPE=AJNA
ROLE=mmrs
STATUS=ACTIVE
for DC in asg sjl tyo chi was lon dfw phx frf
do
   echo "$DC $ROLE $PREAMBLE $CTYPE"
   build_case $DC $ROLE "$PREAMBLE" $CTYPE $STATUS 1 majorset,minorset
done


CTYPE=AJNA
ROLE=mmrelay
STATUS=ACTIVE

for DC in asg sjl tyo chi was lon dfw phx frf
do
   echo "$DC $ROLE $PREAMBLE $CTYPE"
   build_case $DC $ROLE "$PREAMBLE" $CTYPE $STATUS 1 majorset,minorset
done
#
CTYPE=SMARTS
ROLE=smarts
STATUS=ACTIVE,PRE_PRODUCTION,PROVISIONING
for DC in asg sjl tyo chi was lon dfw phx frf
do
   echo "$DC $ROLE $PREAMBLE $CTYPE"
   build_case $DC $ROLE "$PREAMBLE" $CTYPE $STATUS 1 majorset,minorset
done

CTYPE=SPLUNK-IDX
ROLE=mandm-splunk-switch
STATUS=ACTIVE
for DC in asg sjl tyo chi was lon dfw phx frf
do
   echo "$DC $ROLE $PREAMBLE $CTYPE"
   build_case $DC $ROLE "$PREAMBLE" $CTYPE $STATUS 10 role
done


CTYPE=POD
ROLE=mgmt_hub

for DC in chi was lon dfw phx frf asg sjl
do
   build_case_extra $DC $ROLE "$PREAMBLE" STANDBY False 
   build_case_extra $DC $ROLE "$PREAMBLE" PRIMARY False
   build_case_extra $DC $ROLE "$PREAMBLE" STANDBY True 
   build_case_extra $DC $ROLE "$PREAMBLE" PRIMARY True
done
#no DR in TYO
build_case_extra tyo $ROLE "$PREAMBLE" STANDBY False 
build_case_extra tyo $ROLE "$PREAMBLE" PRIMARY False



