
Case generation examples

implementation planner patch details must be in json format

Sites proxy

DR

python build_plan.py -c 0000001 -C -G '{"clusters" : "'$1'" ,"datacenter": "chi" , "roles": "proxy", "grouping" : "majorset,minorset", "maxgroupsize": 5, "templateid" : "siteproxy_standby.linux", "dr": "True"  }' -v

python gus_cases.py -T change  -f ../templates/sites-proxy-rh6u6-patch.json  -s "May Patch Bundle : Sites Proxies CHI $1 DR" -k ../templates/6u6-plan.json  -l ../output/summarylist.txt -D chi -i ../output/plan_implementation.txt

PROD

python build_plan.py -c 0000001 -C -G '{"clusters" : "'$1'" ,"datacenter": "chi" , "roles": "proxy", "grouping" : "majorset,minorset", "maxgroupsize": 5, "templateid" : "siteproxy.linux" }'

python gus_cases.py -T change  -f ../templates/sites-proxy-rh6u6-patch.json  -s "May Patch Bundle : Sites Proxies CHI $1 PROD" -k ../templates/6u6-plan.json  -l ../output/summarylist.txt -D chi -i ../output/plan_implementation.txt

HBASE

DR

python build_plan.py -c 0000001 -C -G '{"clusters" : "'$1'" ,"datacenter": "chi" , "roles": "mnds,dnds", "grouping" : "majorset,minorset", "maxgroupsize": 4, "templateid" : "hbase.linux", "dr": "False"  }' -v

python gus_cases.py -T change  -f ../templates/hbase-rh6u6-patch.json  -s "May Patch Bundle : HBASE CHI $1 DR" -k ../templates/6u6-plan.json  -l ../output/summarylist.txt -D chi -i ../output/plan_implementation.txt

PROD

python build_plan.py -c 0000001 -C -G '{"clusters" : "'$1'" ,"datacenter": "chi" , "roles": "mnds,dnds", "grouping" : "majorset,minorset", "maxgroupsize": 14, "templateid" : "hbase.linux" }' -v

python gus_cases.py -T change  -f ../templates/hbase-rh6u6-patch.json  -s "May Patch Bundle : HBASE CHI $1 PROD" -k ../templates/6u6-plan.json  -l ../output/summarylist.txt -D chi -i ../output/plan_implementation.txt

Search

DR

python build_plan.py -c 0000001 -C -G '{"clusters" : "'$1'" ,"datacenter": "chi" , "roles": "search", "grouping" : "majorset,minorset", "maxgroupsize": 4, "templateid" : "search", "dr": "True"  }' -v

python gus_cases.py -T change  -f ../templates/search-rh6u6-patch.json  -s "May Patch Bundle : SEARCH CHI $1 DR" -k ../templates/6u6-plan.json  -l ../output/summarylist.txt -D chi -i ../output/plan_implementation.txt

PROD

python build_plan.py -c 0000001 -C -G '{"clusters" : "'$1'" ,"datacenter": "chi" , "roles": "search", "grouping" : "majorset,minorset", "maxgroupsize": 4, "templateid" : "search" }' -v

python gus_cases.py -T change  -f ../templates/search-rh6u6-patch.json  -s "May Patch Bundle : SEARCH CHI $1 PROD" -k ../templates/6u6-plan.json  -l ../output/summarylist.txt -D chi -i ../output/plan_implementation.txt

MQ

DR

python build_plan.py -c 0000001 -C -G '{"clusters" : "'$1'" ,"datacenter": "was" , "roles": "mqbroker", "grouping" : "majorset", "maxgroupsize": 4, "templateid" : "mqbroker", "dr": "True"  }' -v

python gus_cases.py -T change  -f ../templates/mq-rh6u6-patch.json  -s "May Patch Bundle : MQ WAS $1 DR" -k ../templates/6u6-plan.json  -l ../output/summarylist.txt -D was -i ../output/plan_implementation.txt -v

PROD

python build_plan.py -c 0000001 -C -G '{"clusters" : "'$1'" ,"datacenter": "was" , "roles": "mq", "grouping" : "majorset", "maxgroupsize": 4, "templateid" : "mq.linux" }' -v

python gus_cases.py -T change  -f ../templates/mq-rh6u6-patch.json  -s "May Patch Bundle : MQ WAS $1 PROD" -k ../templates/6u6-plan.json  -l ../output/summarylist.txt -D was -i ../output/plan_implementation.txt

Public Proxy

generate a hostlist and update into hl.txt

python build_plan.py -c 0000001 -l hl.txt -t public-proxy.linux -x

python gus_cases.py -T change  -f ../templates/public-proxy-rh6u6-patch.json  -s "May Patch Bundle : PUBLIC PROXY WAS SP1 PROD" -k ../templates/6u6-plan.json  -l hl.txt -D was -i ../output/plan_implementation.txt

Insights

PROD

python build_plan.py -c 0000001 -C -G '{"clusters" : "chi" ,"datacenter": "CHI" , "roles": "insights_iworker,insights_redis", "grouping" : "majorset", "maxgroupsize": 18, "templateid" : "insights" , "hostfilter": ".*[a-zA-Z]"}' -v
python gus_cases.py -T change  -f ../templates/insights-patch.json  -s "May Patch Bundle : INSIGHTS CHI $1 PROD" -k ../templates/6u6-plan.json  -l ../output/summarylist.txt -D chi -i ../output/plan_implementation.txt -A


Live Agent

PROD

python build_plan.py -c 0000001 -C -G '{"clusters" : "'$1'" ,"datacenter": "CHI" , "roles": "lapp", "grouping" : "majorset", "maxgroupsize": 8, "templateid" : "la.linux" }' -v

python gus_cases.py -T change  -f ../templates/hbase-rh6u6-patch.json  -s "May Patch Bundle : Live Agent CHI $1 PROD" -k ../templates/6u6-plan.json  -l ../output/summarylist.txt -D chi -i ../output/plan_implementation.txt

PBSGEO

PROD

python build_plan.py -c 0000001 -l hl.txt -s NONE -d chi -i NONE -t pbsgeo.linux -r pbsgeo -x

python gus_cases.py -T change  -f ../templates/hbase-rh6u6-patch.json  -s "May Patch Bundle : PBSGEO CHI $1 PROD" -k ../templates/6u6-plan.json  -l hl.txt -D chi -i ../output/plan_implementation.txt

PBSMATCH

PROD

python build_plan.py -c 0000001 -C -G '{"clusters" : "'$1'" ,"datacenter": "chi" , "roles": "pbsmatch", "grouping" : "majorset", "maxgroupsize": 1, "templateid" : "pbsmatch.linux" }' -v

python gus_cases.py -T change  -f ../templates/hbase-rh6u6-patch.json  -s "May Patch Bundle : PBSMATCH CHI $1 PROD" -k ../templates/6u6-plan.json  -l ../output/summarylist.txt -D chi -i ../output/plan_implementation.txt

FFX

PROD

python build_plan.py -c 0000001 -C -G '{"clusters" : "'$1'" ,"datacenter": "chi" , "roles": "ffx", "grouping" : "majorset", "maxgroupsize": 4, "templateid" : "ffx", "dr": "True"  }' -v

python gus_cases.py -T change  -f ../templates/ffx-rh6u6-patch.json  -s "May Patch Bundle : FFX CHI $1 DR" -k ../templates/6u6-plan.json  -l ../output/summarylist.txt -D chi -i ../output/plan_implementation.txt -v

python build_plan.py -c 0000001 -C -G '{"clusters" : "'$1'" ,"datacenter": "chi" , "roles": "ffx", "grouping" : "majorset", "maxgroupsize": 4, "templateid" : "ffx" }' -v

python gus_cases.py -T change  -f ../templates/ffx-rh6u6-patch.json  -s "May Patch Bundle : FFX CHI $1 PROD" -k ../templates/6u6-plan.json  -l ../output/summarylist.txt -D chi -i ../output/plan_implementation.txt


