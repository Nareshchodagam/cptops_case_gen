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

# Global assignments
pp = pprint.PrettyPrinter(indent=2)
global new_data
active_hosts = []


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

    return [tryint(c) for c in re.split('([0-9]+)', s)]


def url_response(url):
    response = requests.get(url, verify=False)
    if response.json() is None:
        logging.error("No Data Present")
        sys.exit(1)
    return response.json()


def get_data(cluster, role, dc):
    '''
    Function queries blackswan for data. It then strips the necessary information and recreates it
    into the master_json dictionary.
    :return:
    '''
    master_json = {}
    ice_chk = re.compile(r'ice|mist')

    if cluster != "NA":
        url = "https://ops0-cpt1-1-xrd.eng.sfdc.net:9876/api/v1/hosts?cluster={}&role={}&dc={}".format(cluster, role, dc)
    else:
        url = "https://ops0-cpt1-1-xrd.eng.sfdc.net:9876/api/v1/hosts?role={}&dc={}".format(role, dc)

    data = url_response(url)

    for host in data:
        logging.debug("{}: patchCurrentRelease:{} clusterStatus:{} hostStatus:{} hostFailover:{}".format(host['hostName'],
                                                                                                         host['patchCurrentRelease'],
                                                                                                         host['clusterStatus'],
                                                                                                         host['hostStatus'],
                                                                                                         host['hostFailover']))
        json_data = {'RackNumber': host['hostRackNumber'], 'Role': host['roleName'],
                     'Bundle': host['patchCurrentRelease'], 'Majorset': host['hostMajorSet'],
                     'Minorset': host['hostMinorSet'], 'OS_Version': host['patchOs']}
        host_json = json.dumps(json_data)
        if host['hostStatus'] == "ACTIVE":
            active_hosts.append(host['hostName'])
        if host['hostFailover'] == failoverstatus or failoverstatus == None:
            if host['clusterStatus'] == cl_status:
                if host['hostStatus'] == "ACTIVE":   
                    if host['superpodName'] in pod_dict.keys():
                        # if host['patchCurrentRelease'] != options.bundle:
                        # if not host['hostCaptain']:
                        if options.skip_bundle:
                            if host['patchCurrentRelease'] < options.skip_bundle or "migration" in templateid .lower():
                                master_json[host['hostName']] = json.loads(host_json)
                            else:
                                logging.debug("{}: patchCurrentRelease is {}, skipped".format(host['hostName'], host['patchCurrentRelease']))
                        else:
                            master_json[host['hostName']] = json.loads(host_json)
                        # else:
                        #        logging.debug("{}: hostCaptain is {}, excluded".format(host['hostName'],host['hostCaptain']))
                        # else:
                            # logging.debug("{}: patchCurrentRelease is {}, excluded".format(host['hostName'],\
                         #             host['patchCurrentRelease']))
                    else:
                        logging.debug("{}: Superpod is {}, excluded".format(host['hostName'], host['superpodName']))
                else:
                    logging.debug("{}: hostStatus is {}, excluded".format(host['hostName'], host['hostStatus']))
            else:
                logging.debug("{}: clusterStatus is {}, excluded".format(host['hostName'], host['clusterStatus']))
        else:
            logging.debug("{}: failoverStatus is {}, excluded".format(host['hostName'], host['hostFailover']))

    logging.debug("Master Json {}".format(master_json))

    if not master_json:
        logging.error("The hostlist is empty!")
        sys.exit(1)
    else:
        #master_json = ice_chk(master_json)
        master_json = bundle_cleanup(master_json, options.bundle)
        master_json = hostfilter_chk(master_json)

    if options.os_version:
        master_json = os_chk(master_json)

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


def find_concurrency(hostpercent):
    """
    This function calculates the host count per block #W-3758985
    :param inputdict: takes inputdict
    :return: maxgroupsize
    """
    pod = inputdict['clusters']
    dc = inputdict['datacenter']
    role = inputdict['roles']
    master_json = get_data(pod, role, dc)
    inputdict['maxgroupsize'] = round(float(hostpercent) * (len(master_json)) / 100)


def os_chk(data):
    for host in data.keys():
        if options.os_version != data[host]['OS_Version']:
            logging.debug("{}: OS_Version is {}, excluded".format(host,
                                                                  data[host]['OS_Version']))
            del data[host]
    return data


def bundle_cleanup(data, targetbundle):
    '''
    This function checks excludes the hosts that are already patched
    :param data:
    :return:
    '''
    current_bundle = {}
    url = "https://ops0-cpt1-1-xrd.eng.sfdc.net:9876/api/v1/patch-bundles"
    bundles = url_response(url)
    if targetbundle.lower() == "current":
        for bundle in bundles:
            if bundle['current'] == True:
                current_bundle[str(int(float(bundle['osMajor'])))] = bundle['release']
        c7_ver = current_bundle['7']
        c6_ver = current_bundle['6']
    elif targetbundle.lower() == "canary":
        # get canary bundle info and assign to
        # c7_ver and c6_ver respectively
        for bundle in bundles:
            if bundle['canary'] == True:
                current_bundle[str(int(float(bundle['osMajor'])))] = bundle['release']
        c7_ver = current_bundle['7']
        c6_ver = current_bundle['6']
    else:
        # if any other specific bundle values are passed
        c7_ver = c6_ver = targetbundle
    if "migration" not in templateid.lower() :
        if targetbundle.lower() in ["current", "canary"]:
            for host in data.keys():
                if data[host]['OS_Version'] == "7" and data[host]['Bundle'] == c7_ver:
                    logging.debug("{}: patchCurrentRelease is {}, excluded".format(host, data[host]['Bundle']))
                    del data[host]
                elif data[host]['OS_Version'] == "6" and data[host]['Bundle'] == c6_ver:
                    logging.debug("{}: patchCurrentRelease is {}, excluded".format(host, data[host]['Bundle']))
                    del data[host]
        else:
            for host in data.keys():
                if data[host]['OS_Version'] == "7" and data[host]['Bundle'] >= c7_ver:
                    logging.debug("{}: patchCurrentRelease is {}, excluded".format(host, data[host]['Bundle']))
                    del data[host]
                elif data[host]['OS_Version'] == "6" and data[host]['Bundle'] >= c6_ver:
                    logging.debug("{}: patchCurrentRelease is {}, excluded".format(host, data[host]['Bundle']))
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
    # check if templates exist
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
            #if not options.nolinebacker:
            #    regex_compile = re.compile('bigipcheck|remove_from_pool|add_to_pool', re.IGNORECASE)
            #    if regex_compile.search(o_list[i]):
            #        o_list[i] = o_list[i].strip() + ' -nolinebacker' + "\n"
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


def compile_template(hosts, template, work_template, file_num):
    '''
    This function put the template together substitute variables with information it obtains from
    command line and Atlas/Blackswan.
    :return:
    '''
    outfile = os.getcwd() + "/output/{}_plan_implementation.txt".format(file_num)
    output = prep_template(work_template, template)

    if 'v_COMMAND' not in output and 'mkdir ' not in output:
        output = output.replace('v_HOSTS', '$(cat ~/v_CASE_include)')
        output_list = output.splitlines(True)
        if role not in ("secrets", "smszk") and "migration" not in template.lower():
            output_list.insert(1, '\n- Verify if hosts are patched or not up\nExec: echo "Verify hosts BLOCK v_NUM" && '
                                  '/opt/cpt/bin/verify_hosts.py -H v_HOSTS --bundle v_BUNDLE --case v_CASE\n\n')
        elif "migration" in template.lower():
            output_list.insert(1, '\n- Verify if hosts are patched or not up\nExec: echo "Verify hosts BLOCK v_NUM" && '
                                  '/opt/cpt/bin/verify_hosts.py -H v_HOSTS --bundle v_BUNDLE --case v_CASE -M\n\n')
        output = "".join(output_list)
    output = compile_vMNDS_(output)
    output = output.replace('v_CLUSTER', new_data['Details']['cluster'])
    output = output.replace('v_DATACENTER', new_data['Details']['dc'])
    output = output.replace('v_SUPERPOD', new_data['Details']['Superpod'])
    output = output.replace('v_ROLE', new_data['Details']['role'])
    output = output.replace('v_HO_OPSTAT', new_data['Details']['ho_status'])
    output = output.replace('v_CL_OPSTAT', new_data['Details']['cl_status'])
    output = output.replace('v_BUNDLE', options.bundle)
    output = output.replace('v_HOSTS', ','.join(hosts))
    if "migration" in template.lower():
        if len(active_hosts) != 0:
            output = output.replace('v_HOST', active_hosts[0])
        else:
            logging.error("No active host present in the cluster to fetch APP version")
    else:
        output = output.replace('v_HOST', hosts[0])
    output = output.replace('v_NUM', str(file_num))
    # other host and v_OHOSTS are used to create a check against all but the host to be patched (i.e. lapp, rps)
    other_hosts = list(set(allhosts) - set(hosts))
    output = output.replace('v_OHOSTS', ','.join(other_hosts))
    output = output.replace('v_ALLHOSTS', ','.join(allhosts))
    if 'v_PRODUCT_RRCMD' in output:
        products ,ignore_processes = product_rrcmd(role)
        output = output.replace('v_PRODUCT_RRCMD', ','.join(products))
        #add ignore processes here if required





    f = open(outfile, 'w')
    f.write(output)
    f.close()
    for t in hosts:
        sum_file.write(t + "\n")


def compile_pre_template(template):
    '''
    This function configures the pre template.
    :param new_data:
    :param template:
    :return:
    '''
    with open(template, 'r') as out:
        output = out.read()
    output = output.replace('v_CLUSTER', new_data['Details']['cluster'])
    output = output.replace('v_DATACENTER', new_data['Details']['dc'])
    output = output.replace('v_SUPERPOD', new_data['Details']['Superpod'])
    output = output.replace('v_ROLE', new_data['Details']['role'])
    output = output.replace('v_HO_OPSTAT', new_data['Details']['ho_status'])
    output = output.replace('v_CL_OPSTAT', new_data['Details']['cl_status'])
    output = output.replace('v_BUNDLE', options.bundle)
    output = output.replace('v_HOSTS', ','.join(allhosts))

    return output


def compile_post_template(template):
    '''
    This function configures the post template.
    :param new_data:
    :param template:
    :return:
    '''
    build_command = " ".join(sys.argv)
    build_command = build_command.replace("{", "'{")
    build_command = build_command.replace("}", "}'")

    with open(template, 'r') as out:
        output = out.read()
    output = output.replace('v_CLUSTER', new_data['Details']['cluster'])
    output = output.replace('v_DATACENTER', new_data['Details']['dc'])
    output = output.replace('v_SUPERPOD', new_data['Details']['Superpod'])
    output = output.replace('v_ROLE', new_data['Details']['role'])
    output = output.replace('v_HO_OPSTAT', new_data['Details']['ho_status'])
    output = output.replace('v_CL_OPSTAT', new_data['Details']['cl_status'])
    output = output.replace('v_BUNDLE', options.bundle)
    output = output.replace('v_COMMAND', build_command)

    return output


def compile_vMNDS_(output):
    """
    :param template: template
    :return: output
    """

    # Load Hbase hbase-mnds template.
    hbaseDowork_ = "{}/templates/{}.template".format(os.getcwd(), "hbase-mnds")

    # Check for hbase-mnds template existence.
    if os.path.isfile(hbaseDowork_):
        with open(hbaseDowork_, 'r') as f:
            mndsData = f.readlines()

    # Load the template data into variable.
    v_MNDS = "".join(mndsData)

    # Replace the v_MNDS variable in Hbase Mnds template.
    try:
        if re.search(r"mnds", new_data['Details']['role'], re.IGNORECASE):
            logging.debug(v_MNDS)
            output = output.replace('v_MNDS', v_MNDS)
        else:
            output = output.replace('v_MNDS', "- SKIPPING MNDS CHECK.")
    except:
        pass

    # Return the plan_implimentation with changed v_MNDS.
    return output


def create_masterplan(consolidated_file, pre_template, post_template):
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
        pre = compile_pre_template(pre_template)
        final_file.write('BEGIN_GROUP: PRE\n' + pre + '\nEND_GROUP: PRE\n\n')

    for f in read_files:
        if f != consolidated_file:
            with open(f, "r") as infile:
                # print('Writing out: ' + f + ' to ' + consolidated_file)
                final_file.write(infile.read() + '\n\n')

    post_file = compile_post_template(post_template)
    post_list = post_file.splitlines(True)
    case_post = "- Auto close case \nExec_with_creds: /opt/cpt/gus_case_mngr.py -c v_CASE --close -y\n\n"
    post_list.insert(-5, case_post)
    post = "".join(post_list)
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


def product_rrcmd(role_name) :
    '''
    This function is used mainly in Reimage/Migration to capture the deployed products on a particular role.

    :return:
    '''


    products = {
        'chatterbox': ['sshare', 'prsn'],
        'chatternow': ['chan', 'dstore', 'msg', 'prsn'],
        'mandm-hub': ['mgmt_hub'],
        'caas': ['app'],
        'lightcycle-snapshot': ['app'],
        'mandm-agent': ['app'],
        'mq-broker': ['mq'],
        'acs': ['acs'],
        'searchserver': ['search'],
        'sfdc-base': ['ffx', 'cbatch', 'app', 'dapp'],
        'insights-redis': ['insights_redis', 'insights_iworker'],
        'insights-edgeservices': ['insights_redis', 'insights_iworker'],
        'waveagent': ['insights_redis', 'insights_iworker'],
        'wave-connector-agent': ['insights_redis', 'insights_iworker'],
        'wave-cassandra': ['insights_redis', 'insights_iworker']
    }
    ignored_process_names ={'redis-server': ['sfdc-base'],'memcached': ['sfdc-base']}
    product_rrcmd=[]
    ignore_process=[]
    for key in products.keys():
        if role_name in products[key]:
            product_rrcmd.append(key)
            for pkey in ignored_process_names :
                if key in ignored_process_names[pkey]:
                    ignore_process.append(pkey)
    return (product_rrcmd,ignore_process)





def group_worker(templateid, gsize):
    '''
    "This function is responsible for doing the work associated with the gsize variable.
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
                compile_template(host_group, template, work_template, file_num)
                host_group = []
                file_num = file_num + 1
            elif host == new_data['Hostnames'][key][-1]:
#### The following section is to manage dynamic grouping while writing plan[W-6755335]. Currently being hardcoded to 10%
                if 'ajna_broker' in role:
                    group_div = int(10 * len(host_group) / 100)
                    if group_div == 0: 
                        group_div = 1
                    ho_lst = [host_group[j: j + group_div] for j in range(0, len(host_group), group_div)]
                    for ajna_hosts in ho_lst:
                        logging.debug(ajna_hosts)
                        logging.debug("File_Num: {}".format(file_num))
                        compile_template(ajna_hosts, template, work_template, file_num)
                        host_group = []
                        file_num = file_num + 1 
                else:               
                    logging.debug(host_group)
                    logging.debug("File_Num: {}".format(file_num))
                    compile_template(host_group, template, work_template, file_num)
                    file_num = file_num + 1
                    host_group = []
    sum_file.close()
    create_masterplan(consolidated_file, pre_template, post_template)


def main_worker(templateid, gsize):
    '''
    This function works with the byrack data. It just prints the contents of the
    value from the new_data dictionary to populate the v_HOSTS variable. Probably needs
    to be renamed.
    :param templateid:
    :param new_data:
    :param file_num:
    :return:
    '''
    file_num = 1
    total_groups = 0
    host_count = 0
    byrack_group = []

    template, work_template, pre_template, post_template = validate_templates(templateid)
    for pri in new_data['Grouping'].iterkeys():
        for key, value in new_data['Grouping'][pri].iteritems():
            if gsize == 0:
                compile_template(value, template, work_template, file_num)
                file_num = file_num + 1
                logging.debug("{} {}".format(key, value))
                total_groups = total_groups + 1
                host_count = host_count + len(value)
            else:
                for host in value:
                    byrack_group.append(host)
                    if len(byrack_group) == gsize:
                        compile_template(byrack_group, template, work_template, file_num)
                        file_num = file_num + 1
                        logging.debug(byrack_group)
                        total_groups = total_groups + 1
                        host_count = host_count + len(byrack_group)
                        byrack_group = []
                    elif host == value[-1]:
                        compile_template(byrack_group, template, work_template, file_num)
                        file_num = file_num + 1
                        logging.debug(byrack_group)
                        total_groups = total_groups + 1
                        host_count = host_count + len(byrack_group)
                        byrack_group = []

    logging.debug("Total # of groups: {}".format(total_groups))
    logging.debug("Total # of servers to be patched: {}".format(host_count))
    sum_file.close()
    create_masterplan(consolidated_file, pre_template, post_template)


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
    group1.add_argument("-o", "--os", dest="os_version", help="Filter servers by OS Version")
    group2.add_argument("--taggroups", dest="taggroups", default=0, help="number of sub-plans per group tag")
    group2.add_argument("--nolinebacker", dest="nolinebacker", action="store_true", default=False, help="Don't use linebacker")
    group2.add_argument("--hostpercent", dest="hostpercent", help="percentange of hosts in parallel")
    group2.add_argument("--no_ice", dest="ice", action="store_true", default=False, help="Include ICE host in query")
    group2.add_argument("--skip_bundle", dest="skip_bundle", help="command to skip bundle")
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
    consolidated_file = cwd + "/output/plan_implementation.txt"
    summary = cwd + "/output/summarylist.txt"
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
            failoverstatus = inputdict['regexfilter']
            failoverstatus = failoverstatus.split("=")[1]
        except KeyError:
            failoverstatus = None

        try:
            cluster = inputdict['clusters']
        except KeyError:
            cluster = "NA"

        # Error checking for variables.
        try:
            cl_status = inputdict['cl_opstat']
        except KeyError:
            cl_status = "ACTIVE"
        try:
            ho_status = inputdict['ho_opstat']
        except KeyError:
            ho_status = "ACTIVE"
    else:
        sys.exit(1)

    # If POD,CLuster info is not passed to this script, Below logic retrieves the info from Blackswan/Atlas
    single_cluster = False
    if pod == "NA" and cluster == "NA":
        cluster = []
        pod_dict = {}
        url = "https://ops0-cpt1-1-xrd.eng.sfdc.net:9876/api/v1/hosts?role={}&dc={}".format(role, dc)
        data = url_response(url)
        for host in data:
            pod = host['superpodName']
            cluster = host['clusterName']
            if pod not in pod_dict:
                pod_dict[pod] = []
            if cluster not in pod_dict[pod]:
                pod_dict[pod].append(cluster)

    elif pod != "NA" and cluster == "NA":
        url = "https://ops0-cpt1-1-xrd.eng.sfdc.net:9876/api/v1/hosts?role={}&dc={}&sp={}".format(role, dc, pod)
        data = url_response(url)
        pod_dict = {pod: []}
        for host in data:
            cluster = host['clusterName']
            if cluster not in pod_dict[pod]:
                pod_dict[pod].append(cluster)

    elif pod == "NA" and cluster != "NA":
        url = "https://ops0-cpt1-1-xrd.eng.sfdc.net:9876/api/v1/hosts?role={}&dc={}&cluster={}".format(role, dc, cluster)
        data = url_response(url)
        single_cluster = True
        pod = data[0]['superpodName']
        pod_dict = {pod: cluster}

    else:
        pod_dict = {pod: cluster}
        single_cluster = True

    for pod, clusters in pod_dict.items():
        inputdict['superpod'] = pod
        total_cluster_list = []
        if not single_cluster:
            clusters = ",".join(clusters)
            total_cluster_list.append(clusters)
        inputdict['clusters'] = clusters
        CreateBlackswanJson(inputdict, options.bundle)
    if total_cluster_list:
        cluster = ",".join(total_cluster_list)

    cleanup()
    if options.hostpercent:
        find_concurrency(options.hostpercent)
    try:
        gsize = inputdict['maxgroupsize']
    except KeyError:
        if grouping == "byrack":
            gsize = 0
        else:
            gsize = 1
    master_json = get_data(cluster, role, dc)
    grp = Groups(cl_status, ho_status, pod, role, dc, cluster, gsize, grouping, templateid, dowork)
    if grouping == "majorset":
        new_data, allhosts = grp.majorset(master_json)
        logging.debug("By Majorset: {}".format(new_data))
        group_worker(templateid, gsize)
    elif grouping == "minorset":
        new_data, allhosts = grp.minorset(master_json)
        logging.debug("By Minorset: {}".format(new_data))
        group_worker(templateid, gsize)
    elif grouping == "byrack":
        new_data, allhosts = grp.rackorder(master_json)
        logging.debug("By Rack Data: {}".format(new_data))
        main_worker(templateid, gsize)
    elif grouping == "all":
        new_data, allhosts = grp.all(master_json)
        logging.debug("By All: {}".format(new_data))
        group_worker(templateid, gsize)
    else:
        sys.exit(1)
