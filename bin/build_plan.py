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
import urllib2
import logging
import re
import glob
import os.path
import logging
import pprint
from common import Common
from idbhost import Idbhost
from buildplan_helper import Buildplan_helper



###############################################################################
#                Constants
###############################################################################
templatefile = ''
out_file = ''
pre_file = ''
post_file = ''
hosts = []
hostlist = []

iDBurl = {'asg': "https://inventorydb1-0-asg.data.sfdc.net/api/1.03",
          'chi': "https://inventorydb1-0-chi.data.sfdc.net/api/1.03",
          'chx': "https://inventorydb1-0-chx.data.sfdc.net/api/1.03",
          'lon': "https://inventorydb1-0-lon.data.sfdc.net/api/1.03",
          'sfm': "https://inventorydb1-0-sfm.data.sfdc.net/api/1.03",
          'sjl': "https://inventorydb1-0-sjl.data.sfdc.net/api/1.03",
          'tyo': "https://inventorydb1-0-tyo.data.sfdc.net/api/1.03",
          'was': "https://inventorydb1-0-was.data.sfdc.net/api/1.03",
          'wax': "https://inventorydb1-0-wax.data.sfdc.net/api/1.03",
          'frf': "https://inventorydb1-0-frf.data.sfdc.net/api/1.03",
          'phx': "https://inventorydb1-0-phx.data.sfdc.net/api/1.03",
          'dfw': "https://inventorydb1-0-dfw.data.sfdc.net/api/1.03",
          'cidb': "https://cidb1-0-sfm.data.sfdc.net/cidb-api/1.03",
          }

supportedfields = { 'superpod' : 'cluster.superpod.name',
                  'role' : 'deviceRole',
                  'cluster' : 'cluster.name',
                  'hostname' : 'name',
                  'failoverstatus' : 'failOverStatus',
                  'dr' : 'cluster.dr',
                  'host_operationalstatus': 'operationalStatus',
                  'cluster_operationalstatus': 'cluster.operationalStatus',
                  'clustertype' : 'cluster.clusterType'
                 }

cache = dict()

###############################################################################
#                Functions
###############################################################################
# Instanciate Common.

common = Common()


def idb_connect():
    try:
        logging.debug('Connecting to CIDB')
        idb = Idbhost()
        return idb
    except:
        print "Unable to connect to idb"
        exit()

def get_hosts_from_file(filename):
    try:
        with open(filename) as f:
            hostlist = f.read().splitlines()
    except:
        print "Unable to open host list file"
        exit()
    return hostlist

def get_hosts_from_file_idb(filename):
    idb = idb_connect()

    hostlist = get_hosts_from_file(filename)

    try:
        idb.gethost(hostlist)
        hosts = idb.mlist
    except:
        print "Unable to query IDB for hosts"
        exit()

    return hosts


def write_list_to_file(filename, list, newline=True):
    if newline:
        s = '\n'.join(list)
    else:
        s = ''.join(list)
    f = open(filename, 'w')
    f.write(s)
    f.close()


def build_dynamic_groups(hosts):

    # Cut up the hostlist by the values stored in ../etc/host_regex.json
    # to generate more complex plans.

    outmap = {}
    with open('../etc/host_regex.json') as data_file:
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


def compile_template(input, hosts, cluster, datacenter, superpod, casenum, role, cl_opstat='',ho_opstat=''):
    # Replace variables in the templates
    logging.debug('Running compile_template')

    output = input

    global gblSplitHosts
    global gblExcludeList

    #before default ids in case of subsets
    for key, hostlist in gblSplitHosts.iteritems():
        output = output.replace(key, ",".join(hostlist))    

    hlist=hosts.split(",")

    if gblExcludeList:
        for excluded_host in gblExcludeList:
            while True:
                try:
                    hlist.remove(str(excluded_host))
                except:
                    break
    hosts=",".join(hlist )

    output = output.replace('v_HOSTS', hosts)
    output = output.replace('v_CLUSTER', cluster)
    output = output.replace('v_DATACENTER', datacenter)
    output = output.replace('v_SUPERPOD', superpod)
    output = output.replace('v_CASENUM', casenum)
    output = output.replace('v_ROLE', role)
    output = output.replace('v_BUNDLE', options.bundle)
    output = output.replace('v_CL_OPSTAT', cl_opstat)
    output = output.replace('v_HO_OPSTAT', ho_opstat)

    return output

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



def gen_plan(hosts, cluster, datacenter, superpod, casenum, role,groupcount=0,cl_opstat='',ho_opstat=''):
    # Generate the main body of the template (per host)
    logging.debug('Executing gen_plan()')
    print "Generating: " + out_file
    
    s = open(template_file).read()

    s = compile_template(s, hosts, cluster, datacenter, superpod, casenum, role, cl_opstat,ho_opstat)
    if groupcount > 0 and options.tags:
        s = apply_grouptags(s, str(groupcount))

    f = open(out_file, 'w')
    f.write(s)
    f.close()

def tryint(s):
    try:
        return int(s)
    except:
        return s

def humanreadable_key(s):
    if isinstance(s, tuple):
        s = str(s)

    return [ tryint(c) for c in re.split('([0-9]+)', s) ]

def apply_grouptags(content,tag_id):
    return 'BEGIN_GROUP: ' + tag_id + '\n\n' + content + '\n\n' + \
                                'END_GROUP: ' + tag_id + '\n\n'
    

def consolidate_plan(hosts, cluster, datacenter, superpod, casenum, role):
    # Consolidate all output into a single implementation plan.
    # This is the bit that tacks on the pre-post scripts

    logging.debug('Executing consolidate_plan()')
    consolidated_file = common.outputdir + '/plan_implementation.txt'
    print "Consolidating output into " + consolidated_file
    print 'Role :' +  role

    with open(consolidated_file, 'a') as final_file:
        if options.tags:
            final_file.write("BEGIN_DC: " + datacenter.upper() + '\n\n')

        if pre_file:
            with open(pre_file, "r") as pre:
                pre = pre.read()
                pre = compile_template(pre, hosts, cluster, datacenter, superpod, casenum, role)
                if options.tags:    
                    pre = apply_grouptags(pre, 'PRE')
                    
                logging.debug('Writing out prefile ' + pre_file + '  to ' + consolidated_file)
                final_file.write(pre + '\n\n')

        # Append individual host files.
        read_files = glob.glob(common.outputdir + "/*")

        read_files.sort(key=humanreadable_key)
        for f in read_files:
            if f != common.outputdir + '/plan_implementation.txt':
                with open(f, "r") as infile:
                    logging.debug('Writing out: ' + f + ' to ' + consolidated_file)
                    final_file.write(infile.read() + '\n\n')

        if post_file:
            # Append postfile
            with open(post_file, "r") as post:
                post = post.read()
                post = compile_template(post, hosts, cluster, datacenter, superpod, casenum, role)
                if options.tags:
                    post = apply_grouptags(post, 'POST')
                logging.debug('Writing out post file ' + post_file + ' to ' + consolidated_file)
                final_file.write(post + '\n\n')
        if options.tags:
                final_file.write("END_DC: " + datacenter.upper() + '\n\n')

    with open(consolidated_file, 'r') as resultfile:
        result = resultfile.readlines()


    return result

def gen_request(reststring, cidblocal=False, derivedc='', debug=False):
    # Build the API URL
    dc = derivedc.lower()
    if cidblocal:
        # CIDB URL is slightly different, so it needs to be cut up and
        # reassembled.
        derivever = iDBurl['cidb'].split('/')[4]
        derivemethod = iDBurl['cidb'].split('/')[0]
        derivehost = iDBurl['cidb'].split('/')[2]
        derivepath = iDBurl['cidb'].split('/')[3]
        url = derivemethod + '//' + derivehost + '/' + \
        derivepath + '/' + dc + '/' + derivever + reststring
        # Use the java cli tool to sign the CIDB request and return a
        # keyed URL.
        url = os.popen('java -jar ' + common.cidb_jar_path + '/cidb-security-client-0.0.3.jar ' + common.cidb_jar_path + '/keyrepo "' + url + '"').read()
    else:
        url = iDBurl[dc] + reststring

    print url
    logging.debug(url)

    # Send the request.
    r = urllib2.urlopen(url)
    # use the data.
    data = json.load(r)
    if debug:
        logging.debug(data)
        logging.debug(data['total'])
    if data['total'] == 1000:
        raise Exception('idb record limit of 1000, you may be missing records')

    return data

def cacher(current_obj, arglist):
    # loop through fields from left to right caching ibased on JacksonId if they point to a json object returning if they are cached
    for arg in arglist:
        if type(current_obj[arg]) is unicode:
          current_obj = cache[current_obj[arg]]
        else:
          current_obj = current_obj[arg]
          cache[current_obj['@' + arg + 'JacksonId']] = current_obj
    return current_obj

    #write_list_to_file(common.outputdir + '/summarylist.txt', [totalhosts)


def get_hosts_by_enum(clusterlist, dr, dc, roles, grouping, cidblocal=True, debug=False):
    superpods = dict()
    assert grouping.values() != [False, False, False, False, False], "must group by at least one value"
    for cluster in clusterlist:
        for role in roles:
          # pass2 get deviceroles and hostlists back and assign to the correct cluster
            reststring = '/allhosts?operationalStatus=active&cluster.dr=' + str(dr).lower() + '&deviceRole=' + role + '&cluster.name=' + cluster + '&fields=name,deviceRole,failOverStatus,cluster.name,cluster.superpod.name&expand=cluster'
            current = gen_request(reststring, cidblocal, dc, debug)
            if current['total'] > 0:
              for hval in current['data']:
                  sptemp = cacher(hval, ['cluster', 'superpod'])['name']
                  minorset = hval['name'].split('-')[2]
                  majorset = ''.join([s for s in hval['name'].split('-')[1] if s.isdigit()])
                  list_ident_temp = ''
                  if grouping['failOverStatus'] == True:
                      list_ident_temp = hval['failOverStatus']
                  if grouping['cluster'] == True:
                      list_ident_temp = list_ident_temp + cluster
                  if grouping['role'] == True:
                      list_ident_temp = list_ident_temp + '-' + role
                  if grouping['majorset'] == True:
                      list_ident_temp = list_ident_temp + '-' + majorset
                  if grouping['minorset'] == True:
                      list_ident_temp = list_ident_temp + '-' + minorset
                  print list_ident_temp

                  if sptemp not in superpods:
                      superpods[sptemp] = {}
                  if list_ident_temp not in superpods[sptemp]:
                      superpods[sptemp][list_ident_temp] = {}
                  print hval['name']
                  superpods[sptemp][list_ident_temp][hval['name']] = {
                       # add more per host values as necessary
                      'clustername' : cacher(hval, ['cluster'])['name'],
                      'rolename' : hval['deviceRole'],
                      'failOverStatus' : hval['failOverStatus']

                  }

      # assign hosts to device roles after splitting into groups per maxgroupsize
    j = json.dumps(superpods)
    pprint.pprint(j, indent=2)
    return j


def chunks(l, n):
    n = max(1, n)
    return [l[i:i + n] for i in range(0, len(l), n)]

def regex_filter_list(contents, fielddict):

    if len(fielddict.keys()) == 0:
        return contents.keys()
    templist = []
    for field in fielddict:
        regex = fielddict[field]
        if field == 'hostfilter':
            # go through each key and see is there a match
            templist = [k for k in sorted(contents.keys()) if re.match(regex, k)]
        else:
            # else check the field specified leaving us open for many fields
            templist = [k for k in sorted(contents.keys()) if re.match(regex, contents[k][field])]

    # OR evaluation for now
    return list(set(templist))


def merge(source, destination):
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            merge(value, node)
        elif isinstance(value, list):
            destination[key] = destination[key] + value if (key in destination) else value
        else:
            destination[key] = value

    return destination





def gen_plan_by_cluster_hostnumber(inputdict):
    global gblSplitHosts
    dc = inputdict['datacenter']
    roles = inputdict['roles'].split(',')
    clusters = inputdict['clusters'].split(',')
    # optional paramters
    # defaults
    template_id = ''
    grouping = {
              "failOverStatus" : False,
              "cluster" : False,
              "role" : False,
              "majorset" : False,
              "minorset" : False
        }
    fielddict = {}
    dr = inputdict['dr'] if 'dr' in inputdict else False
    template_suffix = '.' + inputdict['template_suffix'] if 'template_suffix' in inputdict else ''
    gsize = inputdict['maxgroupsize'] if 'maxgroupsize' in inputdict else 1

    if 'grouping' in inputdict:
      for grp in inputdict['grouping'].split(','):
        if grp in grouping.keys():
            grouping[grp] = True

    if 'templateid' in inputdict:
       template_id = inputdict['templateid']
    elif len(roles) > 1:
       raise Exception('if you have specified more than one role you need a template')

    if 'hostfilter' in inputdict:  # this is for backwards compatibility
        assert 'regexfilter' not in inputdict, "cannot specify hostfilter and regexfilter at the same time"
        inputdict['regexfilter'] = 'hostfilter=' + inputdict['hostfilter']

    if 'regexfilter' in inputdict:
        field, regex = inputdict['regexfilter'].split('=')
        fielddict[field] = regex

    cleanup_out()
    results = json.loads(get_hosts_by_enum(clusters, dr, dc, roles, grouping, cidblocal=True, debug=False))
    # generate template
    fullhostlist = []
    ro = ''
    i = 0
    sp = 'none'
    for sp in results.keys():
       for host_enum in sorted(results[sp].keys()):
           for hostnames in chunks(regex_filter_list(results[sp][host_enum], fielddict), gsize):
                fullhostlist.extend(hostnames)
                cl = ','.join(set([results[sp][host_enum][host]['clustername'] for host in hostnames]))
                ro = ','.join(set([results[sp][host_enum][host]['rolename'] for host in hostnames]))
                i += 1
                fileprefix = str(i)
                print 'myprefix : ' + fileprefix
                # build individual plans setting template to role name unless a template is specified
                # want to use template for role by default unless overridden
                template_id = ro + template_suffix if len(template_id) == 0 else template_id + template_suffix
                # template_id = template_id + '.dr' if dr else template_id

                gblSplitHosts = build_dynamic_groups(hostnames)
                logging.debug(gblSplitHosts)

                prep_template(template_id, common.outputdir + '/' + fileprefix + "_plan_implementation.txt")
                gen_plan(','.join(hostnames).encode('ascii'), cl, dc, sp, options.caseNum, ro)

    consolidate_plan(','.join(fullhostlist), ','.join(clusters), dc, sp, options.caseNum, ro)

    global gblExcludeList

    if gblExcludeList:
        for excluded_host in gblExcludeList:
            while True:
                try:
                    fullhostlist.remove(str(excluded_host))
                except:
                    break
    write_list_to_file(common.outputdir + '/summarylist.txt', fullhostlist)

def cleanup_out():
    cleanup = glob.glob(common.outputdir + "/*")
    for junk in cleanup:
       os.remove(junk)

def get_dr_prod_by_dc(dclist, filename, cidblocal=True):
    idb = idb_connect()
    idb.poddata(dclist)
    dcs = idb.dcs

    if filename:
        with open(filename, 'w') as outfile:
            json.dump(dcs, outfile)

        with open(filename) as json_data:
            d = json.load(json_data)
            json_data.close()
            pp = pprint.PrettyPrinter(indent=2)

        pp.pprint(d)

        return json.dumps(dcs, indent=2)


def chunks_tuple_list(tlist, n):
    #convert and group a list of tuples
    l=[el for tup in tlist for el in tup]
    n = max(1, n)
    return [l[i:i + n] for i in range(0, len(l), n)]

    

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
        regexfilters['name'] = inputdict['hostfilter']

    if 'regexfilter' in inputdict:
        for pair in inputdict['regexfilter'].split(';'):
            field, regex = pair.split('=')
            regexfilters[field] = regex
            
    print logging.debug('Regexfilters:')
    logging.debug( regexfilters )

    
    logging.debug(supportedfields)
    logging.debug(idbfilters)
    logging.debug(regexfilters)

    bph = Buildplan_helper('allhosts?', supportedfields,True)
    writeplan = bph.prep_idb_plan_info(dcs,idbfilters,regexfilters,grouping,template_id)
    consolidate_idb_query_plans(writeplan, dcs, gsize)

def consolidate_idb_query_plans(writeplan,dcs,gsize):

    allplans={}
    fullhostlist=[]
    writelist=[]
    ok_dclist=[]

    logging.debug(dcs)

    for template in writeplan:
        allplans[template]={}
        for dc in dcs:
            if (dc,) not in writeplan[template].keys():
                continue
            allplans[template][dc] = write_plan_dc(dc,template,writeplan,gsize)
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

def write_plan_dc(dc,template_id,writeplan,gsize):

    global gblSplitHosts
    results=writeplan[template_id][(dc,)]
    i=0

    allhosts=[]
    allclusters=[]
    allsuperpods=[]
    allroles=[]

    cleanup_out()
    for group_enum in sorted(results.keys()):

        superpod= group_enum[0]
        #superpod always first group field
        for hostnames in chunks_tuple_list(sorted(results[group_enum].keys(),key=humanreadable_key),gsize):
                #gather node info
            i += 1
            clusters = set([results[group_enum][(host,)]['cluster'] for host in hostnames])
            roles = set([results[group_enum][(host,)]['role'] for host in hostnames])
            cluster_operationalstatus = set([results[group_enum][(host,)]['cluster_operationalstatus'] for host in hostnames])
            host_operationalstatus = set([results[group_enum][(host,)]['host_operationalstatus'] for host in hostnames])
            
            #gather rollup info
            allhosts.extend(hostnames)
            allclusters.extend(clusters)
            allroles.extend(roles)
            allsuperpods.append(superpod)
            #increment groupid

            #fileprefix = str(group_enum) + str(i) + '_' + str(clusters)
            fileprefix = str(i)
            gblSplitHosts = build_dynamic_groups(hostnames)
            logging.debug(gblSplitHosts)

            prep_template(template_id, common.outputdir + '/' + fileprefix + "_plan_implementation.txt")
            gen_plan(','.join(hostnames).encode('ascii'), ','.join(clusters), dc, superpod, options.caseNum, ','.join(roles),i,','.join(cluster_operationalstatus),','.join(host_operationalstatus))

    consolidated_plan = consolidate_plan(','.join(set(allhosts)), ','.join(set(allclusters)), dc, ','.join(set(allsuperpods)), options.caseNum, ','.join(set(allroles)))

    return consolidated_plan, sorted(allhosts)

def gen_plan_by_hostlist_idb(hostlist, templateid, gsize, grouping):
    hostnames =[]
    dcs = []
    
    file = open(hostlist).readlines()
    for line in file:
        dc = line.split('-')[3].rstrip('\n')
        if dc not in dcs:
            dcs.append(dc)
        hostnames.append(line.rstrip('\n'))
    idbfilters = { 'name': hostnames }
    
    
    bph = Buildplan_helper('allhosts?', supportedfields,True,True)
    writeplan = bph.prep_idb_plan_info(dcs,idbfilters,{},groups,templateid)
    consolidate_idb_query_plans(writeplan, dcs, gsize)
    
def gen_plan_by_hostlist(hostlist, templateid, gsize, groups):
    hostnames =[]
    dcs = []
    
    file = open(hostlist).readlines()
    for line in file:
        dc = line.split('-')[3].rstrip('\n')
        if dc not in dcs:
            dcs.append(dc)
        hostnames.append(line.rstrip('\n'))
    
    
    bph = Buildplan_helper('', supportedfields,True,True)
    writeplan = bph.prep_plan_info_hostlist(hostnames,groups,templateid)
    consolidate_idb_query_plans(writeplan, dcs, gsize)
            
        
    

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
parser.add_option("-t", "--template", dest="template", help="Override Template")
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
parser.add_option("--exclude", dest="exclude_list", default=False, help="Host Exclude List")
parser.add_option("-L", "--legacyversion", dest="legacyversion", default=False , action="store_true", help="flag to run new version of -G option")
parser.add_option("-T", "--tags", dest="tags", default=False , action="store_true", help="flag to run new version of -G option")
(options, args) = parser.parse_args()
if __name__ == "__main__":

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

    if not os.path.exists('../output'):
        logging.debug('Creating output dir')
        os.makedirs('../output')

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


