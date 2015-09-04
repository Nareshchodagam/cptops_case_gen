from optparse import OptionParser
import logging
import re

dc_details = { 'asg_none' : 'na0 na3 cs2 cs4 cs13',
    'tyo_none': 'ap0 ap1 ap2 cs5 cs5',
    'sjl_none': 'na1 na5 na6 cs1 cs3 cs12 cs30',
    'chi_sp1': 'na8 na8 na10 eu1 gs0 cs7 cs8 cs14',
    'chi_sp2': 'na2 na13 na15 cs15 cs16',
    'chi_sp3': 'na19 na20 cs23 cs24 cs25',
    'was_sp1': 'na7 na11 na12 na14 cs9 cs10 cs11',
    'was_sp2': 'na4 na16 eu0 eu2 eu3 cs17 cs18 cs19 cs20',
    'was_sp3': 'na17 na18 na22 na23 na41 cs21 cs22 cs26',
    'lon_sp9': 'eu5 cs80 cs81' }

def gen_plan_sitesproxy(case,sp,inst,dc,host,filename):

    logging.debug(filename)
    f = open(filename, 'w')

    f.write("""
All actions take place on the release host using packaged release runner. Call KZ via

katzmeow.pl --case %s --impl


%s

- set your DC env
Exec: DC=%s
""" % (case,inst.upper(),dc))


    f.write("""
- create a local remote_transfer directory

mkdir -p ~/releaserunner/remote_transfer

- the get the update script:
cd ~/releaserunner/remote_transfer
 svn export svn://vc-%s/subversion/tools/dcc/update_glibc.sh

RR based commands
- copy it up to the target host
""" % dc)

    f.write("""release_runner.pl -forced_host %s-%s-%s -force_update_bootstrap -c sudo_cmd -m "ls" -threads -auto2\n""" % (inst,host,dc))

    f.write("""
-Validate hosts are in pool and no issues with the pool
release_runner.pl -invdb_mode -superpod %s -cluster %s -product sitesproxy -c bigipcheck -thread -auto2\n""" % (sp,inst))

    f.write("""
-disable monitor
release_runner.pl -c disable_host_monitor -forced_host %s-%s-%s -forced_monitor_host %s-monitor-%s.ops.sfdc.net -threads -auto2\n""" % (inst,host,dc,inst,dc))

    f.write("""
- remove from pool
release_runner.pl -invdb_mode -superpod %s -cluster %s -product sitesproxy -device_role proxy -host %s-%s -c remove_from_pool -auto2\n""" % (sp,inst,inst,host))

    f.write("""
-stop app
release_runner.pl -invdb_mode -superpod %s -cluster %s -product sitesproxy -device_role proxy -host %s-%s -c stop_server -auto2\n""" % (sp,inst,inst,host))

    f.write("""
- stop splunk
release_runner.pl -invdb_mode -superpod %s -cluster %s -product sfdc-splunk-forwarder -device_role proxy -host %s-%s -c stop_server -auto2\n""" % (sp,inst,inst,host))

    f.write("""
- Execute the  update script:
release_runner.pl -forced_host %s-%s-%s -c sudo_cmd -m "./remote_transfer/update_glibc.sh" -threads -auto2\n""" % (inst,host,dc))

    f.write("""
- Reboot the host
release_runner.pl -forced_host %s-%s-%s -c sudo_cmd -m "reboot" -threads -auto2\n""" % (inst,host,dc))

    f.write("""
- Verify glibc versions
release_runner.pl -forced_host %s-%s-%s -c cmd -m "rpm -qa | grep glibc; rpm -qa | grep nscd" -threads -auto2\n""" % (inst,host,dc))

    f.write("""
-start app
release_runner.pl -invdb_mode -superpod %s -cluster %s -product sitesproxy -device_role proxy -host %s-%s -c start_server -auto2\n""" % (sp,inst,inst,host))

    f.write("""
- validate the max file descriptors as squid startup can be problematic target is 65k if it fails do a stop and start to restart it.
release_runner.pl -forced_host %s-%s-%s -c sudo_cmd -m "/usr/bin/squidclient -p 8084 mgr:info | grep 'file descrip'|grep -i max" -auto2\n""" % (inst,host,dc))

    f.write("""
release_runner.pl -forced_host %s-%s-%s -c sudo_cmd -m "/usr/bin/squidclient -p 8085 mgr:info | grep 'file descrip'|grep -i max" -auto2\n""" % (inst,host,dc))
    f.write("""
- start splunk
release_runner.pl -invdb_mode -superpod %s -cluster %s -product sfdc-splunk-forwarder -device_role proxy -host %s-%s -c start_server -auto2\n""" % (sp,inst,inst,host))
    f.write("""
- add to pool
release_runner.pl -invdb_mode -superpod %s -cluster %s -product sitesproxy -device_role proxy -host %s-%s -c add_to_pool -auto2\n""" % (sp,inst,inst,host))
    f.write("""
- enable monitoring
release_runner.pl -c enable_host_monitor -forced_host %s-%s-%s -forced_monitor_host %s-monitor-%s.ops.sfdc.net -threads -auto2\n""" % (inst,host,dc,inst,dc))
    f.write("""
-Validate hosts are in pool and no issues with the pool
release_runner.pl -invdb_mode -superpod %s -cluster %s -product sitesproxy -c bigipcheck -thread -auto2\n""" % (sp,inst))
    f.write("""
- test endpoint connectivity.
release_runner.pl -forced_host %s-%s-%s -c sudo_cmd -m 'wget --header "X-Salesforce-Forwarded-To: %s.salesforce.com" --header "X-Salesforce-SIP: 10.13.37.1" --header "Host: www.test.com" -O - http://`hostname -f`:8084/smth.jsp' -auto2\n""" % (inst,host,dc,inst))
    f.write("""
release_runner.pl -forced_host %s-%s-%s -c sudo_cmd -m 'wget --header "X-Salesforce-Forwarded-To: %s.salesforce.com" --header "X-Salesforce-SIP: 10.13.37.1" --header "Host: www.test.com" -O - http://`hostname -f`:8085/smth.jsp' -auto2\n""" % (inst,host,dc,inst))
    f.close()

def gen_plan_publicproxy(case,sp,inst,dc,host,filename):

    logging.debug(filename)
    f = open(filename, 'w')

    f.write("""
All actions take place on the release host using packaged release runner. Call KZ via

katzmeow.pl --case %s --impl


%s

- set your DC env
Exec: DC=%s
""" % (case,inst.upper(),dc))
    f.write("""release_runner.pl -forced_host %s-%s-%s -force_update_bootstrap -c sudo_cmd -m "ls" -threads -auto2\n""" % (inst,host,dc))
    f.write("""
-Validate hosts are in pool and no issues with the pool
release_runner.pl -invdb_mode -superpod %s -cluster %s -product publicproxy -c bigipcheck -thread -auto2\n""" % (sp,inst))

    f.write("""
-disable monitor
release_runner.pl -c disable_host_monitor -forced_host %s-%s-%s -forced_monitor_host %s-monitor-%s.ops.sfdc.net -threads -auto2\n""" % (inst,host,dc,inst,dc))

    f.write("""
- remove from pool
release_runner.pl -invdb_mode -superpod %s -cluster %s -product publicproxy -device_role proxy -host %s-%s -c remove_from_pool -auto2\n""" % (sp,inst,inst,host))

    f.write("""
-stop app
release_runner.pl -invdb_mode -superpod %s -cluster %s -product publicproxy -device_role proxy -host %s-%s -c stop_server -auto2\n""" % (sp,inst,inst,host))

    f.write("""
- stop splunk
release_runner.pl -invdb_mode -superpod %s -cluster %s -product sfdc-splunk-forwarder -device_role proxy -host %s-%s -c stop_server -auto2\n""" % (sp,inst,inst,host))

    f.write("""
- Execute the  update script:
release_runner.pl -forced_host %s-%s-%s -c sudo_cmd -m "./remote_transfer/update_glibc.sh" -threads -auto2\n""" % (inst,host,dc))

    f.write("""
- Reboot the host
release_runner.pl -forced_host %s-%s-%s -c sudo_cmd -m "reboot" -threads -auto2\n""" % (inst,host,dc))

    f.write("""
- Verify glibc versions
release_runner.pl -forced_host %s-%s-%s -c cmd -m "rpm -qa | grep glibc; rpm -qa | grep nscd" -threads -auto2\n""" % (inst,host,dc))

    f.write("""
-start app
release_runner.pl -invdb_mode -superpod %s -cluster %s -product publicproxy -device_role proxy -host %s-%s -c start_server -auto2\n""" % (sp,inst,inst,host))

    f.write("""
- validate the max file descriptors as squid startup can be problematic target is 65k if it fails do a stop and start to restart it.
release_runner.pl -forced_host %s-%s-%s -c sudo_cmd -m "/usr/bin/squidclient -p 8080 mgr:info | grep 'file descrip'|grep -i max" -auto2\n""" % (inst,host,dc))

    f.write("""
- start splunk
release_runner.pl -invdb_mode -superpod %s -cluster %s -product sfdc-splunk-forwarder -device_role proxy -host %s-%s -c start_server -auto2\n""" % (sp,inst,inst,host))
    f.write("""
- add to pool
release_runner.pl -invdb_mode -superpod %s -cluster %s -product publicproxy -device_role proxy -host %s-%s -c add_to_pool -auto2\n""" % (sp,inst,inst,host))
    f.write("""
- enable monitoring
release_runner.pl -c enable_host_monitor -forced_host %s-%s-%s -forced_monitor_host %s-monitor-%s.ops.sfdc.net -threads -auto2\n""" % (inst,host,dc,inst,dc))
    f.write("""
-Validate hosts are in pool and no issues with the pool
release_runner.pl -invdb_mode -superpod %s -cluster %s -product publicproxy -c bigipcheck -thread -auto2\n""" % (sp,inst))

#    wget -e use_proxy=yes -e http_proxy=`hostname -f`:8080 -O - http://public-obmm1-1-chi.ops.sfdc.net:8088

    dc_sp = dc + "_" + sp
    f.write("""
    for i in ssl %s; do wget -e use_proxy=yes -e http_proxy=%s-%s-%s:8080 -O - http://$i.salesforce.com/smth.jsp; done
    """ % (dc_details[dc_sp],inst,host,dc))
    f.close()

if __name__ == "__main__":
    usage = """
    proxy patching case implementation plan generation

    This code will generate the implementation plan for patching sites proxy hosts.
    The arguments required to be passed are case, superpod, instance, data center and host.

    %prog -c caseNum -s superpod -i instance -d datacenter -H host
    %prog -c 00081002 -s none -i cs3 -d sjl -H proxy1-1
    %prog -c 00081002 -s sp1 -i na7 -d was -H proxy1-1

    How to call the
    """
    parser = OptionParser(usage)
    parser.add_option("-c", "--case", dest="caseNum",
                help="The case number to use")
    parser.add_option("-s", "--superpod", dest="superpod", help="The superpod")
    parser.add_option("-i", "--instance", dest="instance", help="The instance")
    parser.add_option("-d", "--datacenter", dest="datacenter", help="The datacenter")
    parser.add_option("-H", "--host", dest="host", help="The host")
    parser.add_option("-f", "--filename", dest="filename", default="implementation_plan.txt", help="The output filename")
    parser.add_option("-v", action="store_true", dest="verbose", help="verbosity")
    (options, args) = parser.parse_args()
    if options.verbose:
        logging.basicConfig(level=logging.DEBUG)
    if options.caseNum and options.superpod and options.instance and options.datacenter and options.host:
        if re.search(r'publicproxy', options.instance):
            gen_plan_publicproxy(options.caseNum,options.superpod,options.instance,options.datacenter,options.host,options.filename)
        else:
            gen_plan_sitesproxy(options.caseNum,options.superpod,options.instance,options.datacenter,options.host,options.filename)
    else:
        gen_plan_sitesproxy('00081002','none','cs3','sjl','proxy1-1')
