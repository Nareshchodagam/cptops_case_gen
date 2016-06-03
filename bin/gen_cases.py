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

def genDCINST(data):
    clusters_dc = {}
    for l in data:
        clusters,dc = l.split()
        clusters_dc[clusters] = dc.rstrip()  
    output = "{ " 
    output = output + ', '.join(['"%s": "%s"' % (value,key) for (key,value) in clusters_dc.items()])
    output = output + " }"
    return output


def get_site(host):
    inst,hfuc,g,site = host.split('-')
    short_site = site.replace(".ops.sfdc.net", "")
    logging.debug(short_site)
    return short_site

def getDCs(data):
    dcs = []
    for l in data:
        dc = get_site(l.rstrip())
        if dc not in dcs:
            dcs.append(dc)
    return dcs

def inputDictStrtoInt(m):
    # do a replace on the matching in m to remove quotes on ints
    str = 'maxgroupsize": ' + m.group(1).replace('"','')
    logging.debug(str)
    return str 

if __name__ == "__main__":
    parser = OptionParser()
    parser.set_defaults(dowork='system_update')
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
    parser.add_option("--idb", dest="idb", action="store_true", default=False, help="Use idb to get host information")
    parser.add_option("--casetype", dest="casetype", help="Case type to use eg patch or re-image")
    parser.add_option("--clusteropstat", dest="clusteropstat", help="Cluster operational status")
    parser.add_option("--hostopstat", dest="hostopstat", help="Host operation status")
    parser.add_option("--casesubject", dest="casesubject", help="Initital case subject to use")
    parser.add_option("--patchset", dest="patchset", help="Patchset name eg 2015.10 or 2016.01")
    parser.add_option("--implplan", dest="implplansection", help="Template to use for implementation steps in planner")
    parser.add_option("--taggroups", dest="taggroups", help="Size for blocked groups for large running cases like hbase")
    parser.add_option("--dowork", dest="dowork", help="Include template to use for v_INCLUDE replacement")
    python = 'python'
    excludelist = ''
    (options, args) = parser.parse_args()
    if options.verbose:
        logging.basicConfig(level=logging.DEBUG)
    if not options.casesubject:
        options.casesubject = options.patchset + " Patch Bundle"
    casesubject = options.casesubject
    grouping = "majorset"
    groupsize = 1
    implplansection = "../templates/6u6-plan.json"
    if re.match(r'ffx', options.role, re.IGNORECASE) and not options.casetype and not options.exclude:
        options.exclude = "../hostlists/ffxexclude"
    if options.implplansection:
        implplansection = options.implplansection
    if re.match(r'True', options.dr, re.IGNORECASE):
        site_flag = "DR"
    else:
        site_flag = "PROD"
    if options.role:
        grouping = groupType(options.role)
        groupsize = groupSize(options.role)     
    if options.groupsize:
        groupsize = options.groupsize
    if options.podgroups and options.casetype == "hostlist":
        data = getData(options.podgroups)
        dcs = getDCs(data)
        subject = casesubject + ": " + options.role.upper()
        dcs_list = ",".join(dcs)
        #python build_plan.py -l ../hostlists/restoreffx -x -t straight-patch -T --bundle 2016.02
        output_str = """python build_plan.py -l %s -t %s --bundle %s -T -M %s""" % (options.podgroups, options.template, options.patchset,grouping)
        if options.idb != True:
            output_str = output_str + " -x"
        if options.groupsize:
            output_str = output_str + " --gsize %s" % groupsize 
        if options.dowork:
            output_str = output_str + " --dowork " + options.dowork
        print("%s" % output_str)
        print("""python gus_cases_vault.py -T change  -f ../templates/%s --infra "%s" -s "%s" -k %s -l ../output/summarylist.txt -D %s -i ../output/plan_implementation.txt""" % (options.bundle,options.infra,subject,implplansection,dcs_list))
    elif options.podgroups and options.casetype == "coreappafw":
        data = getData(options.podgroups)
        inst_data = genDCINST(data)
        if not re.search(r"json", options.bundle):
            options.bundle = options.bundle + "-patch.json"
        subject = casesubject + ": " + options.role.upper() + " " + options.casetype.upper() + " " + site_flag
        print("""python gus_cases_vault.py -T change  -f ../templates/%s --infra "%s" -s "%s" -k %s -D '%s'""" % (options.bundle,options.infra,subject,implplansection,inst_data))
    elif options.podgroups and not options.casetype:
        data = getData(options.podgroups)
        for l in data:
            pods,dc = l.split()
            # Create a dict containing the options used for input to build_plan
            opt_bp = {"clusters" : pods ,"datacenter": dc.lower() , "roles": options.role, 
                      "grouping" : grouping, "maxgroupsize": groupsize,
                      "templateid" : options.template, "dr": options.dr}
            opt_gc = {}
            if options.filter:
                filter = "^.*" + options.filter
                opt_bp["hostfilter"] = filter
            if options.regexfilter:
                opt_bp["regexfilter"] = options.regexfilter
                host_pri_sec = opt_bp.get("regexfilter").split('=')[1]
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
            if options.casetype == "reimage":
                output_str = output_str + " --serial --monitor"
            if options.dowork:
                output_str = output_str + " --dowork " + options.dowork
            print(output_str)
            subject = casesubject + ": " + options.role.upper() + " " + dc.upper() + " " + pods + " " + site_flag + " " + host_pri_sec
            logging.debug(subject)
            if options.group:
                subject = subject + " " + options.group
            if not re.search(r"json", options.bundle):
                options.bundle = options.bundle + "-patch.json"
            print("""python gus_cases_vault.py -T change  -f ../templates/%s  --inst %s --infra "%s" -s "%s" -k %s  -l ../output/summarylist.txt -D %s -i ../output/plan_implementation.txt""" % (options.bundle,pods,options.infra,subject,implplansection,dc))
