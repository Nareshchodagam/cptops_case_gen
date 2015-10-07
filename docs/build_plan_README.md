## Build Plan Examples.

 _Build plan with all na21 ACS servers one by one by majorset-minorset_

	./build_plan.py -c 0000001 -C -G '{"clusters" : "na21" ,"datacenter": "wax" , "roles": "acs", "grouping" : "majorset,minorset", "templateid": "generic_test" }'


 _Build plan with  all na21 acs app and cbatch one by one by majorset minorset_

	./build_plan.py -c 0000001 -C -G '{"clusters" : "na21" ,"datacenter": "wax" , "roles": "acs,app,cbatch", "grouping" : "majorset,minorset", "templateid": "generic_test" }'

 _Build plan with  all na21 acs app and cbatch one by one by majorset minorset applying parallel groups of no more than 12 where possible_

	./build_plan.py -c 0000001 -C -G '{"clusters" : "na21" ,"datacenter": "wax" , "roles": "acs,app,cbatch", "grouping" : "majorset,minorset", "templateid": "generic_test", "maxgroupsize" : 12 }'

 _Build plan with  all na21,cs32,cs33 acs app and cbatch one by one by majorset minorset applying parallel groups of no more than 12 where possible_

	/build_plan.py -c 0000001 -C -G '{"clusters" : "cs32,cs33,na21" ,"datacenter": "wax" , "roles": "acs,app,cbatch", "grouping" : "majorset,minorset", "templateid": "generic_test", "maxgroupsize" : 12 }'

 _Build plan with all na21,cs32,cs33 acs app and cbatch one by one by majorset applying parallel groups of no more than 12 where possible (then by role then by cluster)_

	./build_plan.py -c 0000001 -C -G '{"clusters" : "cs32,cs33,na21" ,"datacenter": "wax" , "roles": "acs,app,cbatch", "grouping" : "majorset", "templateid": "generic_test", "maxgroupsize" : 12 }'
	./build_plan.py -c 0000001 -C -G '{"clusters" : "cs32,cs33,na21" ,"datacenter": "wax" , "roles": "acs,app,cbatch", "grouping" : "role,majorset", "templateid": "generic_test", "maxgroupsize" : 12 }'
	./build_plan.py -c 0000001 -C -G '{"clusters" : "cs32,cs33,na21" ,"datacenter": "wax" , "roles": "acs,app,cbatch", "grouping" : "cluster,role,majorset", "templateid": "generic_test", "maxgroupsize" : 12 }'

 _Build plan using  host filter regex example:_

	./build_plan.py -c 0000001 -C -G '{"clusters" : "cs32,cs33,na21" ,"datacenter": "wax" , "roles": "app,acs,cbatch", "grouping" : "majorset", "templateid": "generic_test", "maxgroupsize" : 12, "hostfilter": 	"^.*1-1" }'

	# get all the 5-* hosts for insights
	./build_plan.py -c 00100209 -C -G '{"clusters" : "INSIGHTS-TYO", "datacenter": "tyo", "roles": "insights_iworker,insights_redis", "grouping" : "majorset", "templateid" : "insights", "maxgroupsize" : 2, "hostfilter": ".*[a-zA-Z]5-*"}'

	newer syntax

	./build_plan.py -c 0000001 -C -G '{"clusters" : "cs32,cs33,na21" ,"datacenter": "wax" , "roles": "mgmt_hub", "grouping" : "majorset", "templateid": "pod-hub_standby", "maxgroupsize" : 12, "regexfilter": 	"failOverStatus=STANDBY" }'

 _Generating plans from a file list of hosts (no IDB)_

	./build_plan.py -l ~/prd_mmxcvrlist  -t mmxcvr_standby -s NONE -c 00092225 -i NONE -r mmxcvr -d prd -a

 _Other build_plan examples._

	./build_plan.py -c 0000001 -C -G '{"clusters" : "cs32,cs33,na21" ,"datacenter": "wax" , "roles": "search,ffx", "grouping" : "majorset,minorset", "templateid" : "generic_test" }'


	./build_plan.py -c 0000001 -C -G '{"clusters" : "cs32,cs33,na21" ,"datacenter": "wax" , "roles": "search", "grouping" : "majorset,minorset" }'

	./build_plan.py -c 0000001 -C -G '{"clusters" : "cs32,cs33,na21" ,"datacenter": "wax" , "roles": "search", "grouping" : "majorset,minorset", "maxgroupsize": 5  }'

	./build_plan.py -c 0000001 -C -G '{"clusters" : "cs32,cs33,na21" ,"datacenter": "wax" , "roles": "ffx", "grouping" : "majorset,minorset", "maxgroupsize" : 2 }'

	./build_plan.py -c 0000001 -C -G '{"clusters" : "cs32,cs33,na21" ,"datacenter": "wax" , "roles": "acs,app,cbatch,search,ffx", "grouping" : "majorset", "maxgroupsize": 50, "templateid" : "generic_test"  }'

 _Also supports non pod hosts with different interpretations of idb metadata_

	./build_plan.py -c 0000001 -C -G '{"clusters" : "WEBX,WEBAUTH-WAS,WEBSTAGE-WAS" ,"datacenter": "was" , "roles": "web,web_auth,web_stage", "grouping" : "majorset", "maxgroupsize": 50, "templateid" : "web.chi-was.linux"  }'

	./build_plan.py -c 0000001 -C -G '{"clusters" : "AJNA-WAS-SP1,AJNA-WAS-SP2,AJNA-WAS-SP3,AJNA-WAS-SP1" ,"datacenter": "was" , "roles": "mmdcs,mmrelay,mmxcvr,mmmbus,mmrs", "templateid": "ajna_all", "grouping": "cluster,role,majorset", "maxgroupsize": 10}'



setup:
==================
On some machines (particularly macs for some reason) you will need to install the corresponding java cryptography extension (JCE)

_Download JCE 6 7 or 8 depending on the version of java you are running_

	http://www.oracle.com/technetwork/java/javase/downloads/jce8-download-2133166.html

_Find the security directory for the jre that you are using eg on mac it will be here as you are forced to use jdk for command line:_

	/Library/Java/JavaVirtualMachines/jdk1.8.0_45.jdk/Contents/Home/jre/lib/security/

_replace the following files in this directory with those from the JCE download_
