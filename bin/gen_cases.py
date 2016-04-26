#!/usr/bin/python
 
import os
import re
import sys
import socket
import subprocess
import logging
from optparse import OptionParser
import subprocess
import json
 
def groupType(role):
    # presets for certain roles for group type
    groupings = {'search': 'majorset',
                 'mnds,dnds': 'majorset',
                 'insights_iworker,insights_redis': 'majorset' 
                 }
    if role in groupings:
        return groupings[role]
    else:
        return 'majorset'

def groupSize(role):
    # presets for certain roles for sizing
    groupsizes = {'search': 15,
                  'insights_iworker,insights_redis': 18,
                  'mnds,dnds': 4
                      }
    if role in groupsizes:
        return groupsizes[role]
    else:
        return 1
    
def getData(filename):
    # Read in data from a file and return it
    with open(filename) as data_file:
        data = data_file.readlines()
    return data

def inputDictStrtoInt(m):
    # do a replace on the matching in m to remove quotes on ints
    str = 'maxgroupsize": ' + m.group(1).replace('"','')
    logging.debug(str)
    return str 

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-v", action="store_true", dest="verbose", default=False, help="verbosity")
    parser.add_option("-r", "--role", dest="role", help="role to be used")
    parser.add_option("-t", "--template", dest="template", help="template to be used")
    parser.add_option("--infra", dest="infra", help="Infra type [Primary|Secondary|Primary and Secondary|Supporting Infrastructure")
    parser.add_option("-g", "--group", dest="group", help="group for subject")
    parser.add_option("-s", "--groupsize", dest="groupsize", help="max groupsize for subject")
    parser.add_option("-p", "--podgroups", dest="podgroups", help="File with pod groupings")
    parser.add_option("-f", "--filter", dest="filter", help="regex host filter")
    parser.add_option("--regexfilter", dest="regexfilter", help="regex generic filter: <supportedfield>=value")
    parser.add_option("-e", "--exclude", dest="exclude", help="exclude file")
    parser.add_option("-d", "--dr", dest="dr", default="False", help="dr true or false")
    parser.add_option("-b", "--bundle", dest="bundle", help="Bundle short name eg may oct")
    parser.add_option("--clusteropstat", dest="clusteropstat", help="Cluster operational status")
    parser.add_option("--hostopstat", dest="hostopstat", help="Host operation status")
    parser.add_option("--casesubject", dest="casesubject", help="Initital case subject to use")
    parser.add_option("--patchset", dest="patchset", help="Patchset name eg 2015.10 or 2016.01")
    parser.add_option("--taggroups", dest="taggroups", help="Size for blocked groups for large running cases like hbase")
    python = 'python'
    excludelist = ''
    (options, args) = parser.parse_args()
    if options.verbose:
        logging.basicConfig(level=logging.DEBUG)
    if not options.casesubject:
        options.casesubject = options.bundle.upper() + " Patch Bundle"
    casesubject = options.casesubject
    grouping = "majorset"
    groupsize = 1
    if re.match(r'True', options.dr, re.IGNORECASE):
        site_flag = "DR"
    else:
        site_flag = "PROD"
    if options.role:
        grouping = groupType(options.role)
        groupsize = groupSize(options.role)     
    if options.groupsize:
        groupsize = options.groupsize
    if options.podgroups:
        data = getData(options.podgroups)
        for l in data:
            pods,dc = l.split()
            # Create a dict containing the options used for input to build_plan
            opt_bp = {"clusters" : pods ,"datacenter": dc , "roles": options.role, 
                      "grouping" : grouping, "maxgroupsize": groupsize,
                      "templateid" : options.template, "dr": options.dr}
            opt_gc = {}
            if options.filter:
                filter = "^.*" + options.filter
                opt_bp["hostfilter"] = filter
            if options.regexfilter:
                opt_bp["regexfilter"] = options.regexfilter
            if options.clusteropstat:
                opt_bp["cl_opstat"] = options.clusteropstat
            if options.hostopstat:
                opt_bp["ho_opstat"] = options.hostopstat
            # Bug in build_plan.py that does not handle quoted ints. 
            # This regex sub converts "1" into 1 and returns it
            opts_str = json.dumps(opt_bp)
            opts_str = re.sub('maxgroupsize": ("\d+")', inputDictStrtoInt, opts_str)
            logging.debug(opts_str)
            output_str = """python build_plan.py -C --bundle %s -G '%s' --taggroups %s -v""" % \
                            (options.patchset,opts_str,options.taggroups)
            if options.exclude:
                output_str = output_str + " --exclude " + options.exclude
            print(output_str)
            subject = casesubject + ": " + options.role.upper() + " " + dc.upper() + " " + pods + " " + site_flag
            logging.debug(subject)
            if options.group:
                subject = subject + " " + options.group
            print("""python gus_cases_vault.py -T change  -f ../templates/%s-patch.json  --inst %s --infra "%s" -s "%s" -k ../templates/6u6-plan.json  -l ../output/summarylist.txt -D %s -i ../output/plan_implementation.txt""" % (options.bundle,pods,options.infra,subject,dc))
