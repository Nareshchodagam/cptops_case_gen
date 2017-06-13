#!/usr/bin/env python
"""
This program is used to generate podlist file in a single shot. This script can be execute in multiple way like
pytnon update_podlist.py -u  [ It will update all the podlist files ]
python update_podlist.py -u -p <preset_name>
python update_podlist.py -u -d chi,was -p <preset_name>
"""
# imports
import logging
import json
import re
import os
import subprocess
from os import environ
import sys
from socket import gethostname
from argparse import ArgumentParser, RawTextHelpFormatter
from idbhost import Idbhost
import pprint

# Functions definition


def dcs(rolename, podtype, prod=True):
    prod_dc = ['chi', 'was', 'tyo', 'lon', 'ukb', 'phx', 'frf', 'dfw', 'par', 'iad', 'yul', 'yhu', 'ord', 'chx', 'wax']
    non_prod_dc = ['sfz', 'crd', 'sfm', 'prd', 'crz']
    if prod:
        if re.search(r'crz', rolename, re.IGNORECASE):
            prod_dc = 'crz'
        elif re.search(r'rps', rolename, re.IGNORECASE):
            prod_dc.extend(['sfz'])
        elif re.search(r'argus', rolename, re.IGNORECASE):
            prod_dc = 'prd'
        elif re.search(r'public', rolename, re.IGNORECASE):
            prod_dc.extend(['prd'])
        elif re.search(r'splunk', rolename, re.IGNORECASE):
            prod_dc.extend(['crz', 'sfz'])
        elif re.search(r'ajna', podtype, re.IGNORECASE):
            prod_dc.extend(['sfz', 'prd'])
        elif re.search(r'ops-stack', podtype, re.IGNORECASE):
            prod_dc.extend(['crd', 'sfz', 'prd'])
        elif re.search(r'lhub', rolename, re.IGNORECASE):
            prod_dc = 'sfz'
        elif re.search(r'cfgapp', rolename, re.IGNORECASE):
            prod_dc.extend(['crd'])
        elif re.search(r'cmgt', rolename, re.IGNORECASE):
            prod_dc = 'was'
        elif re.search(r'irc', rolename, re.IGNORECASE):
            prod_dc = (['sfm', 'crd'])
        return prod_dc
    else:
        return non_prod_dc


# Where am I
def where_am_i():
    """
    This function will extract the DC/site name form where you are executing your code.

    :param: This function doesn't require any parameter to pass.
    :return: This function will return the side/DC name e.g sfm/chi/was/tyo etc....
    """
    logger.info("Check the site_name, before connecting to iDB")
    hostname = gethostname()
    logger.debug(hostname)
    if not re.search(r'(sfdc.net|salesforce.com)', hostname):
        short_site = 'sfm'
    elif re.search(r'internal.salesforce.com', hostname):
        short_site = 'sfm'
    else:
        inst, hfuc, g, site = hostname.split('-')
        short_site = site.replace(".ops.sfdc.net", "")
    logger.info("Setup the site name to '{0}'" .format(short_site))
    return short_site


# idb class instantiate
def idb_connect(site):
    """
    Initiate connection to idb based on the site/DC name.

    :param site: The site name
    :type site: string
    :return: This function will return a class instance.
    :rtype:  Instance

    """
    logger.info("Connecting to iDB")
    try:
        if site == "sfm":
            idb = Idbhost()
        else:
            idb = Idbhost(site)
        logger.info("Successfully connect to iDB")
        return idb
    except Exception as e:
        logger.error(color.RED + "Unable to connect to idb, '{0}'" .format(e) + color.END)
        sys.exit(1)


def read_file(loc, filename, json_fmt=True):
    """
    The function is used to read file(Json OR Non-Json) and return the content of the file
    for next operations.
    :param loc: The location of the file '$USER/git/cptops_jenkins/scripts'
    :type loc: string
    :param filename: Name of the file   'case_presets.json'
    :type filename: string
    :param json_fmt: If True, it will read file as json object else plain file
    :type json_fmt: bool (True/False)
    :return: A dict which contains the content of given file 'filename'
    :rtype: dict
    """
    try:
        logger.info("Opening file {0}{1}".format(loc, filename))
        with open(loc + filename, 'r') as f_content:
            if json_fmt:
                try:
                    logger.info("Loading json file")
                    f_data = json.load(f_content)
                    logger.debug(pprint.pformat(f_data))
                except ValueError as e:
                    logger.error("Expected a json file, but doesn't looks like a json '{0}' " .format(e))
                    sys.exit(1)
                else:
                    logger.info("Successfully load the data from the {0} file" .format(filename))
                    retval = f_data
            else:
                logger.info("Reading file content")
                f_data = f_content.readlines()
                retval = f_data
    except IOError as e:
        logger.error("Can't open the file {0}{1} '{2}'".format(loc, filename, e))
        sys.exit(1)
    else:
        logger.debug("Successfully load the data from the file")
        return retval


def parse_json_data(data):
    """
    This function takes the input (case_preset.json file content) and choose the roles which are belongs to prod and doesn't
    have canary and type hostlist.
    This function will return a dict for all the presets in following format :-  {'preset_name' : ['podlist_file', 'cluster_type']}
    :param data: The output of case_preset.json file
    :type data: json
    :returns : returns a dict containing the preset_name, podlist file and POD/Cluster to query
    :rtype: dict
    :Example:
        {u'pbsmatch_prod': [u'pbsmatchcl', u'PBSMATCH']}
    """
    role_details = {}
    try:
        logger.info("Parsing json data for prod POD/Clusters")
        for roletype, roledata in data.items():

            if 'prod' in roletype and 'canary' not in roletype and 'standby' not in roletype:
                for role_file in roledata.values():
                    try:
                        role_details[roletype] = [role_file['PODGROUP'], role_file['CLUSTER_TYPE']]
                    except Exception as e:
                        logger.warn("update_podlist.py: Auto podlist not supported for preset '{0}' - '{1}' is missing"
                                      .format(roletype, e))
    except Exception as e:
        logger.error("Something went wrong with data parsing, '{0}'". format(e))
    else:
        logger.info("Successfully parsed the data")
        return role_details


def query_to_idb(dc, rolename, idb_object):
    """
    This function is used to query iDB with DC name and roles
    :param dc: DC's to query
    :param rolename: Rolename to query
    :param idb_object:
    :return: A dictionary contains superpod and pod information.
    :rtype: dict
    """
    logger.info("Extracting data from iDB")
    idb.sp_data(dc, 'active', rolename)
    logger.info("Successfully extracted data from iDB")
    if not idb.spcl_grp:
        logger.error("Data not returned from iDB for - '{0}' from dc '{1}'".format(rolename, dc))
    else:
        return idb.spcl_grp


def file_handles(file_name):
    """
    This function takes podlist file as an argument and build primary and secondary files to write pod information.
    :param file_name:
    :return: None
    """
    if re.search(r'acs|trust|afw|hammer|hbase.pri|pod|public-trust|monitor', file_name, re.IGNORECASE):
        file_handle_pri = open('hostlists/' + file_name, 'w')
        file_handle_sec = open('hostlists/' + file_name.split('.')[0] + '.sec', 'w')
        logger.info("Opened file handles on podlist file - '{0}, {1}.sec'".format(file_name, file_name.split('.')[0]))
        return file_handle_pri, file_handle_sec

    elif 'hbase.clusters' in file_name:
        file_handle_pri = open('hostlists/' + file_name, 'w')
        logger.info("Opened file handles on podlist file - '{0}'".format(file_name))
        return file_handle_pri, None

    elif 'la_clusters' in file_name:
        file_handle_pri = open('hostlists/' + file_name, 'w')
        file_handle_sec = open('hostlists/' + 'la_cs_clusters', 'w')
        logger.info("Opened file handles on podlist file - '{0}'".format(file_name))
        return file_handle_pri, file_handle_sec

    elif 'la_cs_clusters' in file_name:
        file_handle_pri = open('hostlists/' + file_name, 'w')
        file_handle_sec = open('hostlists/' + 'la_clusters', 'w')
        logger.info("Opened file handles on podlist file - '{0}'".format(file_name))
        return file_handle_pri, file_handle_sec

    else:
        file_handle_pri = open('hostlists/' + file_name, 'w')
        file_handle_sec = 'None'
        logger.info("Opened file handles on podlist file - '{0}'".format(file_name))
        return file_handle_pri, file_handle_sec


def run_cmd(cmdlist):
    """
    Uses subprocess to run a command and return the output
    :param cmdlist: A list containing a command and args to execute
    :return: the output of the command execution
    """
    logger.debug(cmdlist)
    run_cmd = subprocess.Popen(cmdlist, stdout=subprocess.PIPE)
    out, err = run_cmd.communicate()
    return out


def get_inst_site(host):
    """
    Splits a host into a list splitting at - in the hostname
    The list contains inst,host function, group and 3 letter site code
    :param host: hostname
    :return: list containing inst,host function and 3 letter site code ignoring group.
    :rtype: list
    """
    inst, hfunc, g, site = host.split('-')
    short_site = site.replace(".ops.sfdc.net.", "")
    return inst, hfunc, short_site


def isInstancePri(inst, dc):
    """
    Confirms if an instance is primary or secondary based on site code
    DNS is used to confirm as the source of truth
        :param: an instance and a 3 letter site code
        :return: either PROD or DR
        :rtype: str
    """
    inst = inst.replace('-HBASE', '')
    monhost = inst + '-monitor.ops.sfdc.net'
    cmdlist = ['dig', monhost, '+short']
    try:
        output = run_cmd(cmdlist)
    except IOError as e:
        logger.error("update_python.py: Please check if you have dig command installed")
    logger.debug(output)
    for o in output.split('\n'):
        logger.debug(o)
        if re.search(r'monitor', o):
            inst, hfunc, short_site = get_inst_site(o)
            logger.debug("%s : %s " % (short_site, dc))
            if short_site != dc:
                return "DR"
            else:
                return "PROD"


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i+n]


def listbuilder(pod_list, dc):  # This was added as part of - 'T-1810443'
    """
    This function is to generate hostlist files for monitor hosts.
    :param pod_list: podlist from pod.sec and pod.pri
    :type pod_list: str
    :param dc: datacenter name
    :return: A tuple containing two lists with primary and secondary monitor host.

    """
    hostnum = re.compile(r"(^monitor)([1-6])")
    hostcomp = re.compile(r'(\w*-\w*)(?<!\d)')
    hostlist_pri = []
    hostlist_sec = []
    if isinstance(pod_list, list):
        pods = pod_list
    else:
        pods = pod_list.split(',')
    for val in pods:
        if val != "None":
            output = os.popen("dig %s-monitor-%s.ops.sfdc.net +short | tail -2 | head -1" % (val.lower(), dc))
            prim_serv = output.read().strip("\n")
            host = prim_serv.split('.')
            logger.debug(host[0])
            mon_num = host[0].split('-')
            if prim_serv:
                hostval2 = hostcomp.search(prim_serv)
                if "%s-monitor" % (val.lower()) == hostval2.group():
                    if val.lower() == mon_num[0]:
                        if host[0] not in hostlist_pri:
                            hostlist_pri.append(host[0])
                    match = hostnum.search(mon_num[1])
                    num = int(match.group(2))
                    if (num % 2) == 0:
                        stby_host = val.lower() + "-" + match.group(1) + str(num - 1) + "-" + mon_num[2] + "-" + dc
                    else:
                        stby_host = val.lower() + "-" + match.group(1) + str(num + 1) + "-" + mon_num[2] + "-" + dc
                    if stby_host not in hostlist_sec:
                        hostlist_sec.append(stby_host)
                else:
                    val = prim_serv.split('-')[0]
                    if host[0] not in hostlist_pri:
                        hostlist_pri.append(host[0])
                    match = hostnum.search(mon_num[1])
                    num = int(match.group(2))
                    if (num % 2) == 0:
                        stby_host = val.lower() + "-" + match.group(1) + str(num - 1) + "-" + mon_num[2] + "-" + dc
                    else:
                        stby_host = val.lower() + "-" + match.group(1) + str(num + 1) + "-" + mon_num[2] + "-" + dc
                    if stby_host not in hostlist_sec:
                        hostlist_sec.append(stby_host)
        return hostlist_pri, hostlist_sec


def parse_cluster_pod_data(file_name, preset_name, idb_data, groupsize):
    """
    This function decides formatting of data to be writtenin  podlist file and it is responsible to restructure incoming data.
    This function regorub the data for the follwing roles
        1.afw
        2.hammer
        3.acs
        4.LiveAgent
        5.hbase
        6. Any other cluster type

    :param file_name: podlist file to write
    :type: str
    :param preset_name: Name of the preset to match in re.search
    :param idb_data: iDB connection
    :param groupsize: No. of pods to write in a single line
    :return: None
    """
    pri, sec = file_handles(file_name)
    for dc in idb_data.keys():
        if re.search(r'afw', file_name, re.IGNORECASE):
            for sp, pods in idb_data[dc].items():
                ttl_len = len(pods)
                p = []
                s = []
                for index in range(0, ttl_len):
                    if 'Primary' in pods[index]:
                        if pods[index]['Primary'] != "None":
                            p.append(pods[index]['Primary'])
                    if 'Secondary' in pods[index]:
                        if pods[index]['Secondary'] != "None":
                            s.append(pods[index]['Secondary'])
                chunked = chunks(p, groupsize)
                for sub_lst in chunked:
                    w = ','.join(sub_lst) + " " + dc.upper() + " " + sp.upper() + "\n"
                    pri.write(w)

                chunked = chunks(s, groupsize)
                for sub_lst in chunked:
                    w = ','.join(sub_lst) + " " + dc.upper() + " " + sp.upper() + "\n"
                    sec.write(w)
            logger.info("Successfully written data to podlist files - '{0}, {1}.sec' for dc '{2}'".format(file_name, file_name.split('.')[0], dc))

        elif re.search(r'hammer', file_name, re.IGNORECASE):
            for sp, pods in idb_data[dc].items():
                ttl_len = len(pods)
                p = []
                s = []
                for index in range(0, ttl_len):
                    if 'Primary' in pods[index]:
                        if pods[index]['Primary'] != "None":
                            p.append(pods[index]['Primary'])
                    if 'Secondary' in pods[index]:
                        if pods[index]['Secondary'] != "None":
                            s.append(pods[index]['Secondary'])
                if p:
                    write_list = []
                    len_list = len(p)
                    if len_list > 5:
                        for cluster in range(len_list):
                            if cluster % 5 == 0 and cluster != 0:
                                pri.write(",".join(write_list) + " " + dc + " " + sp.upper() + "\n")
                                write_list = []
                            write_list.append(p[cluster])
                    else:
                        w = ",".join(p) + " " + dc + " " + sp.upper() + "\n"
                        pri.write(w)
                if s:
                    write_list = []
                    len_list = len(s)
                    if len_list > 5:
                        for cluster in range(len_list):
                            if cluster % 5 == 0 and cluster != 0:
                                sec.write(",".join(write_list) + "\n")
                                write_list = []
                            write_list.append(s[cluster])
                    else:
                        w = ",".join(s) + " " + dc + " " + sp.upper() + "\n"
                        sec.write(w)
                logger.info("Successfully written data to podlist files - '{0}, {1}.sec' for dc '{2}'".format(file_name,
                                                                                                              file_name.split('.')[0], dc))

        elif 'pod' in file_name or 'acs' in file_name:
            logger.info("Writing data on podlist file - '{0}'".format(file_name))
            groupsize = 3
            for sp, pods in idb_data[dc].items():
                ttl_len = len(pods)
                p = []
                s = []
                for index in range(0, ttl_len):
                    if 'Primary' in pods[index]:
                        if pods[index]['Primary'] != "None":
                            p.append(pods[index]['Primary'])
                    if 'Secondary' in pods[index]:
                        if pods[index]['Secondary'] != "None":
                            s.append(pods[index]['Secondary'])

                chunked = chunks(p, groupsize)
                for sub_lst in chunked:
                    w = ','.join(sub_lst) + " " + dc.upper() + " " + sp.upper() + "\n"
                    pri.write(w)

                chunked = chunks(s, groupsize)
                for sub_lst in chunked:
                    w = ','.join(sub_lst) + " " + dc.upper() + " " + sp.upper() + "\n"
                    sec.write(w)
            logger.info("Successfully written data to -  '{0}, {1}.sec' for dc {2}".format(file_name, file_name.split('.')[0], dc))

        elif re.match(r'hbase_sp_prod', preset_name, re.IGNORECASE):
            logger.info("Writing data on podlist file - '{0}'".format(file_name))
            for sp, pods in idb_data[dc].items():
                ttl_len = len(pods)
                for index in range(0, ttl_len):
                    if pods[index]['Primary'] != "None" and re.match(r"HBASE\d", pods[index]['Primary'], re.IGNORECASE):
                        if pods[index]['Primary'] != "None":
                            w = pods[index]['Primary'] + " " + dc + " " + sp.upper() + "\n"
                            pri.write(w)
            logger.info("Successfully written data to - '{0}' for dc '{1}'".format(file_name, dc))

        elif re.search(r'(hbase_prod)', preset_name, re.IGNORECASE):
            """
            This code splits up hbase clusters into primary, secondary lists
            writing the output to files
            """
            logger.info("Writing data on podlist file -  '{0}', '{1}.sec' ".format(file_name, file_name.split('.')[0]))
            for sp, pods in idb_data[dc].items():
                p = []
                s = []
                ttl_len = len(pods)
                for index in range(0, ttl_len):
                    if pods[index]['Primary'] != "None" and 'HBASE' in pods[index]['Primary']:
                        loc = isInstancePri(pods[index]['Primary'], dc)
                        if loc == 'PROD':
                            p.append(pods[index]['Primary'])
                        elif loc == 'DR':
                            s.append(pods[index]['Primary'])

                chunked = chunks(p, groupsize)
                for sub_lst in chunked:
                    w = ','.join(sub_lst) + " " + dc.upper() + " " + sp.upper() + "\n"
                    pri.write(w)

                chunked = chunks(s, groupsize)
                for sub_lst in chunked:
                    w = ','.join(sub_lst) + " " + dc.upper() + " " + sp.upper() + "\n"
                    sec.write(w)
            logger.info("Successfully written data to -  '{0}, {1}.sec' for dc '{2}'".format(file_name, file_name.split('.')[0], dc))

        elif re.search(r'lapp', preset_name, re.IGNORECASE):
            """
            This code generate podlist files for lapp hosts [CS and PROD]. 
            """
            logger.info("Writing data on podlist file - '{0}'".format(file_name))
            for sp, pods in idb_data[dc].items():
                ttl_len = len(pods)
                for index in range(0, ttl_len):
                    if pods[index]['Primary'] != "None":
                        if 'cs' in file_name:
                            if 'CS' in pods[index]['Primary'] and 'GLA' not in pods[index]['Primary']:
                                w = pods[index]['Primary'] + " " + dc.upper() + " " + sp.upper() + "\n"
                                pri.write(w)
                            elif 'CS' not in pods[index]['Primary'] and 'GLA' not in pods[index]['Primary']:
                                w = pods[index]['Primary'] + " " + dc.upper() +  " " + sp.upper() + "\n"
                                sec.write(w)
                        else:
                            if 'CS' not in pods[index]['Primary'] and 'GLA' not in pods[index]['Primary']:
                                w = pods[index]['Primary'] + " " + dc.upper() + " " + sp.upper() + "\n"
                                pri.write(w)
                            elif 'GLA' not in pods[index]['Primary']:
                                w = pods[index]['Primary'] + " " + dc.upper() + " " + sp.upper() + "\n"
                                sec.write(w)

        elif re.match(r'(monitor)', preset_name, re.IGNORECASE):  # This was added as part of - 'T-1810443'
            """
            This code reads podlist from pod.pri and pod.sec file and generate the monitor hostlist.
            """
            p = []
            s = []

            for files in ['pod.pri', 'pod.sec']:
                f_data = read_file('hostlists/', files, json_fmt=False)
                for line in f_data:
                    if dc in line.lower():
                        hostlist_pri, hostlist_sec = listbuilder(line.split()[0], dc)
                        p.extend(hostlist_pri)
                        s.extend(hostlist_sec)
            pod_list = ['ops', 'ops0', 'net', 'net0', 'sr1', 'sr2']
            hostlist_pri, hostlist_sec = listbuilder(pod_list, dc)
            p.extend(hostlist_pri)
            s.extend(hostlist_sec)
            for item in p:
                pri.write("%s\n" % item)
            for item in s:
                sec.write("%s\n" % item)

        else:
            logger.info("Writing data on podlist file - '{0}'".format(file_name))
            for sp, pods in idb_data[dc].items():
                ttl_len = len(pods)
                for index in range(0, ttl_len):
                    if 'Primary' in pods[index]:
                        if 'irc' in file_name and 'MTA' in pods[index]['Primary']:
                            continue
                        elif 'argus' in file_name and 'ARGUS_DEV' in pods[index]['Primary']:
                            continue
                        elif 'piperepo' in file_name and 'OPS_PIPELINE' not in pods[index]['Primary']:
                            continue
                        w = pods[index]['Primary'] + " " + dc.upper() + " " + sp.upper() + "\n"
                        pri.write(w)

                    if 'Secondary' in pods[index]:
                        if 'HUB' not in pods[index]['Secondary']:
                            w = pods[index]['Secondary'] + " " + dc.upper() + " " + sp.upper() + "\n"
                            sec.write(w)
            logger.info("Successfully written data to podlist file -  '{0}' for dc '{1}'".format(file_name, dc))

if __name__ == "__main__":
    parser = ArgumentParser(description="""This code to update existing podlist files""",
                            usage=''
                                '%(prog)s -u -r <role>\n'
                                  '%(prog)s -u \n'
                                  '%(prog)s -u -p <role|roles> -d <dc|dcs> \n',formatter_class=RawTextHelpFormatter)
    parser.add_argument("-u", dest='update', action='store_true', required=True, help="To update all files in a single run")
    parser.add_argument("-p", dest='preset_name', help='To query the specfic role')
    parser.add_argument("-v", dest="verbose", help="For debugging purpose", action="store_true")
    parser.add_argument("-g", "--groupsize", dest="groupsize", default=3, help="Groupsize of pods or clusters for build file")
    parser.add_argument("-d", dest='datacenter', help="Datacenters to query")
    args = parser.parse_args()

    # Setting up custom logging
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if args.verbose == True else logging.INFO)

    # create a Stream handler
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG if args.verbose == True else logging.INFO)

    # create a logging format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # add the handlers to the logger
    logger.addHandler(handler)

    groupsize = args.groupsize  # NOTE This is specific to group the PODS
    groupsize = int(groupsize)
    if args.update:
        site = where_am_i()
        idb = idb_connect(site)
        file_content = read_file('/{0}/git/cptops_jenkins/scripts/'.format(environ['HOME']), 'case_presets.json')
        preset_data = parse_json_data(file_content)
        logger.debug(pprint.pformat(preset_data))

        if args.preset_name:  # This loop will be called when user is trying to extract information for a specific role
            cstm_preset_data = {}
            if 'monitor' in args.preset_name:
                args.preset_name = 'search_prod,' + args.preset_name
            for preset in args.preset_name.split(','):
                try:
                    cstm_preset_data[preset] = preset_data[preset]
                except KeyError as e:
                    logger.error("Could not recognise preset name - {0}" .format(e))
                    sys.exit(1)
            preset_data = cstm_preset_data
        role_details = []
        total_idb_data = {}
        for k, v in preset_data.items():
            if v[1]:
                logger.info("\n************************* Starting on role '{0}'*************************".format(k))
                if v[1] not in role_details or re.search(r'afw|acs|hbase|lhub|log_hub', v[0], re.IGNORECASE):
                    role_details.append(v[1])
                    total_idb_data['monitor'] = {dc:'' for dc in dcs(k, v[1])}
                    if v[1] not in total_idb_data.keys():
                        if args.datacenter:
                            dcs = args.datacenter.split(',')
                            idb_ret = query_to_idb(dcs, v[1],  idb)
                        else:
                            idb_ret = query_to_idb(dcs(k, v[1]), v[1], idb)
                        total_idb_data[v[1]] = idb_ret
                        if not idb_ret:
                            break
                    else:
                        logger.info("Skipping iDB query, using data from cache")

                    parse_cluster_pod_data(v[0], k, total_idb_data[v[1]], groupsize)
                    logger.info("\n************************* Done with Role '{0}' *************************\n".format(k))
                else:
                    logger.info("skipping... The podlist file {0} for role {1}  has been processed" .format(v[0], k))
                    logger.info("\n************************* Done with Role '{0}' *************************\n".format(k))
            else:
                continue
