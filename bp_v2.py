#!/usr/bin/python
#
#
import requests
import re
import pprint
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from modules.grouper import Groups
import sys
import glob
import os
import argparse
import logging
import json
import os
import re
from caseToblackswan import CreateBlackswanJson

pp = pprint.PrettyPrinter(indent=2)


def tryint(s):
    """
        convert key to string for ordering using humanreadable_key
    """
    try:
        return int(s)
    except:
        return s

def sort_key(s):
    """
        function for sorting lists of values to make them readable from left to right
    """
    s = str(s)

    return [ tryint(c) for c in re.split('([0-9]+)', s) ]

def get_data(cluster, role, dc):
    '''
    Function queries blackswan for data. It then strips the necessary information and recreates it
    into the master_json dictionary.
    :return:
    '''
    master_json = {}
    ice_chk = re.compile(r'ice|mist')

    if cluster != "NA":
        url = "https://ops0-cpt1-2-prd.eng.sfdc.net:9876/api/v1/hosts?cluster={}&role={}&dc={}".format(cluster, role, dc)
    else:
        url = "https://ops0-cpt1-2-prd.eng.sfdc.net:9876/api/v1/hosts?role={}&dc={}".format(role, dc)

    response = requests.get(url, verify=False)
    if response.json() is None:
        logging.error("No Data Present")
        sys.exit(1)
    else:
        data = response.json()

    for hostname in data:
        if hostname['clusterStatus'] == cl_status and hostname['hostStatus'] == ho_status and \
                hostname['patchCurrentRelease'] != options.bundle:
            try:
                if hostname['hostCaptain']:
                    logging.debug("Excluding Captain owned host: {}".format(hostname['hostName']))
            except KeyError:
                master_json[hostname['hostName']] = {'RackNumber': hostname['hostRackNumber'],
                                                     'Role': hostname['roleName'],
                                                     'Bundle': hostname['patchCurrentRelease'],
                                                     'Majorset': hostname['hostMajorSet'],
                                                     'Minorset': hostname['hostMinorSet']}
        else:
            logging.debug("{}: Current Bundle:{} Cluster Status:{} Host Status:{}".format(hostname['hostName'],
                                                                                          hostname['patchCurrentRelease'],
                                                                                          hostname['clusterStatus'],
                                                                                          hostname['hostStatus']))

    logging.debug("Master Json {}".format(master_json))
    if not master_json:
        logging.error("All Hosts are current at {} bundle".format(options.bundle))
        sys.exit(1)
    else:
        #master_json = ice_chk(master_json)
        master_json = hostfilter_chk(master_json)

    if not master_json:
        logging.error("No servers match any filters.")
        sys.exit(1)

    return master_json

def hostfilter_chk(data):
    if hostfilter:
        host_filter = re.compile(r'{}'.format(hostfilter))
        for host in data.keys():
            if not host_filter.match(host):
                logging.debug("{} does not match ...".format(host))
                del data[host]
    return data

def ice_mist_check(hostname):
    ice_chk = re.compile(r'ice|mist|^stm')

    if options.ice:
        if ice_chk.match(hostname):
            logging.debug("Host matches skipping...")
            return 1
        else:
            return 0

def validate_templates(tempalteid):
    '''
    This functions validates that all templates are in place.
    :return:
    '''
    #check if templates exist
    ######
    template = "{}/templates/{}.template".format(os.getcwd(), templateid)
    template_1 = "{}/templates/{}.template.pre".format(os.getcwd(), templateid)
    template_2 = "{}/templates/{}.template.post".format(os.getcwd(), templateid)
    work_template = "{}/templates/{}.template".format(os.getcwd(), options.dowork)

    if not os.path.isfile(template) or not os.path.isfile(work_template):
        logging.error("No such file or directory")
        sys.exit(1)

    pre_template = template_1 if os.path.isfile(template_1) else "{}/templates/generic.pre".format(os.getcwd())
    post_template = template_2 if os.path.isfile(template_2) else "{}/templates/generic.post".format(os.getcwd())

    logging.debug("Defined Templates")
    logging.debug(template)
    logging.debug(work_template)
    logging.debug(pre_template)
    logging.debug(post_template)

    return template, work_template, pre_template, post_template

def prep_template(work_template, template):
    '''
    This function does the prep work to the template by adding the comment line and block v_NUM.
    :return:
    '''
    with open(work_template, 'r') as do:
        dw = do.read()

    with open(template, 'r') as out:
        output = out.read()
        output = output.replace('v_INCLUDE', dw)

    """This code is to add unique comment to each line in implementation plan.
             e.g - release_runner.pl -forced_host $(cat ~/v_CASE_include) -force_update_bootstrap -c sudo_cmd -m "ls" -auto2 -threads
             -comment 'BLOCK 1'"""
    if 'v_COMMAND' not in output and 'mkdir ' not in output:
        o_list = output.splitlines(True)
        for i in range(len(o_list)):
            # Added to skip linebacker -  W-3779869
            if not options.nolinebacker:
                regex_compile = re.compile('bigipcheck|remove_from_pool|add_to_pool', re.IGNORECASE)
                if regex_compile.search(o_list[i]):
                    o_list[i] = o_list[i].strip() + ' -nolinebacker' + "\n"
            if o_list[i].startswith('release_runner.pl') and 'BLOCK' not in o_list[i]:
                cmd = o_list[i].strip() + ' -comment ' + "'BLOCK v_NUM'\n"
                o_list.remove(o_list[i])
                o_list.insert(i, cmd)
            elif o_list[i].startswith('Exec_with') and 'BLOCK' not in o_list[i]:
                cmd = "Exec_with_creds: " + o_list[i][
                                            o_list[i].index(':') + 1:].strip() + " && echo 'BLOCK v_NUM'\n"
                o_list.remove(o_list[i])
                o_list.insert(i, cmd)
            elif o_list[i].startswith('Exec') and 'BLOCK' not in o_list[i]:
                cmd = "Exec: echo 'BLOCK v_NUM' && " + o_list[i][o_list[i].index(':') + 1:]
                o_list.remove(o_list[i])
                o_list.insert(i, cmd)
        output = "".join(o_list)

    return output

def compile_template(new_data, value, template, work_template, file_num):
    '''
    This function put the template together subsititue variables with information it obtain from
    command line and blackswan.
    :return:
    '''
    outfile = os.getcwd() + "/output/{}_plan_implementation.txt".format(file_num)
    output = prep_template(work_template, template)
    if 'v_COMMAND' not in output and 'mkdir ' not in output:
        output = output.replace('v_HOSTS', '$(cat ~/v_CASE_include)')
        output_list = output.splitlines(True)
        if role != "secrets":
            output_list.insert(1, '\n- Verify if hosts are patched or not up\nExec: echo "Verify hosts BLOCK v_NUM" && '
                                  '/opt/cpt/bin/verify_hosts.py -H v_HOSTS --bundle v_BUNDLE --case v_CASE\n\n')
        output = "".join(output_list)
    output = output.replace('v_CLUSTER', new_data['Details']['cluster'])
    output = output.replace('v_DATACENTER', new_data['Details']['dc'])
    output = output.replace('v_SUPERPOD', new_data['Details']['Superpod'])
    output = output.replace('v_ROLE', new_data['Details']['role'])
    output = output.replace('v_HO_OPSTAT', new_data['Details']['ho_status'])
    output = output.replace('v_CL_OPSTAT', new_data['Details']['cl_status'])
    output = output.replace('v_BUNDLE', options.bundle)
    output = output.replace('v_HOSTS', ','.join(value))
    output = output.replace('v_NUM', str(file_num))
    f = open(outfile, 'w')
    f.write(output)
    f.close()
    for t in value:
        sum_file.write(t + "\n")

def create_masterplan(consolidated_file, pre_template):
    '''
    This function basically takes all the plans in the output directory and consolidates
    them into one plan.
    :return:
    '''
    read_files = glob.glob(os.getcwd() + "/output/*_implementation.txt")
    read_files.sort(key=sort_key)
    logging.debug(read_files)
    try:
        logging.debug("Removing Old file {}".format(consolidated_file))
        os.remove(consolidated_file)
    except OSError:
        pass
    final_file = open(consolidated_file, 'a')
    with open(pre_template, "r") as pre:
        pre = pre.read()
        final_file.write('BEGIN_GROUP: PRE\n' + pre + '\nEND_GROUP: PRE\n\n')

    for f in read_files:
        if f != consolidated_file:
            with open(f, "r") as infile:
                #print('Writing out: ' + f + ' to ' + consolidated_file)
                final_file.write(infile.read() + '\n\n')

    post = "- Auto close case \nExec_with_creds: /opt/cpt/gus_case_mngr.py -c v_CASE --close -y\n\n"
    final_file.write('BEGIN_GROUP: POST\n' + post + '\nEND_GROUP: POST\n\n')
    cleanup()


def cleanup():
    '''
    This function is a cleanup routine for the output directory.
    :return:
    '''
    cleanup = glob.glob(os.getcwd() + "/output/*_plan_implementation.txt")
    logging.debug("Cleaning up output directory")
    for junk in cleanup:
        if junk != consolidated_file:
            os.remove(junk)

def group_worker(templateid, new_data, gsize):
    '''
    "This function is responsible for doing the work assoicated with the gsize variable.
    it ensures the number of host done in parallel are translated correctly into the v_HOSTS
    variable.
    :param templateid:
    :param new_data:
    :param grouping:
    :param gsize:
    :return:
    '''
    host_group = []
    file_num = 1
    outfile = os.getcwd() + "/output/{}_plan_implementation.txt".format(file_num)

    template, work_template, pre_template, post_template = validate_templates(templateid)
    for key in sorted(new_data['Hostnames'].keys()):
        for host in new_data['Hostnames'][key]:
            host_group.append(host)
            if len(host_group) == gsize:
                logging.debug(host_group)
                logging.debug("File_Num: {}".format(file_num))
                compile_template(new_data, host_group, template, work_template, file_num)
                host_group = []
                file_num = file_num + 1
            elif host == new_data['Hostnames'][key][-1]:
                logging.debug(host_group)
                logging.debug("File_Num: {}".format(file_num))
                compile_template(new_data, host_group, template, work_template, file_num)
                file_num = file_num + 1
                host_group = []
    sum_file.close()
    create_masterplan(consolidated_file, pre_template)

def main_worker(templateid, new_data):
    '''
    This fucntions works with the byrack data. It just prints the contents of the
    value from the new_data dictionary to populate the v_HOSTS variable. Probably needs
    to be renamed.
    :param templateid:
    :param new_data:
    :param file_num:
    :return:
    '''
    file_num = 1

    template, work_template, pre_template, post_template = validate_templates(templateid)
    for pri in new_data['Grouping'].iterkeys():
        for key, value in new_data['Grouping'][pri].iteritems():
            compile_template(new_data, value, template, work_template, file_num)
            file_num = file_num + 1
    sum_file.close()
    create_masterplan(consolidated_file, pre_template)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build_Plan")
    group1 = parser.add_argument_group('Standard', 'Command Line Options')
    group2 = parser.add_argument_group('Advanced', 'Additonal Parameters')
    group1.add_argument("-r", "--role", dest="role", help="Device RoleName")
    group1.add_argument("-d", "--datacenter", dest="dc", help="Datacenter")
    group1.add_argument("-p", "--pod", dest="pod", help="Superpod")
    group1.add_argument("-c", "--cluster", dest="cluster", help="Cluster")
    group1.add_argument("-t", "--template", dest="templateid", help="Template")
    group1.add_argument("-g", "--grouping", dest="grouping", help="Host Grouping (majorset|minorset|byrack)")
    group1.add_argument("--maxgroupsize", dest="maxgroupsize", help="# of servers in parallel")
    group1.add_argument("--dr", dest="dr", action="store_true", default=False, help="DR Host only")
    group1.add_argument("--bundle", dest="bundle", default="current", help="Patchset version")
    group1.add_argument("--gsize", dest="gsize", default=1, help="Group Size value")
    group1.add_argument("--dowork", dest="dowork", help="command to supply for dowork functionality")
    group1.add_argument("-G", "--idbgen", dest="idbgen", help='Create json string for input (i.e \'{"dr": "FALSE", "datacenter": "prd", "roles": "sdb", "templateid": "sdb", "grouping": "majorset", "maxgroupsize": 1}\')')
    group2.add_argument("--taggroups", dest="taggroups", default=0, help="number of sub-plans per group tag")
    group2.add_argument("--nolinebacker", dest="nolinebacker", action="store_true", default=False, help="Don't use linebacker")
    group2.add_argument("--hostpercent", dest="hostpercent", help="% of hosts in parallel")
    group2.add_argument("--no_ice", dest="ice", action="store_true", default=False, help="Include ICE host in query")
    group2.add_argument("-v", "--verbose", action="store_true", default=False, help="Verbose Logging")
    options = parser.parse_args()

    ###############################################################################
    #                Constants
    ###############################################################################
    bundle = options.bundle
    dowork = options.dowork
    cwd = os.getcwd()
    if not os.path.isdir(cwd + "/output"):
        os.mkdir(cwd + "/output")
    #outputdir = "/root/git/cptops_case_gen/output/"
    consolidated_file = os.getcwd() + "/output/plan_implementation.txt"
    summary = "{}/output/summarylist.txt".format(os.getcwd())
    if os.path.isfile(summary):
        os.remove(summary)
    sum_file = open(summary, 'a')
    ###############################################################################

    if options.verbose:
        logging.basicConfig(level=logging.DEBUG)
        logging.debug("Bundle: {}".format(bundle))
        logging.debug("Dowork: {}".format(dowork))
        logging.debug("Current Working Directory {}".format(cwd))
        logging.debug("Ending file {}".format(consolidated_file))
        logging.debug("Summary File {}".format(summary))
        logging.debug("Linebacker Option: {}".format(options.nolinebacker))
    else:
        logging.basicConfig(level=logging.ERROR)

    if options.idbgen:
        inputdict = json.loads(options.idbgen)
        logging.debug(inputdict)
        role = inputdict['roles']
        dc = inputdict['datacenter']
        grouping = inputdict['grouping']
        templateid = inputdict['templateid']
        dr = inputdict['dr']

        # options parameters
        try:
            pod = inputdict['superpod']
        except KeyError:
            pod = "NA"

        try:
            hostfilter = inputdict['hostfilter']
        except KeyError:
            hostfilter = None

        try:
            cluster = inputdict['clusters']
        except KeyError:
            cluster = "NA"

        # Error checking for variables.
        if grouping != "byrack":
            try:
                gsize = inputdict['maxgroupsize']
            except KeyError:
                gsize = 1
        else:
            gsize = 0

        try:
            cl_status = inputdict['cl_opstat']
        except KeyError:
            cl_status = "ACTIVE"
        try:
            ho_status = inputdict['ho_stat']
        except KeyError:
            ho_status = "ACTIVE"
    else:
        sys.exit(1)

    CreateBlackswanJson(inputdict, options.bundle)
    cleanup()
    master_json = get_data(cluster, role, dc)
    grp = Groups(cl_status, ho_status, pod, role, dc, cluster, gsize, grouping, templateid, dowork)
    if grouping == "majorset":
        new_data = grp.majorset(master_json)
        logging.debug("By Majorset: {}".format(new_data))
        group_worker(templateid, new_data, gsize)
    elif grouping == "minorset":
        new_data = grp.minorset(master_json)
        logging.debug("By Minorset: {}".format(new_data))
        group_worker(templateid, new_data, gsize)
    elif grouping == "byrack":
        new_data = grp.rackorder(master_json)
        logging.debug("By Rack Data: {}".format(new_data))
        main_worker(templateid, new_data)
    else:
        sys.exit(1)