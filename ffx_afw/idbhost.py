#!/usr/bin/python
#
#
import json
import urllib2
import sys
import os
from os.path import expanduser
import socket

class Common:
    """Help on module common:

    NAME
        Common

    DESCRIPTION
        This is a common library used hold commonly used methods and properties.

    Instructions

    How to import -
        from common import Common
        common=Common()

    Access common properties
        outputdir=common.outputdir


    """
    def __init__(self):

        # Filesystem paths.
        self.home = expanduser("~")
        self.logdir = '../log'
        self.outputdir= self.home + '/git/cptops_case_gen/output'
        self.etcdir= self.home + '/git/cptops_case_gen/etc'
        self.bindir='.'
        self.includedir='../includes'
        self.tmpdir='../tmp'
        self.templatedir= self.home + '/git/cptops_case_gen/templates'
        self.cidb_jar_path = self.home + '/git/cptops_case_gen/lib/auth'
        
class Idbhost(Common):
    """Help on module Idbhost:

    NAME
        Idbhost

    DESCRIPTION
        The purpose of this module is to retrieve specific information related to
        Compute Deploy needs to feed into other programs (Template generation, nagios_monitor).

    Instructions

    How to import -
        from idbhost import Idbhost

    Make an alias of the initial call to the module. You can also set the search path
    (i.e IDB server) to make API calls.
        idb=Idbhost() or
    To m/ake API calls in chi IDB server.
        idb=Idbhost('chi')


    """


    def __init__(self, search='cidb'):
        self.search = search
        self.iDBurl = {'asg': "https://inventorydb1-0-asg.data.sfdc.net/api/1.03",
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
                       'cidb': "https://cidb1-0-sfm.data.sfdc.net/cidb-api/1.03"}

        if self.search == 'cidb':
            self.cidblocal = True
        else:
            self.cidblocal = False
        Common.__init__(self)


    def gethost(self, hosts):

        """ Composes the API url for a given host based on the datacenter location.

        Variables:

        hosts = A python list of servers.

        Objects:

        Idbhost.url -- Returns the url(s) of the servers for a host or
                       hostlist in a dictionary.
        """
        self.hjson = {}
        self.failedhost = []
        if isinstance(hosts, list):
            self.hosts = hosts
        else:
            self.hosts = hosts.split(',')
        self.url = {}
        for host in self.hosts:
            if self.cidblocal:
                derivedc = host.split('-')[3]
                derivever = self.iDBurl['cidb'].split('/')[4]
                derivemethod = self.iDBurl['cidb'].split('/')[0]
                derivehost = self.iDBurl['cidb'].split('/')[2]
                derivepath = self.iDBurl['cidb'].split('/')[3]
                url = derivemethod + '//' + derivehost + '/' + \
                derivepath + '/' + derivedc + '/' + derivever + \
                '/allhosts?name=' + \
                host + '&expand=cluster,cluster.superpod,superpod.datacenter'
                self.url[host] = os.popen('java -jar ' + self.cidb_jar_path + \
                    '/cidb-security-client-0.0.3.jar ' + self.cidb_jar_path + \
                    '/keyrepo "' + url + '"').read()
                host_info = urllib2.urlopen(self.url[host])
                host_data = json.load(host_info)
                if host_data['total'] == 0:
                    self.failedhost.append(host)
                else:
                    self.hjson[host] = host_data['data']
            else:
                try:
                    self.search in self.iDBurl.keys()
                    self.url[host] = self.iDBurl[self.search] + '/allhosts?name=' + host + \
                    '&expand=cluster,cluster.superpod,superpod.datacenter,deviceRole'
                    host_info = urllib2.urlopen(self.url[host])
                    host_data = json.load(host_info)
                    if host_data['total'] == 0:
                        self.failedhost.append(host)
                    else:
                        self.hjson[host] = host_data['data']
                except KeyError:
                    sys.exit(1)
        self.multi_host()

    def multi_host(self):
        """Handles multiple host to extract data for build_plan.py.

        Objects:

        Idbhost.mlist -- Host list dictionary of parsed json host data.

        """
        self.mlist = {}
        mlist2 = {}

        for hostname, data in self.hjson.iteritems():
            clustconfig = data[0]['cluster']['clusterConfigs']
            try:
                mlist2[hostname] = (item for item in clustconfig if item["key"] ==
                                    "monitor-host").next()
            except StopIteration:
                mlist2[hostname] = {'value': 'no host'}

            self.mlist[hostname] = {'clusterstatus': data[0]['failOverStatus'],
                                    'opsStatus_Host': data[0]['operationalStatus'],
                                    'opsStatus_Cluster': data[0]['cluster']['operationalStatus'],
                                    'Environment': data[0]['cluster']\
                                    ['environment'], 'superpod': data[0]\
                                    ['cluster']['superpod']['name'],
                                    'clustername': data[0]['cluster']\
                                    ['name'], 'deviceRole': data[0]\
                                    ['deviceRole'], 'monitor-host':\
                                    mlist2[hostname]['value']}

    def poddata(self, dc):
        """Retrieves all the Pod information from the specified datacenter.
           Data is seperated by primary and secondary.

        Variables:

        dc = A python list of datacenters

        Objects:

        Idbhost.pjson -- Full pod json data for a specified datacenter.

        """
        if isinstance(dc, list):
            self.dc = dc
        else:
            self.dc = dc.split(',')
        self.podurl = {}
        self.pjson = {}
        for dc in self.dc:
            if self.search != 'cidb':
                self.podurl[dc] = self.iDBurl[dc]\
                 + '/clusters?operationalStatus=active&clusterType=POD&superpod.dataCenter.name='\
                 + dc
                pod_info = urllib2.urlopen(self.podurl[dc])
                pod_data = json.load(pod_info)
                self.pjson[dc] = pod_data['data']
            else:
                url = 'https://cidb1-0-sfm.data.sfdc.net/cidb-api/' + dc\
                + '/1.03/clusters?operationalStatus=active&clusterType=POD&superpod.dataCenter.name='\
                + dc
                self.podurl[dc] = os.popen('java -jar  ' + self.cidb_jar_path +\
                     '/cidb-security-client-0.0.3.jar ' + self.cidb_jar_path + \
                      '/keyrepo "' + url + '"').read()
                pod_info = urllib2.urlopen(self.podurl[dc])
                pod_data = json.load(pod_info)
                self.pjson[dc] = pod_data['data']
        self.podinfo()

    def podinfo(self):
        """Extracts Primary and Secondary Pod information from specified data-center.

        Objects:

        Idbhost.dcs = Dictionary containing Pod information based on datacenter.

        """

        self.dcs = dict()
        for key, vals in self.pjson.iteritems():
            drgrp = dict()
            drgrp['Secondary'] = ','.join(sorted([val['name'] for val in vals if val['dr']]))
            drgrp['Primary'] = ','.join(sorted([val['name'] for val in vals if not val['dr']]))
            self.dcs[key] = drgrp

    def sp_data(self, dc, pd_status="active", pd_type="pod"):
        """
        Extracts a list of all the active superpods in a Datacenter.

        pd_status = Passes Pod operational statuses to retrieve to sp_info function. By default
        all active pods are reported.
        """
        #if isinstance(dc, list):
        self.dc = dc
        #else:
         #   self.dc = dc.split(',')
        self.sp_json = {}
        self.sp_url = {}
        self.sp_list = []
        self.pod_status = pd_status
        self.pod_type = pd_type

        #for dc in self.dc:
        if self.search != 'cidb':
            self.sp_url[self.dc] = self.iDBurl[self.dc] + '/superpods?fields=name&dataCenter.name='\
             + self.dc
            sp_info = urllib2.urlopen(self.sp_url[self.dc])
            sp_data = json.load(sp_info)
            self.sp_json[dc] = sp_data['data']
        else:
            url = 'https://cidb1-0-sfm.data.sfdc.net/cidb-api/' + self.dc\
             + '/1.03/superpods?fields=name&dataCenter.name=' + self.dc
            self.sp_url[self.dc] = os.popen('java -jar  ' + self.cidb_jar_path +\
                '/cidb-security-client-0.0.3.jar ' + self.cidb_jar_path + \
                '/keyrepo "' + url + '"').read()
            sp_info = urllib2.urlopen(self.sp_url[self.dc])
            sp_data = json.load(sp_info)
            self.sp_json[self.dc] = sp_data['data']
        #for keys, vals in self.sp_json.iteritems():
        for vals in self.sp_json.itervalues():
            for val in vals:
                self.sp_list.append(str(val['name']))
        self.sp_info(self.dc, self.sp_list, self.pod_status, self.pod_type)

    def sp_info(self, dc, pod_list, pd_status, pd_type):
        """
        Retrieves the Primary and Secondary pods from an given Superpod.

        DC = Datacenter
        pod_list = List of pods to retrieve data. By default when sp_data is run it search all pods
                   from that function.
        pd_status = Operational status of the pods to report. By default when using sp_data the
                    argument is retrieve from that function.
        """
        if isinstance(pod_list, list):
            pods = pod_list
        else:
            pods = pod_list.split(',')
        spcl_url = {}
        self.spcl_json = {}
        self.spcl_grp = {}
        for sp in pods:
            if self.search != 'cidb':
                spcl_url[sp] = self.iDBurl[self.dc]\
                 + '/clusters?fields=name,dr,clusterType,operationalStatus&operationalStatus='\
                 + pd_status + '&clusterType=' + pd_type + '&superpod.dataCenter.name=' + dc +\
                  '&superpod.name=' + sp
                spcl_info = urllib2.urlopen(spcl_url[sp])
                spcl_data = json.load(spcl_info)
                if spcl_data['total'] == 0:
                    pass
                else:
                    self.spcl_json[sp] = spcl_data['data']
            else:
                url = 'https://cidb1-0-sfm.data.sfdc.net/cidb-api/' + dc + \
                      '/1.03/clusters?fields=name,dr,clusterType,operationalStatus&operationalStatus='\
                       + pd_status + '&clusterType=' + pd_type + '&superpod.dataCenter.name=' \
                       + dc + '&superpod.name=' + sp
                spcl_url[sp] = os.popen('java -jar  ' + self.cidb_jar_path +\
                     '/cidb-security-client-0.0.3.jar ' + self.cidb_jar_path + \
                      '/keyrepo "' + url + '"').read()
                spcl_info = urllib2.urlopen(spcl_url[sp])
                spcl_data = json.load(spcl_info)
                if spcl_data['total'] == 0:
                    pass
                else:
                    self.spcl_json[sp] = spcl_data['data']
        for keys, vals in self.spcl_json.iteritems():
            spgrp = {}
            spgrp['Secondary'] = ','.join(sorted([val['name'] for val in vals if val['dr']]))
            spgrp['Primary'] = ','.join(sorted([val['name'] for val in vals if not val['dr']]))
            if not spgrp['Primary']:
                spgrp['Primary'] = "None"
            elif not spgrp['Secondary']:
                spgrp['Secondary'] = "None"
            self.spcl_grp[keys] = spgrp

    def clusterdata(self, dc, idbfilters={"operationalStatus": "active", "clusterType": "POD"}):
        """Retrieves all the Cluster specific information from the specified datacenter
        primary as well as secondary


        Variables:

        dc = A python list of datacenters

        Objects:

        Idbhost.dc -- Datacenter
        Idbhost.cldurl -- Url string for retrieving the Pod data from IDB
        Idbhost.cljson -- Full pod json data for a specified datacenter.

        """
        if isinstance(dc, list):
            self.dc = dc
        else:
            self.dc = dc.split(',')

        filterline = '&'.join(['='.join([key, idbfilters[key]]) for key in idbfilters])
        self.clurl = {}
        self.cljson = {}
        for dc in self.dc:
            if self.search != 'cidb':
                self.clurl[dc] = self.iDBurl[dc] + '/clusters?' + filterline\
                + '&superpod.dataCenter.name=' + dc
                cl_info = urllib2.urlopen(self.clurl[dc])
                cl_data = json.load(cl_info)
                self.cljson[dc] = cl_data['data']
            else:

                url = 'https://cidb1-0-sfm.data.sfdc.net/cidb-api/' + dc + \
                      '/1.03/clusters?' + filterline + \
                      '&superpod.dataCenter.name='  + dc
                self.clurl[dc] = os.popen('java -jar  ' + self.cidb_jar_path +\
                     '/cidb-security-client-0.0.3.jar ' + self.cidb_jar_path + \
                      '/keyrepo "' + url + '"').read()

                cl_info = urllib2.urlopen(self.clurl[dc])
                cl_data = json.load(cl_info)
                self.cljson[dc] = cl_data['data']
    def _getdc(self):
        hostname_split  = socket.gethostname().split('-')
        if len(hostname_split) == 4:
           dc = hostname_split[3]
        else:
           dc = None
           
    
    def checkprod(self,clust_list,dc=None):
        result={}
        clust_list =[clust.lower() for clust in clust_list]
        if dc==None and not self.cidblocal:
	    dc = self._getdc()
        if dc == None:
            raise Exception("No production DC supplied")
        self.poddata(dc)
        for record in self.pjson[dc]:
            if record['name'].lower() in clust_list:
                result[record['name']] = not record['dr']
        return result

    def clustinfo(self, dc, clust_list):
        """Reports all the nodes from a specified cluster.

        Variables:
        dc = String value for data-center.
        clustername = String value for Cluster name.

        Objects:

        Idbhost.clustername - Name of the cluster to search.
        Idbhost.clusturl - Url generated to search IDB for cluster information.
        Idbhost.cjson - Json data retrieved from the API.
        Idbhost.clusterhost - List of nodes in the specified cluster (Idbhost.clustername).

        """
        if isinstance(clust_list, list):
            self.clust_list = clust_list
        else:
            self.clust_list = clust_list.split(',')
        self.clusturl = {}
        self.cjson = {}
        self.clusterhost = {}
        if self.search != 'cidb':
            for clustername in self.clust_list:
                self.clusterhost[clustername] = []
                self.clusturl[clustername] = self.iDBurl[dc]\
                + '/allhosts?fields=name,failOverStatus,deviceRole&cluster.name=' + clustername
                cluster_info = urllib2.urlopen(self.clusturl[clustername])
                cluster_data = json.load(cluster_info)
                self.cjson[clustername] = cluster_data['data']
                host_info = [i['name'] for i in self.cjson[clustername] if 'name' in i]
                for i in host_info:
                    self.clusterhost[clustername].append(str(i))
        else:
            for clustername in self.clust_list:
                self.clusterhost[clustername] = []
                url = 'https://cidb1-0-sfm.data.sfdc.net/cidb-api/' + dc\
                + '/1.03/allhosts?fields=name,failOverStatus,deviceRole&cluster.name='  + clustername
                self.clusturl[clustername] = os.popen('java -jar  ' + self.cidb_jar_path\
                                                       + '/cidb-security-client-0.0.3.jar '\
                                                       + self.cidb_jar_path + '/keyrepo "' + url + '"').read()
                cluster_info = urllib2.urlopen(self.clusturl[clustername])
                cluster_data = json.load(cluster_info)
                self.cjson[clustername] = cluster_data['data']
                host_info = [i['name'] for i in self.cjson[clustername] if 'name' in i]
                for i in host_info:
                    self.clusterhost[clustername].append(str(i))
        #self.clust_summ()

    def clust_summ(self):
        """
        Creates node count summary of the specified cluster.
        """
        if self.cjson:
            self.cluster_summary = {}
            for clustername in self.clust_list:
                for val in self.cjson[clustername]:
                    if val['deviceRole'] in self.cluster_summary:
                        self.cluster_summary[clustername][val['deviceRole']] += 1
                    else:
                        self.cluster_summary[clustername][val['deviceRole']] = 1

    def deviceRoles(self, role):
        """
        Method works with clustinfo function.
        Provides a sorted list of servers based on role(s) for a specified cluster(s)
        """
        if isinstance(role, list):
            self.role = role
        else:
            self.role = role.split(',')
        roletypes = {}
        role_pri = {}
        role_sb = {}
        self.roles_all = {}
        self.roles_primary = {}
        self.roles_standby = {}
        for clustername in self.clust_list:
            for val in self.role:
                roletypes[val] = []
                role_pri[val] = []
                role_sb[val] = []
                for i in self.cjson[clustername]:
                    if i['deviceRole'] == val:
                        roletypes[val].append(str(i['name']))
                        roletypes[val].sort()
                        if i['failOverStatus'] == "PRIMARY":
                            role_pri[val].append(str(i['name']))
                            role_pri[val].sort()
                        elif i['failOverStatus'] == "STANDBY":
                            role_sb[val].append(str(i['name']))
                            role_sb[val].sort()
            self.roles_all[clustername] = roletypes
            self.roles_primary[clustername + "-Primary"] = role_pri
            self.roles_standby[clustername + "-Standby"] = role_sb
            roletypes = {}
            role_pri = {}
            role_sb = {}