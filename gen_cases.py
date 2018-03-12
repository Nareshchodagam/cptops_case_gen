#!/usr/bin/python

import json
import logging
import re
from optparse import OptionParser

def groupType(role):
    # presets for certain roles for group type
    groupings = {'search': 'majorset',
                 'lhub': 'minorset',
                 'insights_iworker,insights_redis': 'majorset',
                 'ajna_mgmt,ajna_tracing,ajna_wrangler': 'minorset'
                 }

    if options.hostopstat and options.csv:
        if re.search(r'decom|hw_provisioning|pre_production|provisioning', options.hostopstat, re.IGNORECASE) and not re.search(r'ffx', options.role, re.IGNORECASE):
            return 'all'

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

def sortHost(data):
    host_dict = {}
    for host in data:
        dc = host.split('-')[3]
        dc = dc.rstrip('\n')
        if host_dict.has_key(dc):
            host_dict[dc].append(host.rstrip())
        else:
            host_dict[dc] = [host.rstrip()]
    return host_dict

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


# W-4574049 This code was repeated on multiple conditions, hence add it to a func and call func on appropriate places
def cmdformat(output_str):
    if not options.idb:
        output_str = output_str + " -x"
    if options.groupsize:
        output_str = output_str + " --gsize %s" % groupsize
    if options.dowork:
        output_str = output_str + " --dowork " + options.dowork
    if options.delpatched:
        output_str = output_str + " --delpatched "
    if options.casework == "reimage":
        output_str = output_str + " --serial --monitor "
    if options.filteros:
        output_str = output_str + " --filter_os "
    if options.failthresh:
        output_str = output_str + " --failthresh " + options.failthresh
    if options.hostpercent:
        output_str = output_str + " --hostpercent " + options.hostpercent

    return output_str
# W-4574049 End


if __name__ == "__main__":
    parser = OptionParser()
    parser.set_defaults(dowork='all_updates')
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
    parser.add_option("--idb", dest="idb", action="store_true", default=False, help="Use idb to get host information")
    parser.add_option("--casetype", dest="casetype", help="Case type to use eg patch or re-image")
    parser.add_option("--clusteropstat", dest="clusteropstat", help="Cluster operational status")
    parser.add_option("--hostopstat", dest="hostopstat", help="Host operation status")
    parser.add_option("--casesubject", dest="casesubject", help="Initital case subject to use")
    parser.add_option("--patchset", dest="patchset", help="Patchset name eg 2015.10 or 2016.01")
    parser.add_option("--implplan", dest="implplansection", help="Template to use for implementation steps in planner")
    parser.add_option("--taggroups", dest="taggroups", help="Size for blocked groups for large running cases like hbase")
    parser.add_option("--dowork", dest="dowork", help="Include template to use for v_INCLUDE replacement")
    parser.add_option("--hostpercent", dest="hostpercent", help=" Host min percentage to calculate concurrency eg 33")
    parser.add_option("--HLGrp", dest="hlgrp", action="store_true", default="False", help="Groups hostlist by DC")
    parser.add_option("--no_host_validation", dest="no_host_v", action="store_true",  help="Skip verify remote hosts")
    parser.add_option("--auto_close_case", dest="auto_close_case", action="store_true", default="True", help="Auto close case")
    parser.add_option("--nolinebacker", dest="nolinebacker", help="Don't use linebacker")
    # W-4531197 Adding logic to remove already patched host for Case.
    parser.add_option("--delpatched", dest="delpatched", action='store_true', help="command to remove patched host.")
    # End
    parser.add_option("--csv", dest="csv", help="Read given CSV file and create cases as per the status.")
    # W-4574049 Command line option to filter hosts by OS [Specific to CentOS7 Migration ]
    parser.add_option("--cstatus", dest="cstatus", default="approved", help="Change cases status")
    parser.add_option("--failthresh", dest="failthresh", help="Failure threshold for kp_client batch")
    parser.add_option("--casework", dest="casework", help="Case type to use eg patch or re-image")
    parser.add_option("--monitor", dest="monitor", action="store_true", help="monitor [used in reimage]")
    parser.add_option("--serial", dest="serial", action="store_true", help="serial [ used in reimage]")
    parser.add_option("--filter_os", dest="filteros", action="store_true", help="Filter hosts for CentOS7 migration")
    # W-4574049 End

    python = 'python'
    excludelist = ''
    (options, args) = parser.parse_args()

    if options.no_host_v:
        hostv = "--no_host_validation"
    else:
        hostv = ""

    if options.verbose:
        logging.basicConfig(level=logging.DEBUG)
    if not options.casesubject:
        options.casesubject = options.patchset + " Patch Bundle"

    # W-4574049 Add to support CentOS7 migration
    if options.casework == "reimage":
        patch_json = "migration-patch.json"
        options.implplansection = "templates/migration-plan.json"
    else:
        patch_json = "bundle-patch.json"
    # W-4574049 end

    casesubject = options.casesubject
    grouping = "majorset"
    groupsize = 1
    implplansection = "templates/6u6-plan.json"
    if re.match(r'ffx', options.role, re.IGNORECASE) and not options.casetype and not options.exclude:
        options.exclude = "hostlists/ffxexclude"
    if options.implplansection:
        implplansection = options.implplansection
    if re.match(r'True', options.dr, re.IGNORECASE):
        site_flag = "DR"
    else:
        site_flag = "PROD"
    # Code to update the HBASE DR status to false.
    if re.match(r'mnds|dnds', options.role, re.IGNORECASE):
        if re.match(r'True', options.dr, re.IGNORECASE):
            options.dr = "false"

    if options.role:
        grouping = groupType(options.role)
        groupsize = groupSize(options.role)
    if options.groupsize:
        groupsize = options.groupsize
    if options.hostpercent:
        hostpercent = options.hostpercent

    # W-4531197 Adding logic to remove already patched host for Case.
    if options.delpatched:
        delpatched = options.delpatched
    # End

    if options.podgroups and options.casetype == "hostlist" and options.hlgrp == "False":
        data = getData(options.podgroups)
        dcs = getDCs(data)
        if options.group:
            subject = casesubject + " " + options.group
        else:
            subject = casesubject + ": " + options.role.upper()
        dcs_list = ",".join(dcs)

        output_str = """python build_plan.py -l %s -t %s --bundle %s -T -M %s %s --auto_close_case %s """\
		     """--nolinebacker %s""" % (options.podgroups, options.template, options.patchset, grouping, hostv, options.auto_close_case,
               					options.nolinebacker)

        output_str = cmdformat(output_str)
        print("%s" % output_str)
        print("""python gus_cases_vault.py -T change --cstatus %s  -f templates/%s --infra "%s" -s "%s" -k %s -l output/summarylist.txt -D %s -i output/plan_implementation.txt -r %s""" % (options.cstatus, patch_json, options.infra, subject, implplansection, dcs_list, options.role))
    elif options.podgroups and options.casetype == "hostlist" and options.hlgrp == True:
        data = getData(options.podgroups)
        hostlist = sortHost(data)
        for dc, hosts in hostlist.iteritems():
            if options.group:
                subject = casesubject + " " + options.group + " " + dc.upper()
            else:
                subject = casesubject + ": " + options.role.upper()
            output_str = """python build_plan.py -l %s -t %s --bundle %s -T -M %s  %s --auto_close_case %s """\
                         """--nolinebacker %s""" % (options.podgroups, options.template, options.patchset, grouping,
                                                    hostv, options.auto_close_case, options.nolinebacker)
            output_str = cmdformat(output_str)
            output_str = output_str + '  -l "%s"' % ",".join(hosts)
            print("%s" % output_str)
            print("""python gus_cases_vault.py -T change --cstatus %s -f templates/%s --infra "%s" -s "%s " -k %s -l output/summarylist.txt -D %s -i output/plan_implementation.txt -r %s""" % (options.cstatus, patch_json,options.infra,subject,implplansection,dc, options.role))

    elif options.podgroups and not options.casetype:
        data = getData(options.podgroups)
        for l in data:
            try:
                pods, dc, sp, cl_status = l.split()
                if sp:
                    if (options.role or options.role.upper()) == "prsn,chan,msg,dstore":
                        # Create a dict containing the options used for input to build_plan for Chatter with SP option passed
                        opt_bp = {"superpod": sp, "clusters": pods, "datacenter": dc.lower(), "roles": options.role,
                                  "maxgroupsize": groupsize, "templateid": options.template, "dr": options.dr, "cl_opstat": cl_status}
                    elif (options.role.lower()) == "app":
                        # This section is to remove grouping tag for core app #W-3758985
                        opt_bp = {"superpod": sp, "clusters": pods, "datacenter": dc.lower(), "roles": options.role,
                                  "maxgroupsize": groupsize, "templateid": options.template, "dr": options.dr, "cl_opstat": cl_status}
                    else:
                        # Create a dict containing the options used for input to build_plan with SP option passed
                        opt_bp = {"superpod": sp, "clusters": pods, "datacenter": dc.lower(), "roles": options.role,
                                  "grouping": grouping, "maxgroupsize": groupsize,
                                  "templateid": options.template, "dr": options.dr, "cl_opstat": cl_status}
            except:
                pods, dc, cl_status = l.split()
                # Create a dict containing the options used for input to build_plan for Chatter
                if (options.role or options.role.upper()) == "prsn,chan,msg,dstore":
                    opt_bp = {"clusters": pods, "datacenter": dc.lower(), "roles": options.role,
                              "maxgroupsize": groupsize, "templateid": options.template, "dr": options.dr, "cl_opstat": cl_status}
                else:
                    # Create a dict containing the options used for input to build_plan
                    opt_bp = {"clusters": pods, "datacenter": dc.lower(), "roles": options.role,
                              "grouping": grouping, "maxgroupsize": groupsize,
                              "templateid": options.template, "dr": options.dr, "cl_opstat": cl_status}
            opt_gc = {}
            if options.filter:
                filter = options.filter
                opt_bp["hostfilter"] = filter
            if options.regexfilter:
                opt_bp["regexfilter"] = options.regexfilter
                host_pri_sec = opt_bp.get("regexfilter").split('=')[1]
                cluster_status = opt_bp["cl_opstat"]
#This section will allow to control the cases creation template to be used once cluster status is passed in preset. Refactoring needed
            if options.clusteropstat:
                for cl_status in options.clusteropstat.split(','):
                    if opt_bp["cl_opstat"] == cl_status:
                        opt_bp["cl_opstat"] = cl_status
                        opt_bp["templateid"] = 'straight-patch'
                        opt_bp["grouping"] = 'all'
                        opt_bp["maxgroupsize"] = '25'
            else:
                pass
            cluster_status = opt_bp["cl_opstat"]

            if options.hostopstat:
                opt_bp["ho_opstat"] = options.hostopstat
            # Bug in build_plan.py that does not handle quoted ints.
            # This regex sub converts "1" into 1 and returns it
            opts_str = json.dumps(opt_bp)
            opts_str = re.sub('maxgroupsize": ("\d+")', inputDictStrtoInt, opts_str)
            logging.debug(opts_str)
            # Added linebacker -  W-3779869
            output_str = """python build_plan.py -C --bundle %s -G '%s' --taggroups %s %s  --auto_close_case %s -v"""\
                         """ --nolinebacker %s""" % (options.patchset,opts_str,options.taggroups, hostv, options.auto_close_case,  options.nolinebacker)
            output_str = cmdformat(output_str)
            print(output_str)
            if options.regexfilter:
                subject = casesubject + ": " + options.role.upper() + " " + dc.upper() + " " + pods + " " + site_flag + " " + host_pri_sec + "[" + cluster_status + "]"
            else:
                subject = casesubject + ": " + options.role.upper() + " " + dc.upper() + " " + pods + " " + site_flag + "[" + cluster_status + "]"
            logging.debug(subject)
            if options.group:
                subject = subject + " " + options.group
            #if not re.search(r"json", options.bundle):
            #    options.bundle = options.bundle + "-patch.json"
            print("""python gus_cases_vault.py -T change --cstatus %s  -f templates/%s  --inst %s --infra "%s" -s "%s" -k %s  -l output/summarylist.txt -D %s -i  output/plan_implementation.txt -r %s""" % (options.cstatus,patch_json,pods,options.infra,subject,implplansection,dc, options.role))
