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

if __name__ == '__main__':
    usage = """
    Code to check host details from idb

    %prog -H hostname [-v]    
    %prog -H ops-monitor1-1-was

    """
    parser = OptionParser(usage)
    parser.add_option("-d", "--dc", dest="dc",
                            help="The dc(s) to get data for ")
    parser.add_option("-H", "--hosts", dest="hosts",
                            help="The case number(s) of the case to attach the file ")
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
    data = idb.sp_data(options.dc)
    pdata = idb.poddata(options.dc)
    print(idb.sp_list)
    print(idb.dcs)
