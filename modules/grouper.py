#!/usr/bin/python
#
#
import re
import logging
import sys


class Organizer():
    def __init__(self):
        '''

        :param master:
        :param grouped_data:
        '''
        #self.master = master_data
        #self.grpdata = grouped_data
        #Function run order.
        #self.bundleorg()
        #self.prigroups()
        self.testvalue = "Hello"

    def bundleorg(self):
        '''
        Functions that takes master_json to extract bundle information and sort by bundle.
        :return:
        '''
        self.bundle_groups={}
        for k in self.master_data.iterkeys():
            bundle = self.master_data[k]['Bundle']
            if bundle in self.bundle_groups.keys():
                self.bundle_groups[bundle].append(k)
            else:
                self.bundle_groups[bundle]=[k]
        self.creategroups()
        self.cleangroups()

        return self.pri_groups

    def creategroups(self):
        '''
        Function that looks for the number of keys in bundle_groups and creates the necessary
        priority groups in pri_groups dictionary.
        :return:
        '''
        self.pri_groups={}
        self.pri_groups['Details'] = self.details
        self.pri_groups['Grouping'] = {}
        for i in range(0, len(self.bundle_groups.keys())):
            self.pri_groups['Grouping'][i] = {}
        if self.grouptype == "byrack":
            self.orgbyrack()

    def cleangroups(self):
        '''
        Function to remove dictionary keys with empty values.
        :return:
        '''
        for key in self.pri_groups['Grouping'].keys():
            if not any(self.pri_groups['Grouping'][key].values()):
                self.pri_groups['Grouping'].pop(key)

    def orgbyrack(self):
        '''
        Function to support the prioritizng of byrack grouping.
        :return:
        '''
        if len(self.pri_groups.keys()) > 2:
            for k,v in self.bundle_groups.iteritems():
                self.index = self.bundle_groups.keys().index(k)
                for self.host in v:
                    for a,b in self.byrack['Hostnames'].iteritems():
                        if self.host in b:
                            for r in range(0, len(self.pri_groups.keys())):
                                if a in self.pri_groups['Grouping'][r].keys():
                                    result = "True"
                                    break
                                else:
                                    result = "False"
                            if result == "False":
                                self.pri_groups['Grouping'][self.index].update({a: b})
        else:
            for a,b in self.byrack['Hostnames'].iteritems():
                self.pri_groups['Grouping'][0].update({a: b})

class Groups(Organizer):
    def __init__(self, cl_status, ho_status, pod, role, dc, cluster, gsize, grouptype, template, dowork):
        Organizer.__init__(self)
        self.bymajor = {}
        self.byminor = {}
        self.byrack = {}
        #self.hostnum = re.compile(r'\w*-\w*(\d)-(\d*)-\w*')
        self.hostnum = re.compile(r'(\d.*)')
        self.grouptype = grouptype
        self.details = {"cl_status": cl_status,
                        "ho_status": ho_status,
                        "role": role,
                        "Superpod": pod,
                        "dc": dc,
                        "cluster": cluster,
                        "gsize": gsize,
                        "grouping": self.grouptype,
                        "tempalteid": template,
                        "dowork": dowork
                        }

    def rackorder(self, data):
        self.byrack['Details'] = self.details
        self.byrack['Hostnames'] = {}
        self.master_data = data
        for host in self.master_data.iterkeys():
            try:
                racknum = self.master_data[host]['RackNumber']
            except KeyError as valerr:
                print valerr
                raise
            if racknum in self.byrack['Hostnames'].keys():
                self.byrack['Hostnames'][racknum].append(host)
            else:
                self.byrack['Hostnames'][racknum] = [host]

        return self.bundleorg()

    def majorset(self, data):
        self.bymajor['Details'] = self.details
        self.bymajor['Hostnames'] = {}
        self.master_data = data
        for host in self.master_data.iterkeys():
            try:
                majorset = self.master_data[host]['Majorset']
            except KeyError as valerr:
                print valerr
                raise
            #regout = self.hostnum.search(host.split("-")[1])
            #regout = self.hostnum.search(host)
            #majorset = int(regout.group())
            if majorset in self.bymajor['Hostnames'].keys():
                self.bymajor['Hostnames'][majorset].append(host)
            else:
                self.bymajor['Hostnames'][majorset] = [host]

        return self.bymajor

    def minorset(self, data):
        self.byminor['Details'] = self.details
        self.byminor['Hostnames'] = {}
        self.master_data = data
        for host in self.master_data.iterkeys():
            try:
                minorset = self.master_data[host]['Minorset']
            except KeyError as valerr:
                print valerr
                raise
            #regout = self.hostnum.search(host.split("-")[2])
            #minorset = regout.groups()
            if minorset in self.byminor['Hostnames'].keys():
                self.byminor['Hostnames'][minorset].append(host)
            else:
                self.byminor['Hostnames'][minorset] = [host]

        return self.byminor
