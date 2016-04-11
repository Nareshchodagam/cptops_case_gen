import common
from idbhost import Idbhost
from optparse import OptionParser
import socket
import logging
import re
import subprocess

def where_am_i():
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
    logging.debug(cmdlist)
    run_cmd = subprocess.Popen(cmdlist, stdout=subprocess.PIPE)
    out, err = run_cmd.communicate()
    return out

def get_inst_site(host):
    inst,hfunc,g,site = host.split('-')
    short_site = site.replace(".ops.sfdc.net.", "")
    return inst,hfunc,short_site

def isInstancePri(inst,dc):
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
    logging.debug(spcl_grp)
    pri_grps = []
    sec_grps = []
    cluster_grps = []
    for sp in spcl_grp:
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
    logging.debug("%s : %s" % (pri_grps,sec_grps))
    return pri_grps,sec_grps,cluster_grps

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

def splitSP(lst):
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


        
if __name__ == '__main__':
    usage = """
    Code to get pods of cluster types from idb

    %prog [-d comma seperated list of dc's short code] [-t cluster type of pod hbase etc] [-v]
    %prog -d asg [-v]   
    %prog -d asg,sjl,chi,was -t hbase

    """
    parser = OptionParser(usage)
    parser.set_defaults(status='active', type='pod')
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
    #status = 'active'
    #cluster_type = 'pod'
    
    if site == 'sfm':
        idb=Idbhost()
    else:
        idb=Idbhost(site)
    dcs = options.dc.split(",")
    if options.status:
        status = options.status
    if options.type:
        cluster_type = options.type.lower()
    
    fname_pri = cluster_type + ".pri"
    fname_sec = cluster_type + ".sec"
    fname_clusters = cluster_type + ".clusters"
    logging.debug("%s : %s" % (fname_pri,fname_sec))
    
    dc_data ={}
    for dc in dcs:
        print(dc)
        data = idb.sp_data(dc, status, cluster_type)
        logging.debug(data)
        pdata = idb.poddata(dc)
        logging.debug(pdata)
        dc_data[dc] = idb.spcl_grp
        logging.debug(idb.spcl_grp)
        
    output_pri = open(fname_pri, 'w')
    output_sec = open(fname_sec, 'w')
    out_clusters = open(fname_clusters, 'w')
    for dc in dc_data:
        logging.debug(dc_data)
        if re.match(r'(pod)', cluster_type, re.IGNORECASE):
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
        elif re.match(r'(hbase)', cluster_type, re.IGNORECASE):
            
            pri_grps,sec_grps,cluster_grps = parseHbaseData(dc,dc_data[dc])
            print(pri_grps,sec_grps,cluster_grps)
            pri_sub_chunks=[pri_grps[x:x+3] for x in xrange(0, len(pri_grps), 3)]
            print(pri_sub_chunks)
            for sub_lst in pri_sub_chunks:
                #for l in sub_lst:
                #    if re.search(r"HBASE\d",l):
                #        loc = sub_lst.index(l)
                #        w = l + " " + dc + "\n"
                #        output_pri.write(w)
                #        del sub_lst[loc]
                #        next   
                if sub_lst != []:
                    w = ','.join(sub_lst) + " " + dc + "\n"
                    output_pri.write(w)
            sec_sub_chunks=[sec_grps[x:x+3] for x in xrange(0, len(sec_grps), 3)]
            for sub_lst in sec_sub_chunks:
                w = ','.join(sub_lst) + " " + dc + "\n"
                output_sec.write(w)
            for c in cluster_grps:
                w = c + " " + dc + "\n"
                out_clusters.write(w)
            logging.debug("primary %s %s" % (dc,pri_grps))
            logging.debug("secondary %s %s" % (dc,sec_grps))
            logging.debug("clusters %s %s" % (dc,cluster_grps))
        else:
            print(cluster_type)
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
    output_pri.close()
    output_sec.close()