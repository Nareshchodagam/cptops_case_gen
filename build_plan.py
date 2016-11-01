#!/usr/bin/python
###############################################################################
#
# Purpose: Take information from idb build imp plans.
#
# Usage: See ../docs/build_plan_README.md
#
###############################################################################

from optparse import OptionParser
import json
import logging
import re
import glob
import os.path
import logging
from modules.buildplan_helper import *
import sys
reload(sys)

sys.setdefaultencoding('utf8')
###############################################################################
#                Constants
###############################################################################
templatefile = ''
out_file = ''
pre_file = ''
post_file = ''
hosts = []
hostlist = []

new_supportedfields = {'superpod' : 'host.cluster.superpod.name',
                   'role' : 'host.deviceRole',
                   'cluster' : 'host.cluster.name',
                   'hostname' : 'host.name',
                   'failoverstatus' : 'host.failOverStatus',
                   'dr' : 'host.cluster.dr',
                   'host_operationalstatus': 'host.operationalStatus',
                   'cluster_operationalstatus': 'host.cluster.operationalStatus',
                   'clustertype' : 'host.cluster.clusterType',
                   'index_key' : 'key',
                   'index_value' : 'value',
                   'cluter_configs': 'host.cluster.clusterConfigs',
                   'host_configs': 'host',
                   'cluster_env': 'host.cluster.environment'}

#Old supportedfields.
supportedfields = {
                  'superpod' : 'cluster.superpod.name',
                  'role' : 'deviceRole',
                  'cluster' : 'cluster.name',
                  'hostname' : 'name',
                  'failoverstatus' : 'failOverStatus',
                  'dr' : 'cluster.dr',
                  'host_operationalstatus': 'operationalStatus',
                  'cluster_operationalstatus': 'cluster.operationalStatus',
                  'clustertype' : 'cluster.clusterType'}

###############################################################################
#                Functions
###############################################################################

def get_hosts_from_file(filename):
    try:
        with open(filename) as f:
            hostlist = f.read().splitlines()
    except:
        print "Unable to open host list file"
        exit()
    return hostlist

def write_list_to_file(filename, list, newline=True):
    if newline:
        s = '\n'.join(list)
    else:
        s = ''.join(list)
    f = open(filename, 'w')
    f.write(s)
    f.close()

def get_json(input_file):
    with open(common.etcdir + '/' + input_file) as data_file:
        try:
            data = json.load(data_file)
        except Exception as e:
            print('Problem loading json from file %s : %s' % (input_file,e))
    return data

def build_dynamic_groups(hosts):

    # Cut up the hostlist by the values stored in ../etc/host_regex.json
    # to generate more complex plans.

    outmap = {}
    with open(common.etcdir + '/host_regex.json') as data_file:
        hostmap = json.load(data_file)

    for r, v in hostmap.items():
        regexp = re.compile(r)
        for host in hosts:
            if regexp.search(host) is not None:
                if v in outmap and not (outmap[v] is None):
                    outmap[v].append(host)
                else:
                    outmap[v] = []
                    outmap[v].append(host)
    return outmap


def compile_template(input, hosts, cluster, datacenter, superpod, casenum, role, cl_opstat='',ho_opstat='',template_vars=None):
    # Replace variables in the templates
    logging.debug('Running compile_template')

    output = input
    build_command = " ".join(sys.argv)
    build_command = build_command.replace("{","'{")
    build_command = build_command.replace("}","}'")

    global gblSplitHosts
    global gblExcludeList
    #before default ids in case of subsets
    for key, hostlist in gblSplitHosts.iteritems():
        output = output.replace(key, ",".join(hostlist))

    print 'template_vars', template_vars
    hlist=hosts.split(",")

    if gblExcludeList:
        for excluded_host in gblExcludeList:
            while True:
                try:
                    hlist.remove(str(excluded_host))
                except:
                    break
    hosts=",".join(hlist )

    #Ability to reuse templates and include sections. Include in refactoring
    if options.dowork:
        output = getDoWork(output, options.dowork)

    if options.checkhosts:
        hosts = '`~/check_hosts.py -H ' + hosts  + '`'
    output = output.replace('v_HOSTS', hosts)
    output = output.replace('v_CLUSTER', cluster)
    output = output.replace('v_DATACENTER', datacenter)
    output = output.replace('v_SUPERPOD', superpod)
    output = output.replace('v_CASENUM', casenum)
    output = output.replace('v_ROLE', role)
    output = output.replace('v_BUNDLE', options.bundle)
    # Total hack to pass kp_client concurrency and threshold values. Include in refactoring
    if options.concur and options.failthresh:
        concur = options.concur
        failthresh = options.failthresh
    else:
        concur, failthresh = getConcurFailure(role,cluster)
    output = output.replace('v_CONCUR', str(concur))
    output = output.replace('v_FAILTHRESH', str(failthresh))
    # Added to enable passing the hostfilter inside the plan.
    if options.idbgen and 'hostfilter' in json.loads(options.idbgen):
        input_values = json.loads(options.idbgen)
        output = output.replace('v_HOSTFILTER', input_values['hostfilter'])

    if not template_vars == None:
        if 'monitor-host' in template_vars.keys():
            output = output.replace('v_MONITOR', template_vars['monitor-host'])
        if 'serialnumber' in template_vars.keys():
            output = output.replace('v_SERIAL', template_vars['serialnumber'])
        if 'sitelocation' in template_vars.keys():
            output = output.replace('v_SITELOCATION', template_vars['sitelocation'])
        if 'product_rrcmd' in template_vars.keys():
            output = output.replace('v_PRODUCT_RRCMD', template_vars['product_rrcmd'])
        if 'ignored_process_names' in template_vars.keys():
            output = output.replace('v_IGNORE_PROCS_RRCMD_', template_vars['ignored_process_names'])
        if 'drnostart_rrcmd' in template_vars.keys():
            output = output.replace('v_DRNOSTART_RRCMD_', template_vars['drnostart_rrcmd'])
    #output = output.replace('v_SERIAL', options.monitor)
    output = output.replace('v_CL_OPSTAT', cl_opstat)
    output = output.replace('v_HO_OPSTAT', ho_opstat)
    output = output.replace('v_COMMAND', build_command)

    return output

def getDoWork(input, dowork):
    template_file = common.templatedir + "/" + str(dowork) + ".template"
    if os.path.isfile(template_file):
        with open(template_file, 'r') as f:
            data = f.readlines()
    v_include = "".join(data)
    input = input.replace('v_INCLUDE', v_include)
    return input

def getConcurFailure(role,cluster):
    rates = get_json('afw_presets.json')
    cluster_type = ''.join([i for i in cluster if not i.isdigit()])
    if cluster in rates and role in rates[cluster]:
        return rates[cluster][role]['concur'], rates[cluster][role]['failthresh']
    elif cluster_type in rates and role in rates[cluster_type]:
        return rates[cluster_type][role]['concur'], rates[cluster_type][role]['failthresh']
    else:
        return rates['concur'],rates['failthresh']


def prep_template(template, outfile):
    # Determine which bits are necessary to include in the final output.
    # This only preps the template. It does not write out anything.


    global pre_file
    global post_file
    global out_file
    global template_file

    logging.debug('Executing prep_template()')
    if options.clusterstatus == 'STANDBY':
      logging.debug('Template is for a standby cluster')
      template_file = common.templatedir + "/" + str(template) + "_standby.template"
      out_file = outfile + ".sb"
    else:
      logging.debug('Template is for a primary cluster')
      template_file = common.templatedir + "/" + str(template) + ".template"
      out_file = outfile
    print out_file

    # Assuming that we do NOT want separate pre/post script for active/standby
    # forcing to use the basename pre/post (for example - search.template.pre)
    # as opposed to search_standby.template.pre

    logging.debug('Using template file: ' + template_file)

    if not os.path.isfile(template_file):
        print(template_file + " is not a file that exists. Check your template name.")
        exit()

    template_basename = re.sub(r'_standby', "", template_file)

    logging.debug('Basename template: ' + template_basename)

    if os.path.isfile(str(template_basename) + ".pre"):
        logging.debug('Pre template exists')
        pre_file = template_basename + ".pre"
    else:
        logging.debug('Using generic pre template')
        pre_file = common.templatedir + "/generic.pre"

    if os.path.isfile(str(template_basename) + ".post"):
        logging.debug('Post template exists')
        post_file = template_basename + ".post"
    else:
        logging.debug('Using generic post template')
        post_file = common.templatedir + "/generic.post"



def gen_plan(hosts, cluster, datacenter, superpod, casenum, role,groupcount=0,cl_opstat='',ho_opstat='',template_vars={}):
    # Generate the main body of the template (per host)
    logging.debug('Executing gen_plan()')
    print "Generating: " + out_file
    s = open(template_file).read()
    s = compile_template(s, hosts, cluster, datacenter, superpod, casenum, role, cl_opstat,ho_opstat,template_vars)


    f = open(out_file, 'w')
    f.write(s)
    f.close()

def apply_grouptags(content,tag_id):
    return 'BEGIN_GROUP: ' + tag_id + '\n\n' + content + '\n\n' + \
                                'END_GROUP: ' + tag_id + '\n'




def rewrite_groups(myglob,taggroups):

    myglob.sort(key=humanreadable_key)
    groupid=1
    i = 1
    content = ''
    logging.debug("Files in output dir: " + str(len(myglob)))
    if taggroups > len(myglob):
        raise Exception('taggroups parameter is greater than the number of groups, try reducing value for maxgroupsize or taggroups')
    # we need to decrement the taggroups if there will be hosts left over in the last group
    if len(myglob) % taggroups != 0:
        taggroups -= 1

    gtsize = len(myglob) / taggroups
    gtsize = 1 if gtsize == 0 else gtsize


    print 'Tag groups : ' + str(taggroups)
    print 'tag group size :' + str(gtsize)
    print 'number of files ' + str(len(myglob))
    for f in myglob:
       print 'rewriting file : ' + f
       content += open(f, "r").read() + '\n\n'
       os.remove(f)
       if i == len(myglob):
          print 'rewriting all content to file :' + str(groupid) + '_group_plan_implementation.txt'
          content = apply_grouptags(content, str(groupid))
          open(common.outputdir + '/' + str(groupid) + '_group_plan_implementation.txt','w').write(content)
          break
       if (i >= gtsize ) and (i % gtsize == 0):
          print 'rewriting all above to file :' + str(groupid) + '_group_plan_implementation.txt'
          content = apply_grouptags(content, str(groupid))
          open(common.outputdir + '/' + str(groupid) + '_group_plan_implementation.txt','w').write(content)
          content = ''
          groupid += 1
       i += 1
            #with open(f, "r") as infile:
            #    logging.debug('Writing out: ' + f + ' to ' + consolidated_file)
            #    final_file.write(infile.read() + '\n\n')


def consolidate_plan(hosts, cluster, datacenter, superpod, casenum, role):
    # Consolidate all output into a single implementation plan.
    # This is the bit that tacks on the pre-post scripts

    logging.debug('Executing consolidate_plan()')
    if options.taggroups > 0:
            rewrite_groups(glob.glob(common.outputdir + "/*"), options.taggroups)
    consolidated_file = common.outputdir + '/plan_implementation.txt'
    print "Consolidating output into " + consolidated_file
    print 'Role :' +  role




    with open(consolidated_file, 'a') as final_file:
        if options.tags:
            final_file.write("BEGIN_DC: " + datacenter.upper() + '\n\n')

        if pre_file and not options.nested: #skip pre template for nested

            with open(pre_file, "r") as pre:
                pre = pre.read()
                pre = compile_template(pre, hosts, cluster, datacenter, superpod, casenum, role)

                logging.debug('Writing out prefile ' + pre_file + '  to ' + consolidated_file)
                final_file.write('BEGIN_GROUP: PRE\n' + pre + '\nEND_GROUP: PRE\n\n')

        # Append individual host files.


        read_files = glob.glob(common.outputdir + "/*")
        read_files.sort(key=humanreadable_key)
        for f in read_files:
            if f != common.outputdir + '/plan_implementation.txt':
                with open(f, "r") as infile:
                    logging.debug('Writing out: ' + f + ' to ' + consolidated_file)
                    final_file.write(infile.read() + '\n\n')

        if post_file and not options.nested: #skip post template for nested
            # Append postfile
            with open(post_file, "r") as post:
                post = post.read()
                post = compile_template(post, hosts, cluster, datacenter, superpod, casenum, role)
                logging.debug('Writing out post file ' + post_file + ' to ' + consolidated_file)
                final_file.write('BEGIN_GROUP: POST\n' + post + '\nEND_GROUP: POST\n\n')
        if options.tags:
                final_file.write("END_DC: " + datacenter.upper() + '\n\n')

    with open(consolidated_file, 'r') as resultfile:
        result = resultfile.readlines()


    return result

def cleanup_out():
    cleanup = glob.glob(common.outputdir + "/*")
    for junk in cleanup:
       os.remove(junk)

def gen_plan_by_idbquery(inputdict):

    #set defaults values
    assert 'datacenter' in inputdict, "must specify 1 or more datacenters"


    idbfilters = {}
    dcs = tuple(inputdict['datacenter'].split(','))
    idbfilters["cluster.dr"] = inputdict['dr'].split(',') if 'dr' in inputdict else 'False'
    idbfilters["cluster.operationalStatus"] = inputdict['cl_opstat'].split(',') if 'cl_opstat' in inputdict else 'ACTIVE'
    idbfilters["operationalStatus"] = inputdict['host_opstat'].split(',') if 'host_opstat' in inputdict else 'ACTIVE'

    #for key in ('datacenters','clusters','superpods','roles','clusterTypes','opstat','dr' ):

    if 'roles' in inputdict:
        idbfilters["deviceRole"] = inputdict['roles'].split(',')
    if 'clusters' in inputdict:
        idbfilters["cluster.name"] = inputdict['clusters'].split(',')
    if  'clusterTypes' in inputdict:
        idbfilters["cluster.clusterType"] = inputdict['clusterTypes'].split(',')
    if 'superpods' in inputdict:
        idbfilters["cluster.superpod.name"] = inputdict['superpods'].split(',')



    # optional paramters
    # defaults

    regexfilters = {}


    gsize = inputdict['maxgroupsize'] if 'maxgroupsize' in inputdict else 1

    grouping=['superpod']
    if 'grouping' in inputdict:
        grouping=grouping + inputdict['grouping'].split(',')


    template_id = 'AUTO'
    if 'templateid' in inputdict:
        template_id = inputdict['templateid']
    if template_id != "AUTO":
        assert os.path.isfile(common.templatedir + "/" + str(template_id) + ".template"), template_id + " template not found"

    if 'hostfilter' in inputdict:  # this is for backwards compatibility
        regexfilters['hostname'] = inputdict['hostfilter']

    if 'regexfilter' in inputdict:
        for pair in inputdict['regexfilter'].split(';'):
            field, regex = pair.split('=')
            field = field.lower() #for backward compatibility
            regexfilters[field] = regex

    print logging.debug('Regexfilters:')
    logging.debug( regexfilters )


    logging.debug(supportedfields)
    logging.debug(idbfilters)
    logging.debug(regexfilters)

    bph = Buildplan_helper(dcs,endpoint,supportedfields,idbfilters)
    bph.apply_regexfilters(regexfilters)
    writeplan = bph.apply_groups(grouping,template_id,gsize)
    consolidate_idb_query_plans(writeplan, dcs)

def consolidate_idb_query_plans(writeplan,dcs):

    allplans={}
    fullhostlist=[]
    writelist=[]
    ok_dclist=[]

    for template in writeplan:
        allplans[template] = {}
        for dc in dcs:
            if (dc,) not in writeplan[template].keys():
                continue
            allplans[template][dc] = write_plan_dc(dc,template,writeplan)
            ok_dclist.append(dc)


    logging.debug( allplans )
    for template in allplans:
        for dc in set(ok_dclist):
            if not dc in allplans[template].keys():
                continue
            content, hostlist = allplans[template][dc]
            writelist.extend(content)
            fullhostlist.extend(hostlist)


    write_list_to_file(common.outputdir + '/plan_implementation.txt', writelist, newline=False)

    global gblExcludeList

    if gblExcludeList:
        for excluded_host in gblExcludeList:
            while True:
                try:
                    fullhostlist.remove(str(excluded_host))
                except:
                    break
    write_list_to_file(common.outputdir + '/summarylist.txt', fullhostlist)

def write_plan_dc(dc,template_id,writeplan):

    global gblSplitHosts
    grouptagcount=0
    results=writeplan[template_id][(dc,)]
    i=0

    allhosts=[]
    allclusters=[]
    allsuperpods=[]
    allroles=[]

    template_vars = {}
    cleanup_out()
    for mygroup in sorted(results.keys()):
        for sizegroup in sorted(results[mygroup]):
            i+=1
            hostnames= results[mygroup][sizegroup]['hostname']
            superpod = ','.join(results[mygroup][sizegroup]['superpod'])
            clusters = results[mygroup][sizegroup]['cluster']
            roles = results[mygroup][sizegroup]['role']
            cluster_operationalstatus = results[mygroup][sizegroup]['cluster_operationalstatus']
            host_operationalstatus = results[mygroup][sizegroup]['host_operationalstatus']
            if options.monitor == True:
                template_vars['monitor-host'] = ','.join(results[mygroup][sizegroup]['monitor-host'])
            if options.serial == True:
                template_vars['serialnumber'] = ','.join(results[mygroup][sizegroup]['serialnumber'])
            template_vars['sitelocation'] = ','.join(results[mygroup][sizegroup]['sitelocation'])
            template_vars['drnostart_rrcmd'] = ','.join(results[mygroup][sizegroup]['drnostart_rrcmd'])
            template_vars['product_rrcmd'] = ','.join(results[mygroup][sizegroup]['product_rrcmd'])
            template_vars['ignored_process_names'] = ','.join(results[mygroup][sizegroup]['ignored_process_names'])
             #gather rollup info
            allhosts.extend(hostnames)
            allclusters.extend(clusters)
            allroles.extend(roles)
            allsuperpods.append(superpod)

            #fileprefix = str(group_enum) + str(i) + '_' + str(clusters)
            fileprefix = str(i)
            gblSplitHosts = build_dynamic_groups(hostnames)
            logging.debug(gblSplitHosts)

            prep_template(template_id, common.outputdir + '/' + fileprefix + "_plan_implementation.txt")
            gen_plan(','.join(hostnames).encode('ascii'), ','.join(clusters), dc, superpod, options.caseNum, ','.join(roles),i,','.join(cluster_operationalstatus),','.join(host_operationalstatus),\
                template_vars)

    consolidated_plan = consolidate_plan(','.join(set(allhosts)), ','.join(set(allclusters)), dc, ','.join(set(allsuperpods)), options.caseNum, ','.join(set(allroles)))

    print 'Template: '+ template_id
    return consolidated_plan, sorted(allhosts)

def get_clean_hostlist(hostlist):
    hostnames =[]
    dcs = []

    file = open(hostlist).readlines()
    for line in file:
        print line

        dc = line.split('-')[3].rstrip('\n')
        if dc not in dcs:
            dcs.append(dc)
        hostnames.append(line.rstrip('\n').rstrip())

    return dcs,hostnames

def gen_nested_plan_idb(hostlist, templates, regex_dict,group_dict,gsize):

    imp_plans = {
        'plan' : []
    }
    dcs, hostnames = get_clean_hostlist(hostlist)
    idbfilters = { 'name': hostnames }
    bph = Buildplan_helper(dcs,endpoint,supportedfields,idbfilters,True)
    for nestedtemplate in templates:
        if not os.path.isfile(common.templatedir +  '/' + nestedtemplate + '.template' ):
            continue
        regexfilters={}
        groups=[]
        refresh = False
        writeplan = bph.apply_groups(groups,nestedtemplate,gsize)
        print 'options:', regex_dict[nestedtemplate], group_dict[nestedtemplate]
        if regex_dict[nestedtemplate] != '':
            regexfilters= { "hostname" : regex_dict[nestedtemplate] }
            refresh = True
        if group_dict[nestedtemplate] != '':
            groups=[group_dict[nestedtemplate]]
            refresh = True
        print 'REfresh: ', True
        if refresh is True:
            bph.apply_regexfilters(regexfilters)
            writeplan = bph.apply_groups(grouping,templateid,gsize)
            bph.remove_regexfilters()
        consolidate_idb_query_plans(writeplan, dcs)
        imp_plans['plan'].extend( ['BEGIN_GROUP: ' + nestedtemplate.upper(), '\n'] )
        imp_plans['plan'].extend( open(common.outputdir + '/plan_implementation.txt').readlines() )
        imp_plans['plan'].extend( ['END_GROUP: ' + nestedtemplate.upper(), '\n', '\n'] )
    write_list_to_file(common.outputdir + '/plan_implementation.txt', imp_plans['plan'], newline=False)
    write_list_to_file(common.outputdir + '/summarylist.txt', hostnames , newline=True)

def gen_plan_by_hostlist_idb(hostlist, templateid, gsize, grouping):

    dcs, hostnames = get_clean_hostlist(hostlist)
    idbfilters = { 'name': hostnames }

    bph = Buildplan_helper(dcs,endpoint,supportedfields,idbfilters,True)
    writeplan = bph.apply_groups(grouping,templateid,gsize)
    consolidate_idb_query_plans(writeplan, dcs)

def gen_plan_by_hostlist(hostlist, templateid, gsize, groups):


    dcs, hostnames = get_clean_hostlist(hostlist)

    bph = Buildplan_helper(dcs,None, supportedfields,{},False,hostnames)
    writeplan = bph.apply_groups(groups,templateid,gsize)
    consolidate_idb_query_plans(writeplan, dcs)




###############################################################################
#                Main
###############################################################################
usage = """
            * Generate an implementation plan based on IDB data.

            ** This script can be called two ways:
                1.) Directly as ./%prog
                2.) Indirectly via hostgetter.py. See usage for hostgetter.py.

            Usage:

            - Process a hostlist in a sequential manner
            %prog -c 123 -l ../etc/hostlist -x -v

            - Process a hostlist in parallel
            %prog -c 123 -l ../etc/hostlist -x -a -v

            - Override the default (role name) template
            %prog -c 123 -l ../etc/hostlist -t spellchecker.glibc -x -a -v

            -get JSON file with all pods for geos for prod and DR
            %prog -g was,chi -o ~/outfile

            """



parser = OptionParser(usage)
parser.add_option("-c", "--case", dest="caseNum", help="The case number to use",
                      default='01234')
parser.add_option("-s", "--superpod", dest="superpod", help="The superpod")
parser.add_option("-S", "--status", dest="clusterstatus", \
                      help="The cluster status - PRIMARY/STANDBY", default="PRIMARY" )
parser.add_option("-i", "--clusterance", dest="cluster", help="The clusterance")
parser.add_option("-d", "--datacenter", dest="datacenter", help="The datacenter")
parser.add_option("-t", "--template", dest="template", default="AUTO", help="Override Template")
parser.add_option("-l", "--hostlist", dest="hostlist", help="Path to list of hosts", \
                      default='hostlist')
parser.add_option("-r", "--role", dest="role", help="Host role")
parser.add_option("-H", "--host", dest="host", help="The host")
parser.add_option("-f", "--filename", dest="filename", \
                      default="plan_implementation.txt", help="The output filename")
parser.add_option("-v", action="store_true", dest="verbose", default=False, \
                      help="verbosity")
parser.add_option("-e", action="store_true", dest="endrun", default=False, \
                      help="End the run and consolidate files")
parser.add_option("-m", dest="manual", default=False, \
                      help="Manually override idb")
parser.add_option("-a", action="store_true", dest="allatonce", default=False, \
                      help="End the run and consolidate files")
parser.add_option("-x", action="store_true", dest="skipidb", default=False, \
                      help="Use for testing idbhost")
parser.add_option("-G", "--idbgen", dest="idbgen", help="generate from idb")
parser.add_option("-C", "--cidblocal", dest="cidblocal", action='store_true', default=True, \
                      help="access cidb from your local machine")
parser.add_option("-g", "--geo", dest="geo", help="geo list" )
parser.add_option("-o", "--out", dest="out", help="output file")
parser.add_option("-M", dest="grouping", type="str", default="majorset,minorset" ,help="Turn on grouping")
parser.add_option("--gsize", dest="gsize", type="int", default=1, help="Group Size value")
parser.add_option("--bundle", dest="bundle", default="current", help="Patchset version")
parser.add_option("--monitor", dest="monitor", action="store_true", default=False, help="Monitor host")
parser.add_option("--serial", dest="serial", action="store_true", default=False, help="Monitor host")
parser.add_option("--concurr", dest="concur", type="int", help="Concurrency for kp_client batch")
parser.add_option("--failthresh", dest="failthresh", type="int", help="Failure threshold for kp_client batch")
parser.add_option("--nested_template", dest="nested", default=False, help="pass a list of templates, for use with hostlists only")
parser.add_option("--checkhosts", dest="checkhosts", action="store_true", default=False, help="Monitor host")
parser.add_option("--exclude", dest="exclude_list", default=False, help="Host Exclude List")
parser.add_option("-L", "--legacyversion", dest="legacyversion", default=False , action="store_true", help="flag to run new version of -G option")
parser.add_option("-T", "--tags", dest="tags", default=False , action="store_true", help="flag to run new version of -G option")
parser.add_option("--taggroups", dest="taggroups", type="int", default=0, help="number of sub-plans per group tag")
parser.add_option("--dowork", dest="dowork", help="command to supply for dowork functionality")

(options, args) = parser.parse_args()
if __name__ == "__main__":
  try:
      if options.serial == True:
         endpoint = 'hosts?'
         supportedfields['serialnumber'] = 'serialNumber'
      else:
         endpoint = 'allhosts?'
      if options.monitor == True:
          supportedfields['monitor-host'] =  ['cluster.clusterConfigs',  { 'key' : 'monitor-host' }]
      if not options.bundle:
          options.bundle = "current"

      if options.exclude_list:
          with open(options.exclude_list) as f:
              lines=f.read().splitlines()
          gblExcludeList=lines
      else:
          gblExcludeList=False

      if options.verbose:
          logging.basicConfig(level=logging.DEBUG)
      else:
          logging.basicConfig(level=logging.ERROR)

      if not os.path.exists(common.outputdir):
          logging.debug('Creating output dir')
          os.makedirs(common.outputdir)

      if options.geo:
          geolist = options.geo.split(',')
          get_dr_prod_by_dc(geolist, options.out)
          exit()

      if options.idbgen:
          inputdict = json.loads(options.idbgen)
          if options.legacyversion:
            gen_plan_by_cluster_hostnumber(inputdict)
            print "You ran the legacy version"
          else:
            gen_plan_by_idbquery(inputdict)
          exit()
      elif options.allatonce and not options.skipidb:
          cleanup_out()
          hosts = ','.join(get_hosts_from_file(options.hostlist))
          prep_template(options.template, common.outputdir + '/' + 'allhosts_' + options.filename)
          gen_plan(hosts, options.cluster, options.datacenter, options.superpod, options.caseNum, options.role)
          consolidate_plan(hosts, options.cluster, options.datacenter, options.superpod, options.caseNum, options.role)
          exit()

      if options.skipidb:
          # Clean up the old output files
          cleanup_out()

          if options.manual:
              print('Overriding IDB with data from {0}'.format(options.manual))
              json_data=open(options.manual).read()
              data=json.loads(json_data)
              options.role=data["role"]
              options.cluster=data["cluster"]
              options.superpod=data["superpod"]
              options.caseNum=data["casenum"]
              role=options.role
              cluster=options.cluster
              superpod=options.superpod
              casenum=options.caseNum

              hosts = get_hosts_from_file(options.hostlist)
              gblSplitHosts = build_dynamic_groups(hosts)

              if options.allatonce:
              # process the plan in parallel
                  hostnames = []
                  for hostname in hosts:
                      outfile = common.outputdir + '/allhosts_plan_implementation.txt'
                      hostnames.append(hostname)
                      datacenter = hostname.rsplit('-', 1)[1]

                      if options.template:
                          template = options.template
                      else:
                          template = role

                      allhosts = ','.join(hostnames)
                      hosts = allhosts
                      prep_template(template, outfile)
                      gen_plan(hosts, cluster, datacenter, superpod, casenum, role)

              else:

                  # process the plan in series
                  for hostname in hosts:
                      outfile = common.outputdir + '/' + hostname + '_plan_implementation.txt'
                      hosts = hostname
                      datacenter = hostname.rsplit('-', 1)[1]

                  if options.template:
                      template = options.template
                  else:
                      template = role

                  prep_template(template, outfile)
                  gen_plan(hosts, cluster, datacenter, superpod, casenum, role)

              consolidate_plan(hosts, cluster, datacenter, superpod, casenum, role)
              exit()
          if options.grouping:
              gen_plan_by_hostlist(options.hostlist, options.template, options.gsize,options.grouping.split(','))
              exit()

      if options.nested and options.hostlist:
          groups = options.grouping.split(',')
          templates = open(common.templatedir + "/" + options.nested +'.template').readlines()
          regex_dict = {}
          grouping_dict = {}
          template_list = []
          for template in templates:
              values = template.strip().split(':')
              hostregex=''
              groupby=''
              if len(values) == 3:
                  temp, groupby, hostregex = values
              else:
                  temp = values[0]
              grouping_dict[temp] = groupby
              regex_dict[temp]=hostregex
              template_list.append(temp)
          gen_nested_plan_idb(options.hostlist, template_list, regex_dict, grouping_dict, options.gsize)
          exit()

      if options.hostlist:
          groups = options.grouping.split(',')

          if not options.template:
              options.template='AUTO'
          print options.hostlist
          gen_plan_by_hostlist_idb(options.hostlist, options.template, options.gsize,groups)
          exit()

      if options.endrun:
          # This hack will go away once Mitchells idbhelper module is merged.
          prep_template(options.template,options.filename)
          consolidate_plan(options.host, options.cluster, options.datacenter, options.superpod, options.caseNum, options.role)
      elif not options.idbgen:
          prep_template(options.template, options.filename)
          gen_plan(options.host, options.cluster, options.datacenter, options.superpod, options.caseNum, options.role)

  except Exception:
      cleanup_out()
      raise
else:
    #default options for build_plan unit test
    options.idbgen=True
    gblExcludeList=False