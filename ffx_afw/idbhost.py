#!/usr/bin/python
#
#
import json
import urllib2
import sys
import os
from os.path import expanduser
import socket
import itertools
import logging
import re
from collections import defaultdict
from threading import Thread
from multiprocessing import Process, Queue, Manager
from subprocess import PIPE, Popen

class Idbhost():
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
        if self.search == 'cidb':
            self.cidblocal = True
        else:
            self.cidblocal = False

    def validatedc(self, dc):
        valid_dcs = ['was', 'chi', 'dfw', 'par', 'asg', 'sjl', 'lon', 'frf', 'tyo',
                     'chx', 'wax', 'sfm', 'phx', 'ukb', 'crd', 'crz', 'prd', 'sfz']
        if dc not in valid_dcs:
            raise Exception("%s is not a valid DC." % dc)

    def _get_uri_list(self, idb_resource, fields, idbfilters):
        """
        construct list of reststrings  using dict idbfilters
        """

        requestlist = []
        results=[]
        assert len(fields) > 0, "Error: No fields specified"
        assert len(idbfilters.keys()) > 0, "Error no filters specified"

        #convert each to list if string assigned
        for key,val in idbfilters.items():
            idbfilters[key] = [val] if not isinstance(val,list) else val


        for key in idbfilters:
            assert (isinstance(idbfilters[key], list) and len(idbfilters[key][0]) > 0), "idbfilter " + key + " must have at least one value"
            requestlist.append([(key,val) for val in idbfilters[key] ])


        requestlist.append([('fields', ','.join(fields))] )

        for clauses in itertools.product(*requestlist):
            reststring = idb_resource + '&'.join(['='.join(clause) for clause in clauses ])
            results.append(reststring)

        return results

    def idbquery(self,datacenters,idb_resource,fields,idbfilters,usehostlist=False):
        """
           datacenters: tuple of 3 character datacenter ids eg : was,chi,tyo ..
           idbfilters : dict of key = valid target fieldname, value = tuple of values
           returns : results by reststring
        """
        assert len(datacenters) > 0, "Error no datacenters specified"

        results = {}

        reststring_list = self._get_uri_list(idb_resource,fields,idbfilters)
        for dc in datacenters:
            for reststring in reststring_list:
                if not usehostlist:
                    current, url = ReqBuilder().gen_request(reststring, dc, self.cidblocal)
                    #current, url=self._gen_request(reststring,dc)
                else:
        #not pretty but this is so we are not querying dcs we don't need
                    if reststring.split('=')[1].split('&')[0].split('-')[3]==dc:
                        current, url = ReqBuilder().gen_request(reststring, dc, self.cidblocal)
                        #current, url =self._gen_request(reststring,dc)
                    else:
                        continue
                results[url] = current['total'], current['data'], dc
        return results

    def failurecheck(self, data_json):
        """
        Test values for failures
        """
        self.failures = []

        for key_name, key_value in data_json.iteritems():
            if not key_value:
                self.failures.append(key_name)

        for val_name in self.failures:
            data_json.pop(val_name)

        return data_json

    def gethost(self, hosts):

        """ Composes the API url for a given host based on the datacenter location.

        Variables:

        hosts = A python list of servers.

        Objects:

        Idbhost.url -- Returns the url(s) of the servers for a host or
                       hostlist in a dictionary.
        """
        manager = Manager()
        self.hjson_all = manager.dict()
        self.hjson_configs = manager.dict()

        args_list = []
        def thread_func(host, hjson_all, hjson_configs):
            """
            Threading function for idb.gethost.
            """
            dc = host.split('-')[3]
            self.validatedc(dc)
            url_all = 'allhosts?expand=cluster,cluster.superpod,superpod.datacenter&name=' + host
            url_config = 'allhostconfigs?fields=key,value&host.name=' + host
            host_data = ReqBuilder().gen_request(url_all, dc, self.cidblocal)
            host_config = ReqBuilder().gen_request(url_config, dc, self.cidblocal)
            hjson_all[host] = host_data[0]['data']
            hjson_configs[host] = host_config[0]['data']

        if isinstance(hosts, list):
            self.hosts = hosts
        else:
            self.hosts = hosts.split(',')
        self.url = {}
        p_list = []
        for host in self.hosts:
            p = Process(target=thread_func, args=(host, self.hjson_all, self.hjson_configs))
            p.start()
            p_list.append(p)
        [process.join() for process in p_list]

        if self.hjson_all:
            self.multi_host()

    def multi_host(self):
        """Handles multiple host to extract data for build_plan.py.

        Objects:

        Idbhost.mlist -- Host list dictionary of parsed json host data.

        """
        self.mlist = {}
        mlist2 = {}
        key_list = ['minorSet', 'majorSet', 'solr_cluster']

        for hostname, data in self.hjson_all.items():
            if len(data) > 0:
                clustconfig = data[0]['cluster']['clusterConfigs']
                try:
                    if re.search(r'mnds|dnds', hostname):
                        mlist2[hostname] = (item for item in clustconfig if item["key"] ==
                                        "hbase-nagios-host").next()
                    else:
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
                for conf_data in self.hjson_configs[hostname]:
                    if conf_data['key'] in key_list:
                        self.mlist[hostname][conf_data['key']] = conf_data['value']                     
            else:
                print("ERROR :- iDB data is missing for host {0}".format(hostname))


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
        self.pjson = {}
        for dc in self.dc:
            pod_restring = 'clusters?operationalStatus=active&clusterType=POD&superpod.dataCenter.name='\
            + dc
            self.pod_data = ReqBuilder().gen_request(pod_restring, dc, self.cidblocal)
            self.pjson[dc] = self.pod_data[0]['data']
        if self.pjson:
            self.podinfo()

    def podinfo(self):
        """Extracts Primary and Secondary Pod information from specified data-center.

        Objects:

        Idbhost.dcs = Dictionary containing Pod information based on datacenter.

        """

        self.dcs = dict()
        for key, vals in self.pjson.items():
            drgrp = dict()
            drgrp['Secondary'] = ','.join(sorted([val['name'] for val in vals if val['dr']]))
            drgrp['Primary'] = ','.join(sorted([val['name'] for val in vals if not val['dr']]))
            self.dcs[key] = drgrp

    def sp_data(self, dc, pd_status="active", pd_type="pod"):
        """
        Extracts a list of all the active superpods in a Datacenter.

        :param dc: Single datacenter OR a list of datacenters
        :param pd_status: Cluster/POD status, default is active
        :param pd_type: PodType, Cluster/POD
        :return: Nothing, but call another function at the end
        """

        manager = Manager()
        sp_json = manager.dict()
        sp_dict = defaultdict(list)
        self.sp_url = {}
        pod_status = pd_status
        pod_type = pd_type
        dc_list = []

        if isinstance(dc, list):
            dcs = dc
        else:
            dcs = dc.split(',')

        for dc in dcs:
            dc_list.append(dc)

        def thread_sp_data(dc, sp_json):
            sp_restring = 'superpods?fields=name&dataCenter.name=' + dc
            spod_data = ReqBuilder().gen_request(sp_restring, dc, self.cidblocal)
            sp_json[dc] = spod_data[0]['data']
        p_list = []
        for dc in dc_list:
            p = Process(target=thread_sp_data, args=(dc, sp_json))
            p.start()
            p_list.append(p)

        [process.join() for process in p_list]

        for key, vals in sp_json.items():
            for val in vals:
                sp_dict[key].append(str(val['name']))
        self.sp_info(dc_list, sp_dict, pod_status, pod_type)

    def sp_info(self, dc, spod_list, pd_status, pd_type):
        """
        Retrieves the Primary and Secondary pods from an given Superpod.

        :param dc: A datacenter OR a list of datacenters
        :param spod_list: List of super_pods in a DataCenter
        :param pd_status: By Default is active
        :param pd_type: PodType, Cluster/POD
        :return:
        """

        q = Queue()
        spods = []
        for spod in spod_list.values():
            spods.extend(spod)

        if isinstance(spods, list):
            spods = spods
        else:
            spods = spods.split(',')

        dcs = [dc[0] for dc in dc]

        def thread_sp_info(sp, dc, q):
            spinfo_restring = 'clusters?fields=name,dr,clusterType,operationalStatus&operationalStatus=' \
                              + pd_status + '&clusterType=' + pd_type + '&superpod.dataCenter.name=' + dc + \
                              '&superpod.name=' + sp
            data = ReqBuilder().gen_request(spinfo_restring, dc, self.cidblocal)
            if data[0]['total'] == 0:
                logging.debug('No records found for %s', sp)
            else:
                q.put((dc, sp, data[0]['data']))

        p_list = []
        for dc, sp in spod_list.items():
            for spod in sp:
                p = Process(target=thread_sp_info, args=(spod, dc, q))
                p.start()
                p_list.append(p)

        [process.join() for process in p_list]

        spcl_dict = {}  # Temporary dict to parse data returned from Q.
        while not q.empty():
            dc, sp, data = q.get()
            if dc not in spcl_dict.keys():
                spcl_dict[dc] = {}
            if sp not in spcl_dict[dc].keys():
                spcl_dict[dc][sp] = []
            spcl_dict[dc][sp].append(data)

        spgrp = {}  # Final dataStructure to return
        for dc in spcl_dict.keys():
            spgrp[dc] = {}
            for sp, data in spcl_dict[dc].items():
                if not spgrp[dc].has_key(sp):
                    spgrp[dc][sp] = []
                dict_len = len(data[0])
                for index in range(0, dict_len):
                    index = int(index)
                    if not data[0][index]['dr']:
                        spgrp[dc][sp].append({'Primary': data[0][index]['name']})
                    else:
                        spgrp[dc][sp].append({'Secondary': data[0][index]['name']})
        self.spcl_grp = spgrp


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
        for dc_name in self.dc:
            clust_restring = '/clusters?' + filterline\
            + '&superpod.dataCenter.name=' + dc
            clust_data = ReqBuilder().gen_request(clust_restring, dc_name, self.cidblocal)
            self.cljson[dc] = clust_data['data']

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
        self.cjson = {}
        self.clusterhost = {}
        for clustername in self.clust_list:
            self.clusterhost[clustername] = []
            clustinf_restring = 'allhosts?fields=name,failOverStatus,deviceRole&cluster.name='\
            + clustername
            clustinfo_data = ReqBuilder().gen_request(clustinf_restring, dc, self.cidblocal)
            self.cjson[clustername] = clustinfo_data[0]['data']
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

class ReqBuilder():
    """
    Class that builds the API request string for IDB.
    """
    def __init__(self):
        """
        Locate jar file locations and path.
        """
        self.jar_dirs = ['./idbhost/lib/auth', os.path.expanduser('~/git/cptops_idbhost/lib/auth') ]
        self.jar_file = "cidb-security-client-0.0.7.jar"
    def lookup_jar(self, cidblocal):
        """
        Locate jar file location for siging CIDB api request. 
        """
        jar_path = ""
        if cidblocal:
            for jar_dir in self.jar_dirs:
                if os.path.isdir(jar_dir):
                    jar_path = jar_dir
                    return jar_path
                    break
            if not jar_path:
                raise Exception('Cannot locate CIDB jar file.')
            
    def gen_request(self, restring, dc, cidblocal):
        """
        Builds URL string for IDB api call.
        """
        self.restring = restring
        self.dc = dc.lower()
        self.cidblocal = cidblocal
        self.cidb_jar_path = ReqBuilder().lookup_jar(cidblocal)
        if self.cidblocal:
            url = "https://cidb1-0-sfm.data.sfdc.net/cidb-api/%s/1.03/" % self.dc + self.restring
            url_cmd = 'java -jar %s/%s %s/keyrepo "%s"' % (self.cidb_jar_path, self.jar_file, self.cidb_jar_path, url)
            url = Popen(url_cmd, shell=True, stdout=PIPE).stdout
            url = url.read()
        else:
            url = "https://inventorydb1-0-%s.data.sfdc.net/api/1.03/" % dc + restring
        logging.debug(url)
        try:
            import requests
            if self.cidblocal:
                 info = requests.get(url.rstrip('\n'), verify=os.path.expanduser('~') + '/git/cptops_idbhost/lib/auth/salesforce.com_Internal_Root_CA_1.pem')
            else:
                info = requests.get(url.rstrip('\n'))
            data = info.json()
            if 'total' in data.keys():
                if data['total'] == 1000:
                    raise Exception('IDB record limit of 1000, you may be missing records')
            return data, url
        except ImportError:
            import urllib2
            if self.cidblocal:
                raw_data = urllib2.urlopen(url, cafile=os.path.expanduser('~') + '/git/cptops_idbhost/lib/auth/salesforce.com_Internal_Root_CA_1.pem')
            else:
                raw_data = urllib2.urlopen(url)
            data = json.load(raw_data)
            if data['total'] == 1000:
                raise Exception('IDB record limit of 1000, you may be missing records')
            logging.debug(' %s records returned' % str(data['total']))
            return data, url
