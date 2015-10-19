#! /usr/bin/python

import sys
import os
sys.path.append(os.getcwd() + '/../bin')



from build_plan import *



	
CHIPODS='NA7,NA11,NA12,NA14,CS9,CS10,CS11,SR2,NA4,NA16,EU0,CS17,CS17,CS17,CS18,CS20,NA17,NA18,NA22,NA23,NA41,CS21,CS22,CS26,NA24,NA26,NA31,CS41,CS43,CS44'
WASPODS='NA9,NA10,CS7,CS8,CS14,SR1,GS0,NA2,NA13,NA15,CS15,CS16,CS19,NA5,NA19,NA20,CS23,CS24,CS25,CS27,CS28,NA5,NA19,NA20,CS23,CS24,CS25,CS27,CS28'

testlist= [	
		
	{ "clusters" : "na21" ,"datacenter": "wax" , "roles": "acs", "grouping" : "majorset,minorset", "templateid": "generic_test" },

	{ "clusters" : "na21" ,"datacenter": "wax" , "roles": "acs,app,cbatch", "grouping" : "majorset,minorset", "templateid": "generic_test" },

	{ "clusters" : "na21" ,"datacenter": "wax" , "roles": "acs,app,cbatch", "grouping" : "majorset,minorset", "templateid": "generic_test", "maxgroupsize" : 12 },

	{ "clusters" : "cs32,cs33,na21" ,"datacenter": "wax" , "roles": "acs,app,cbatch", "grouping" : "majorset,minorset", "templateid": "generic_test", "maxgroupsize" : 12 },

	{ "clusters" : "cs32,cs33,na21" ,"datacenter": "wax" , "roles": "acs,app,cbatch", "grouping" : "majorset", "templateid": "generic_test", "maxgroupsize" : 12 },

	{ "clusters" : "cs32,cs33,na21" ,"datacenter": "wax" , "roles": "acs,app,cbatch", "grouping" : "role,majorset", "templateid": "generic_test", "maxgroupsize" : 12 },

	{ "clusters" : "cs32,cs33,na21" ,"datacenter": "wax" , "roles": "acs,app,cbatch", "grouping" : "cluster,role,majorset", "templateid": "generic_test", "maxgroupsize" : 12 },

	{ "clusters" : "cs32,cs33,na21" ,"datacenter": "wax" , "roles": "app,acs,cbatch", "grouping" : "majorset", "templateid": "generic_test", "maxgroupsize" : 12, "hostfilter": 	"^.*1-1" },

	{ "clusters" : "INSIGHTS-TYO", "datacenter": "tyo", "roles": "insights_iworker,insights_redis", "grouping" : "majorset", "templateid" : "insights", "maxgroupsize" : 2, "hostfilter": ".*[a-zA-Z]5-*"},

	{ "clusters" : "cs32,cs33,na21" ,"datacenter": "wax" , "roles": "mgmt_hub", "grouping" : "majorset", "templateid": "pod-hub_standby", "maxgroupsize" : 12, "regexfilter": 	"failOverStatus=STANDBY" },


	{ "clusters" : "cs32,cs33,na21" ,"datacenter": "wax" , "roles": "search,ffx", "grouping" : "majorset,minorset", "templateid" : "generic_test" },

	{ "clusters" : "cs32,cs33,na21" ,"datacenter": "wax" , "roles": "search", "grouping" : "majorset,minorset" },

	{ "clusters" : "cs32,cs33,na21" ,"datacenter": "wax" , "roles": "search", "grouping" : "majorset,minorset", "maxgroupsize": 5  },

	{ "clusters" : "cs32,cs33,na21" ,"datacenter": "wax" , "roles": "ffx", "grouping" : "majorset,minorset", "maxgroupsize" : 2 },

	{ "clusters" : "cs32,cs33,na21" ,"datacenter": "wax" , "roles": "acs,app,cbatch,search,ffx", "grouping" : "majorset", "maxgroupsize": 50, "templateid" : "generic_test"  },

	{ "clusters" : "WEBX,WEBAUTH-WAS,WEBSTAGE-WAS" ,"datacenter": "was" , "roles": "web,web_auth,web_stage", "grouping" : "majorset", "maxgroupsize": 50, "templateid" : "web.chi-was.linux"  },

	{ "clusters" : "AJNA-WAS-SP1,AJNA-WAS-SP2,AJNA-WAS-SP3,AJNA-WAS-SP1" ,"datacenter": "was" , "roles": "mmdcs,mmrelay,mmxcvr,mmmbus,mmrs", "templateid": "ajna_all", "grouping": "cluster,role,majorset", "maxgroupsize": 10},

	{ "clusters" : WASPODS,"datacenter": "chi" , "roles": "proxy", "grouping" : "majorset,minorset", "maxgroupsize": 5, "templateid" : "siteproxy_standby.linux", "dr": "True"  },

	{ "clusters" : CHIPODS,"datacenter": "chi" , "roles": "proxy", "grouping" : "majorset,minorset", "maxgroupsize": 5, "templateid" : "siteproxy.linux" },

	{ "clusters" : CHIPODS,"datacenter": "chi" , "roles": "mnds,dnds", "grouping" : "majorset,minorset", "maxgroupsize": 4, "templateid" : "hbase.linux", "dr": "False"  },

	{ "clusters" : CHIPODS,"datacenter": "chi" , "roles": "mnds,dnds", "grouping" : "majorset,minorset", "maxgroupsize": 14, "templateid" : "hbase.linux" },

	{ "clusters" : WASPODS ,"datacenter": "chi" , "roles": "search", "grouping" : "majorset,minorset", "maxgroupsize": 4, "templateid" : "search", "dr": "True"  },

	{ "clusters" : CHIPODS ,"datacenter": "chi" , "roles": "search", "grouping" : "majorset,minorset", "maxgroupsize": 4, "templateid" : "search" },

	{ "clusters" : CHIPODS ,"datacenter": "was" , "roles": "mqbroker", "grouping" : "majorset", "maxgroupsize": 4, "templateid" : "mq.linux", "dr": "True"  },

	{ "clusters" : WASPODS ,"datacenter": "was" , "roles": "mq", "grouping" : "majorset", "maxgroupsize": 4, "templateid" : "mq.linux" },


	{ "clusters" : "INSIGHTS-CHI-SP2,INSIGHTS-CHI-SP1" ,"datacenter": "CHI" , "roles": "insights_iworker,insights_redis", "grouping" : "majorset", "maxgroupsize": 18, "templateid" : "insights" , "hostfilter": ".*[a-zA-Z]"},

	{ "clusters" : "LAPP2C1,LAPP2C2,LAPP2C2CS,LAPP2C1CS" ,"datacenter": "CHI" , "roles": "lapp", "grouping" : "majorset", "maxgroupsize": 8, "templateid" : "la.linux" },

	{ "clusters" : "PBSMATCH-SP2,PBSMATCH-SP1" ,"datacenter": "chi" , "roles": "pbsmatch", "grouping" : "majorset", "maxgroupsize": 1, "templateid" : "pbsmatch.linux" },

	{ "clusters" : WASPODS ,"datacenter": "chi" , "roles": "ffx", "grouping" : "majorset", "maxgroupsize": 4, "templateid" : "ffx", "dr": "True"  },

	{ "clusters" : CHIPODS ,"datacenter": "chi" , "roles": "ffx", "grouping" : "majorset", "maxgroupsize": 4, "templateid" : "ffx" }

]
if __name__ == "__main__": 
        i = 1 
	for test in testlist:
                print str(i) + ' #'
		gen_plan_by_idbquery(test)
		i += 1




