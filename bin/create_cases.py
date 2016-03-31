import common
from idbhost import Idbhost
from optparse import OptionParser
import socket
import logging
import re

def where_am_i():
    hostname = socket.gethostname()
    logging.debug(hostname)
    if re.search(r'internal.salesforce.com', hostname):
        short_site = 'sfm'
    else:
        inst,hfuc,g,site = hostname.split('-')
        short_site = site.replace(".ops.sfdc.net", "")
    logging.debug(short_site)
    return short_site

def parseData(dc,spcl_grp):
    #print(spcl_grp)
    pri_grps = []
    sec_grps = []
    for sp in spcl_grp:
        #print(sp)
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

def splitSP(lst):
    ap_lst = []
    cs_lst = []
    na_lst = []
    eu_lst = []
    gs_lst = []
    sr_lst = []
    for pod in lst.split(','):
        if re.search('ap', pod, re.IGNORECASE):
            ap_lst.append(pod)
        if re.search('cs', pod, re.IGNORECASE):
            cs_lst.append(pod)
        if re.search('na', pod, re.IGNORECASE):
            na_lst.append(pod)
        if re.search('eu', pod, re.IGNORECASE):
            eu_lst.append(pod)
        if re.search('gs', pod, re.IGNORECASE):
            gs_lst.append(pod)
        if re.search('sr', pod, re.IGNORECASE):
            sr_lst.append(pod)
    return ap_lst,cs_lst,na_lst,eu_lst,gs_lst,sr_lst

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in xrange(0, len(l), n):
        yield l[i:i+n]
        
if __name__ == '__main__':
    usage = """
    Code to get pods of cluster types from idb

    %prog [-d comma seperated list of dc's short code] [-t cluster type of pod hbase etc] [-v]
    %prog -d asg [-v]   
    %prog -d asg,sjl,chi,was -t hbase

    """
    parser = OptionParser(usage)
    parser.add_option("-d", "--dc", dest="dc",
                            help="The dc(s) to get data for ")
    parser.add_option("-s", "--status", dest="status",
                            help="The SP status eg hw_provisioning or provisioning or active ")
    parser.add_option("-t", "--type", dest="type",
                            help="The type of clusters eg pod, hbase, insights ")
    parser.add_option("-v", action="store_true", dest="verbose", default=False, help="verbosity") # will set to False later
    (options, args) = parser.parse_args()
    if options.verbose:
        logging.basicConfig(level=logging.DEBUG)
    site=where_am_i()
    print(site)
    
    if site == 'sfm':
        idb=Idbhost()
    else:
        idb=Idbhost(site)
    dcs = options.dc.split(",")
    if options.status:
        status = options.status
    else:
        status = 'active'
    if options.type:
        cluster_type = options.type
    else:
        cluster_type = 'pod'
    
    fname_pri = cluster_type + ".pri"
    fname_sec = cluster_type + ".sec"
    dc_data ={}
    for dc in dcs:
        print(dc)
        data = idb.sp_data(dc, status, cluster_type)
        pdata = idb.poddata(dc)
        dc_data[dc] = idb.spcl_grp
        
    output_pri = open(fname_pri, 'w')
    output_sec = open(fname_sec, 'w')
    for dc in dc_data:
        pri_grps,sec_grps = parseData(dc,dc_data[dc])
        for grp in pri_grps:
            chunked = list(chunks(grp, 3))
            print(chunked)
            for sub_lst in chunked:
                w = ','.join(sub_lst) + " " + dc + "\n"
                output_pri.write(w)
        for grp in sec_grps:
            chunked = list(chunks(grp, 3))
            logging.debug(chunked)
            for sub_lst in chunked:
                w = ','.join(sub_lst) + " " + dc + "\n"
                output_sec.write(w)
        logging.debug("primary %s %s" % (dc,pri_grps))
        logging.debug("secondary %s %s" % (dc,sec_grps))
    output_pri.close()
    output_sec.close()