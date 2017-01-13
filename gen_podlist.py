import logging
import os
import re
import socket
import subprocess
from optparse import OptionParser

from idbhost import Idbhost


def where_am_i():
    """
    Figures out location based on hostname
    
    Input : nothing
    Returns : 3 letter site code
    """
    hostname = socket.gethostname()
    logging.debug(hostname)
    if not re.search(r'(sfdc.net|salesforce.com)', hostname):
        short_site = 'sfm'
    elif re.search(r'internal.salesforce.com', hostname):
        short_site = 'sfm'
    else:
        inst,hfuc,g,site = hostname.split('-')
        short_site = site.replace(".ops.sfdc.net", "")
    logging.debug(short_site)
    return short_site


def parseData(dc,spcl_grp):
    logging.debug(spcl_grp)
    pri_grps = []
    sec_grps = []
    for sp in spcl_grp:
        logging.debug(sp)
        if 'Primary' in spcl_grp[sp]:
            #print(spcl_grp[sp]['Primary'])
            pri_lsts = splitSP(spcl_grp[sp]['Primary'])
            for sp_lst in pri_lsts:
                if sp_lst != []:
                    #print(dc,sp_lst)
                    pri_grps.append(sp_lst)
        if 'Secondary' in spcl_grp[sp]:
            #print(spcl_grp[sp]['Secondary'])
            sec_lsts = splitSP(spcl_grp[sp]['Secondary'])
            for sp_lst in sec_lsts:
                if sp_lst != []:
                    #print(dc,sp_lst)
                    sec_grps.append(sp_lst)
    return pri_grps,sec_grps


def run_cmd(cmdlist):
    """
    Uses subprocess to run a command and return the output

    Input : A list containing a command and args to execute

    Returns : the output of the command execution
    """
    logging.debug(cmdlist)
    run_cmd = subprocess.Popen(cmdlist, stdout=subprocess.PIPE)
    out, err = run_cmd.communicate()
    return out


def get_inst_site(host):
    """
    Splits a host into a list splitting at - in the hostname
    The list contains inst,host function, group and 3 letter site code
    Input : hostname

    Returns : list containing inst,host function and 3 letter site code ignoring group.
    """
    inst,hfunc,g,site = host.split('-')
    short_site = site.replace(".ops.sfdc.net.", "")
    return inst,hfunc,short_site


def isInstancePri(inst,dc):
    """
    Confirms if an instance is primary or secondary based on site code
    DNS is used to confirm as the source of truth
    Input : an instance and a 3 letter site code

    Returns either PROD or DR
    """
    inst = inst.replace('-HBASE', '')
    monhost = inst + '-monitor.ops.sfdc.net'
    cmdlist = ['dig', monhost, '+short']
    output = run_cmd(cmdlist)
    logging.debug(output)
    for o in output.split('\n'):
        logging.debug(o)
        if re.search(r'monitor', o):
            inst,hfunc,short_site = get_inst_site(o)
            logging.debug("%s : %s " % (short_site,dc))
            if short_site != dc:
                return "DR"
            else:
                return "PROD"


def parseHbaseData(dc,spcl_grp):
    """
    Parses the list of hbase pods by super pod and
    converts them into a list of primary and secondary due to the fact
    that the normal primary secondary flags are not used correctly in iDB

    Input : 3 letter site code and pod data at sp level

    Returns : dict containing sp and pri,sec and cluster groups in that sp
    """
    logging.debug(spcl_grp)
    groups = {}
    for sp in spcl_grp:
        pri_grps = []
        sec_grps = []
        cluster_grps = []
        groups[sp] = {}
        logging.debug(sp)
        if 'Primary' in spcl_grp[sp]:
            logging.debug(spcl_grp[sp]['Primary'])
            for inst in spcl_grp[sp]['Primary'].split(","):
                if re.match(r"HBASE\d", inst, re.IGNORECASE):
                    cluster_grps.append(inst)
                    next
                elif re.match(r"GS", inst, re.IGNORECASE):
                    next
                # would be good to replace this with idbhost data
                loc = isInstancePri(inst,dc)
                logging.debug(loc)
                if loc == "PROD":
                    pri_grps.append(inst)
                elif loc == "DR":
                    sec_grps.append(inst)

        logging.debug('%s %s %s' % (pri_grps,sec_grps,cluster_grps))
        groups[sp]['pri_grps'] = pri_grps
        groups[sp]['sec_grps'] = sec_grps
        groups[sp]['cluster_grps'] = cluster_grps

        logging.debug("%s : %s" % (pri_grps,sec_grps))
    #return pri_grps,sec_grps,cluster_grps
    return groups


def parsegfdata(dc,spcl_grp):
        """
        Parses the list of gridforce pods by super pod and
        converts them into a list of primary and Secondary.

        Input : 3 letter site code and pod data at sp level

        Returns : list containing cluster names
        """
        logging.debug(spcl_grp)
        pri_grps = []
        sec_grps = []
        cluster_grps = []
        for sp in spcl_grp:
            logging.debug(sp)
            if 'Primary' in spcl_grp[sp]:
                logging.debug(spcl_grp[sp]['Primary'])
                for inst in spcl_grp[sp]['Primary'].split(","):
                    if re.match(r"GF", inst, re.IGNORECASE):
                        pri_grps.append(inst)
                    elif re.match(r"GS", inst, re.IGNORECASE):
                        pass
            logging.debug('%s %s %s' % (pri_grps, sec_grps, cluster_grps))
        return pri_grps



def parseHammerData(dc,spcl_grp):
    logging.debug(spcl_grp)
    pri_grps = []
    sec_grps = []
    for sp in spcl_grp:
        logging.debug(sp)
        if 'Primary' in spcl_grp[sp]:
            pri_lsts = spcl_grp[sp]['Primary']
            if pri_lsts != []:
                pri_grps.append(pri_lsts)
        if 'Secondary' in spcl_grp[sp]:
            sec_lsts = spcl_grp[sp]['Secondary']
            if sec_lsts != []:
                sec_grps.append(sec_lsts)
    return pri_grps,sec_grps


def parseNonPodData(spcl_grp):
    logging.debug(spcl_grp)
    pri_grps = []
    sec_grps = []
    for sp in spcl_grp:
        logging.debug(sp)
        if 'Primary' in spcl_grp[sp]:
            for i in spcl_grp[sp]['Primary'].split(','):
                if not i in pri_grps:
                    pri_grps.append(i)
        if 'Secondary' in spcl_grp[sp]:
            for i in spcl_grp[sp]['Secondary'].split(','):
                if not i in sec_grps:
                    sec_grps.append(i)
    return pri_grps,sec_grps


def sp_lst_gen(sp_lst):
    logging.debug(sp_lst)
    if len(sp_lst) > 90:
        tmp_lst = sp_lst.split(',')
        size = len(tmp_lst)
        w = ""
        for tmp in range(size):
            w += tmp_lst[tmp]
            if (tmp == size / 2 - 1) or (tmp == size - 1):
                output_pri.write(w + " " + dc + "\n")
                w = ""
            else:
                w += ","
    else:
        w = sp_lst + " " + dc + "\n"
        return w


def splitSP(lst):
    """
    Splits the instances into related groups for grouping later

    Returns a set of lists containing instances
    """
    ap_lst = []
    cs_lst = []
    na_lst = []
    eu_lst = []
    gs_lst = []
    sr_lst = []
    for pod in lst.split(','):
        if re.match('ap', pod, re.IGNORECASE):
            ap_lst.append(pod)
        if re.match('cs', pod, re.IGNORECASE):
            if not re.match('cs46', pod, re.IGNORECASE):
                cs_lst.append(pod)
        if re.match('na', pod, re.IGNORECASE):
            na_lst.append(pod)
        if re.match('eu', pod, re.IGNORECASE):
            eu_lst.append(pod)
        if re.match('gs', pod, re.IGNORECASE):
            gs_lst.append(pod)
        if re.match('sr', pod, re.IGNORECASE):
            sr_lst.append(pod)
    return ap_lst,cs_lst,na_lst,eu_lst


def splitHbaseSP(lst):
    ap_lst = []
    cs_lst = []
    na_lst = []
    eu_lst = []
    gs_lst = []
    sr_lst = []
    other_lst = []
    for pod in lst.split(','):
        if re.match('ap', pod, re.IGNORECASE):
            ap_lst.append(pod)
        if re.match('cs', pod, re.IGNORECASE):
            cs_lst.append(pod)
        if re.match('na', pod, re.IGNORECASE):
            na_lst.append(pod)
        if re.match('eu', pod, re.IGNORECASE):
            eu_lst.append(pod)
        if re.match('gs', pod, re.IGNORECASE):
            gs_lst.append(pod)
        if re.match('sr', pod, re.IGNORECASE):
            sr_lst.append(pod)
        else:
            if re.search(r'hbase', pod, re.IGNORECASE):
                other_lst.append(pod)

    return ap_lst,cs_lst,na_lst,eu_lst,other_lst


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in xrange(0, len(l), n):
        yield l[i:i+n]


def read_file(file_name):
    try:
        file_name = file_name
        if os.path.exists(file_name):
            logging.debug("File %s exists " % file_name)
            with open(file_name) as f:
                f_handle = f.readlines()
                return f_handle
    except IOError as e:
        print(e)


def listbuilder(pod_list, dc):
    hostnum = re.compile(r"(^monitor)([1-6])")
    if isinstance(pod_list, list):
        pods = pod_list
    else:
        pods = pod_list.split(',')
    for val in pods:
        if val != "None":
            output = os.popen("dig %s-monitor-%s.ops.sfdc.net +short | tail -2 | head -1" % (val.lower(), dc))
            prim_serv = output.read().strip("\n")
            host = prim_serv.split('.')
            mon_num = host[0].split('-')
            if prim_serv:
                if val.lower() == mon_num[0]:
                    output_pri.write(host[0] + "\n")
                match = hostnum.search(mon_num[1])
                num = int(match.group(2))
                if (num % 2) == 0:
                    output_sec.write(val.lower() + "-" + match.group(1) + str(num - 1) + "-" + mon_num[2] + "-" + dc + "\n")
                else:
                    output_sec.write(val.lower() + "-" + match.group(1) + str(num + 1) + "-" + mon_num[2] + "-" + dc + "\n")

if __name__ == '__main__':
    usage = """
    Code to get pods of cluster types from idb

    %prog [-d comma seperated list of dc's short code] [-t cluster type of pod hbase etc] [-v]
    %prog -d asg [-v]
    %prog -d asg,sjl,chi,was -t hbase
    %prog -d all_prod -t mta
    %prog -d all_non_prod -t DUST_DELPHI

    """
    parser = OptionParser(usage)
    parser.set_defaults(status='active', type='pod')
    parser.add_option("-d", "--dc", dest="dc",
                            help="The dc(s) to get data for ")
    parser.add_option("-s", "--status", dest="status",
                            help="The SP status eg hw_provisioning or provisioning or active ")
    parser.add_option("-g", "--groupsize", dest="groupsize", type="int", default=3,
                            help="Groupsize of pods or clusters for build file")
    parser.add_option("-t", "--type", dest="type",
                            help="The type of clusters eg pod, hbase, insights ")
    parser.add_option("-v", action="store_true", dest="verbose", help="verbosity")
    (options, args) = parser.parse_args()
    if options.verbose:
        logging.basicConfig(level=logging.DEBUG)
    groupsize = options.groupsize
    # Figure out where code is running
    site=where_am_i()
    #print(site)
    all_prod_dcs = ['asg', 'chi', 'was', 'tyo', 'lon', 'phx', 'dfw', 'frf', 'par']
    all_non_prod_dcs = ['sfm', 'crz', 'prd', 'crd', 'sfz']

    #Set the correct location for the Idbhost object
    if site == 'sfm':
        idb=Idbhost()
    else:
        idb=Idbhost(site)

    # Create a list from the supplied dcs
    if re.match(r'all_prod', options.dc, re.IGNORECASE):
        dcs = all_prod_dcs
    elif re.match(r'all_non_prod', options.dc, re.IGNORECASE):
        dcs = all_non_prod_dcs
    else:
        dcs = options.dc.split(",")
    if options.status:
        status = options.status
    if options.type:
        cluster_type = options.type.lower()

    # Create the filename variables
    fname_pri = cluster_type + ".pri"
    fname_sec = cluster_type + ".sec"
    fname_clusters = cluster_type + ".clusters"
    logging.debug("%s : %s : %s" % (fname_pri,fname_sec, fname_clusters))

    dc_data = {}
    # Get the clusters for a given type based on status in a dc
    for dc in dcs:
        print("Generating list for %s" % dc)
        if re.match(r'(afw)', cluster_type, re.IGNORECASE):
            cluster_type = 'pod'
        elif re.match(r'(gforce)', cluster_type, re.IGNORECASE):
            cluster_type = 'hbase'
        data = idb.sp_data(dc, status, cluster_type)
        logging.debug(data)
        pdata = idb.poddata(dc)
        logging.debug(pdata)
        dc_data[dc] = idb.spcl_grp
        logging.debug(idb.spcl_grp)

    if options.type == 'gforce':
        cluster_type = 'gforce'

    #Set the output filename and open them for writing
    output_pri = open("hostlists/" + fname_pri, 'w')
    output_sec = open("hostlists/" + fname_sec, 'w')
    out_clusters = open("hostlists/" + fname_clusters, 'w')

    # Parse the returned cluster data
    for dc in dc_data:
        logging.debug(dc_data)
        if re.match(r'(afw)', options.type, re.IGNORECASE):
            #print(dc_data[dc])
            for sp in dc_data[dc]:
                #print(dc_data[dc][sp])
                if 'Primary' in dc_data[dc][sp]:
                    if dc_data[dc][sp]['Primary'] != "None":
                        w = dc_data[dc][sp]['Primary'] + " " + dc + "-" + sp + "\n"
                        output_pri.write(w)
                if 'Secondary' in dc_data[dc][sp]:
                    if dc_data[dc][sp]['Secondary'] != "None":
                        w = dc_data[dc][sp]['Secondary'] + " " + dc + "-" + sp + "\n"
                        output_sec.write(w)

        elif re.match(r'(pod)', cluster_type, re.IGNORECASE):
            # Parses the groups of pods into groups of 3 and writes the output to files
            pri_grps,sec_grps = parseData(dc,dc_data[dc])
            for grp in pri_grps:
                chunked = list(chunks(grp, groupsize))
                #print(chunked)
                for sub_lst in chunked:
                    w = ','.join(sub_lst) + " " + dc + "\n"
                    output_pri.write(w)
            for grp in sec_grps:
                chunked = list(chunks(grp, groupsize))
                logging.debug(chunked)
                for sub_lst in chunked:
                    w = ','.join(sub_lst) + " " + dc + "\n"
                    output_sec.write(w)
            logging.debug("primary %s %s" % (dc,pri_grps))
            logging.debug("secondary %s %s" % (dc,sec_grps))
        elif re.match(r'(hammer)', cluster_type, re.IGNORECASE):
            """
            This code splits up hammer clusters into primary, secondary and sp cluster lists
            writing the output to files
            """
            pri_grps,sec_grps = parseHammerData(dc,dc_data[dc])
            logging.debug("%s %s" % (pri_grps,sec_grps))
            for sp_lst in pri_grps:
                logging.debug("pri : %s" % sp_lst)
                if sp_lst != "None":
                    sp_lst_gen(sp_lst)
                    w = sp_lst + " " + dc + "\n"
                    output_pri.write(w)
            for sp_lst in sec_grps:
                logging.debug("sec : %s" % sp_lst)
                if sp_lst != "None":
                    sp_lst_gen(sp_lst)
                    w = sp_lst + " " + dc + "\n"
                    output_sec.write(w)
        elif re.match(r'(hbase)', cluster_type, re.IGNORECASE):
            """
            This code splits up hbase clusters into primary, secondary and sp cluster lists
            writing the output to files
            """
            groups = parseHbaseData(dc,dc_data[dc])
            logging.debug(groups)
            for sp in groups:
                pri_grps = groups[sp]['pri_grps']
                sec_grps = groups[sp]['sec_grps']
                cluster_grps = groups[sp]['cluster_grps']
                logging.debug('%s %s %s' % (pri_grps,sec_grps,cluster_grps))
                #pri_sub_chunks=[pri_grps[x:x+groupsize] for x in xrange(0, len(pri_grps), groupsize)]
                #print(pri_sub_chunks)
                #for sub_lst in pri_sub_chunks:
                for sp_lst in pri_grps:
                    if sp_lst != "None":
                        sp_lst_gen(sp_lst)
                        w = sp_lst + " " + dc + "\n"
                        output_pri.write(w)
                     #w = sp_lst + " " + dc + "\n"
                     #output_pri.write(w)
                #sec_sub_chunks=[sec_grps[x:x+groupsize] for x in xrange(0, len(sec_grps), groupsize)]
                for sp_lst in sec_grps:
                    if sp_lst != "None":
                        sp_lst_gen(sp_lst)
                        w = sp_lst + " " + dc + "\n"
                        output_pri.write(w)
                    #w = sp_lst + " " + dc + "\n"
                    #output_sec.write(w)
                for c in cluster_grps:
                    w = c + " " + dc + "\n"
                    out_clusters.write(w)
                logging.debug("primary %s %s" % (dc,pri_grps))
                logging.debug("secondary %s %s" % (dc,sec_grps))
                logging.debug("clusters %s %s" % (dc,cluster_grps))

        elif re.match(r'(monitor)', cluster_type, re.IGNORECASE):
            """
            """
            for files in ['hostlists/pod.pri', 'hostlists/pod.sec']:
                f_data = read_file(files)
                for line in f_data:
                    if dc in line:
                        listbuilder(line.split()[0], dc)
            pod_list = ['ops', 'ops0', 'net', 'net0', 'sr1', 'sr2']
            listbuilder(pod_list, dc)

        elif re.match(r'gforce', cluster_type, re.IGNORECASE):
            """
            This code splits up gforce clusters into primary, secondary
            """
            pri_grps = parsegfdata(dc, dc_data[dc])
            logging.debug(pri_grps)
            for sp_lst in pri_grps:
                if sp_lst != "None":
                    sp_lst_gen(sp_lst)
                    print(sp_lst)
                    w = sp_lst + " " + dc + "\n"
                    output_pri.write(w)
                    # w = sp_lst + " " + dc + "\n"
                    # output_pri.write(w)

            logging.debug("primary %s %s" % (dc, pri_grps))


        else:
            """
            Parses any sp level instances and writes them to the output files
            Generally of the type cluster DC on successive lines. 
            Eg 
            MTA was
            MTA chi 
            """
            logging.debug(cluster_type)
            pri_grps,sec_grps = parseNonPodData(dc_data[dc])
            for grp in pri_grps:
                if grp != 'None':
                    w = grp + " " + dc + "\n"
                    output_pri.write(w)
            for grp in sec_grps:
                if grp != 'None':
                    w = grp + " " + dc + "\n"
                    output_sec.write(w)
            logging.debug("primary %s %s" % (dc,pri_grps))
            logging.debug("secondary %s %s" % (dc,sec_grps))
    # close writing the output files
    output_pri.close()
    output_sec.close()
    out_clusters.close()
