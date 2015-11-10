#!/usr/bin/python

import os
import re
import sys
import socket
import subprocess
import logging
from optparse import OptionParser
import subprocess
import common


def getData(filename):
    with open(filename) as data_file:
        data = data_file.readlines()
    return data

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-v", action="store_true", dest="verbose", default=False, help="verbosity")
    parser.add_option("-r", "--role", dest="role", help="role to be used")
    parser.add_option("-t", "--template", dest="template", help="template to be used")
    parser.add_option("-g", "--group", dest="group", help="group for subject")
    parser.add_option("-p", "--podgroups", dest="podgroups", help="File with pod groupings")
    parser.add_option("-f", "--filter", dest="filter", help="regex host filter")
    parser.add_option("-d", "--dr", dest="dr", default="False", help="dr true or false")
    parser.add_option("-b", "--bundle", dest="bundle", help="Bundle short name eg may oct")
    
    (options, args) = parser.parse_args()
    if options.verbose:
        logging.basicConfig(level=logging.DEBUG)
    if options.podgroups:
        data = getData(options.podgroups)
        for l in data:
            pods,dc = l.split()
            #pods,dc,options.role,options.template,options.dr

            #msg =  { "clusters" : pods ,"datacenter": dc , "roles": options.role, "cl_opstat" : "ACTIVE", "grouping" : "majorset", "maxgroupsize": 4, "templateid" : options.template, "dr": options.dr }
            #print("""python build_plan.py -c 0000001 -C -G '{"clusters" : "%s" ,"datacenter": "%s" , "roles": "%s", "grouping" : "majorset", "maxgroupsize": 4, "templateid" : "%s", "hostfilter": "^.*%s" }' -v""" % (pods,dc,options.role,options.template,options.filter))
            #print("""python build_plan.py -c 0000001 -C -G '{"clusters" : "%s" ,"datacenter": "%s" , "roles": "%s", "grouping" : "majorset", "maxgroupsize": 4, "templateid" : "%s", "dr": "%s", "hostfilter": "^.*%s" }' -v""" % (pods,dc,options.role,options.template,options.dr,options.filter))
            print("""python build_plan.py -C -G '{"clusters" : "%s" ,"datacenter": "%s" , "roles": "%s", "grouping" : "majorset,minorset", "maxgroupsize": 3, "templateid" : "%s", "dr": "%s" , "hostfilter": "^.*%s"}' -v""" % (pods,dc,options.role,options.template,options.dr,options.filter))
            #print("""python build_plan.py -C -G '%s' -v""" % msg)
            if options.group:
                print("""python gus_cases.py -T change  -f ../templates/%s-patch.json  -s "%s Patch Bundle: %s %s %s %s" -k ../templates/6u6-plan.json  -l ../output/summarylist.txt -D %s -i ../output/plan_implementation.txt""" % (options.bundle,options.bundle.upper(),options.role.upper(),dc.upper(),pods,options.group,dc))
            else:
                print("""python gus_cases.py -T change  -f ../templates/%s-patch.json  -s "%s Patch Bundle: %s %s %s" -k ../templates/6u6-plan.json  -l ../output/summarylist.txt -D %s -i ../output/plan_implementation.txt""" % (options.bundle,options.bundle.upper(),options.role.upper(),dc.upper(),pods,dc))